"""Reindex data/raw/* into ChromaDB + SQLite for a given course, from a clean slate.

Calls the same production functions as `POST /documents/upload` + `POST /documents/{id}/index`
(load_document -> clean_pages -> create_chunks -> add_chunks_to_vector_store) directly, instead
of going through the HTTP API. See the plan file for why: no server needed, no endpoint exists
to wipe Chroma anyway, and the upload endpoint would rename files with a uuid prefix that breaks
the (document_name, page, chunk_index) gold-label keying used by evaluate_retrieval.py.

Usage:
    python scripts/ingest_corpus.py --course-id 1 --user-id 1 --reset --yes
"""

import argparse
import csv
import os
import sys
import unicodedata
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
os.chdir(PROJECT_ROOT)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from backend.database import SessionLocal  # noqa: E402
from backend.models.document import Document  # noqa: E402
from backend.services import vector_store  # noqa: E402
from backend.services.chunking import create_chunks  # noqa: E402
from backend.services.document_loader import load_document  # noqa: E402
from backend.services.text_cleaner import clean_pages  # noqa: E402
from backend.services.vector_store import add_chunks_to_vector_store  # noqa: E402

RAW_DIR = Path("data/raw")
PROCESSED_DIR = Path("data/processed")
EVAL_DIR = Path("data/eval")
SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt"}


def _write_processed_text(processed_path: Path, cleaned_pages: list[dict]) -> None:
    with processed_path.open("w", encoding="utf-8") as file:
        for page in cleaned_pages:
            file.write(f"\n\n--- Page {page['page']} ---\n")
            file.write(str(page["text"]))


def diacritic_health(text: str) -> tuple[float, float]:
    n = len(text) or 1
    repl = (text.count("�") + text.count("?")) / n
    diac = sum(
        1 for ch in unicodedata.normalize("NFD", text) if unicodedata.category(ch) == "Mn"
    ) / n
    return diac, repl


def guard_cwd() -> None:
    if not (Path("backend").is_dir() and Path("app.db").exists()):
        print(
            "ERROR: must be run from the project root (backend/ and app.db not found here).",
            file=sys.stderr,
        )
        sys.exit(2)


def reset_chroma(course_id: int, scope: str) -> int:
    if scope == "all":
        ids = vector_store.collection.get(include=[])["ids"]
    else:
        ids = vector_store.collection.get(
            where={"course_id": str(course_id)}, include=[]
        )["ids"]
    if ids:
        vector_store.collection.delete(ids=ids)
    return len(ids)


def reset_sqlite(db, course_id: int) -> int:
    count = db.query(Document).filter(Document.course_id == course_id).count()
    db.query(Document).filter(Document.course_id == course_id).delete()
    db.commit()
    return count


def discover_files(skip_globs: list[str]) -> list[Path]:
    files = sorted(p for p in RAW_DIR.iterdir() if p.suffix.lower() in SUPPORTED_EXTENSIONS)
    for pattern in skip_globs:
        skipped = set(RAW_DIR.glob(pattern))
        files = [f for f in files if f not in skipped]
    return files


def main() -> None:
    guard_cwd()

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--course-id", type=int, required=True)
    parser.add_argument("--user-id", type=int, required=True)
    parser.add_argument("--reset", action="store_true", help="wipe existing Chroma + SQLite rows first")
    parser.add_argument("--reset-scope", choices=["all", "course"], default="all")
    parser.add_argument("--skip", action="append", default=[], help="glob pattern(s) under data/raw to skip")
    parser.add_argument("--yes", action="store_true", help="proceed without interactive confirmation")
    parser.add_argument("--percentile", type=float, default=None,
                         help="override semantic chunking breakpoint percentile (default: chunking.py's constant)")
    parser.add_argument("--overlap-sentences", type=int, default=None,
                         help="override semantic chunking sentence overlap (default: chunking.py's constant)")
    parser.add_argument("--fixed-size", action="store_true",
                         help="use plain fixed-size chunking instead of semantic chunking")
    args = parser.parse_args()

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    EVAL_DIR.mkdir(parents=True, exist_ok=True)

    db = SessionLocal()

    if args.reset:
        removed_vectors = reset_chroma(args.course_id, args.reset_scope)
        removed_docs = reset_sqlite(db, args.course_id)
        print(f"[reset] removed {removed_vectors} Chroma vector(s) (scope={args.reset_scope}), "
              f"{removed_docs} Document row(s) for course_id={args.course_id}")

    files = discover_files(args.skip)
    if not files:
        print(f"No supported files ({sorted(SUPPORTED_EXTENSIONS)}) found in {RAW_DIR}.")
        sys.exit(1)

    if args.percentile is not None:
        print(f"Semantic chunking breakpoint percentile override: {args.percentile}")
    if args.overlap_sentences is not None:
        print(f"Semantic chunking overlap_sentences override: {args.overlap_sentences}")
    print(f"Manifest ({len(files)} file(s), course_id={args.course_id}):")
    for f in files:
        print(f"  - {f.name} ({f.stat().st_size} bytes)")

    if not args.yes:
        answer = input("Proceed with ingestion? [y/N] ").strip().lower()
        if answer != "y":
            print("Aborted.")
            sys.exit(0)

    all_chunk_rows: list[dict] = []
    total_pages = 0
    total_chars = 0

    for path in files:
        document = Document(
            course_id=args.course_id,
            user_id=args.user_id,
            file_name=path.name,
            file_path=str(path),
            file_type=path.suffix.lstrip(".").lower(),
            status="uploaded",
        )
        db.add(document)
        db.commit()
        db.refresh(document)

        try:
            pages = load_document(str(path))
            cleaned_pages = clean_pages(pages)
        except Exception as exc:
            document.status = "failed"
            db.commit()
            print(f"[FAIL] {path.name}: could not load/clean -- {exc}")
            continue

        doc_chars = sum(len(str(p["text"])) for p in cleaned_pages)
        total_pages += len(cleaned_pages)
        total_chars += doc_chars

        for page in cleaned_pages:
            text = str(page["text"])
            if len(text) < 50:
                print(f"[WARN] {path.name} page {page['page']}: only {len(text)} chars "
                      f"-- likely a scanned/image page with no extractable text.")
            diac, repl = diacritic_health(text)
            if repl > 0.01 or (len(text) > 200 and diac < 0.01):
                print(f"[WARN] {path.name} page {page['page']}: encoding looks corrupted "
                      f"(replacement_ratio={repl:.3f}, diacritic_ratio={diac:.3f}).")

        processed_path = PROCESSED_DIR / f"{document.id}_{path.stem}.txt"
        _write_processed_text(processed_path, cleaned_pages)

        chunk_kwargs = {}
        if args.percentile is not None:
            chunk_kwargs["percentile"] = args.percentile
        if args.overlap_sentences is not None:
            chunk_kwargs["overlap_sentences"] = args.overlap_sentences
        if args.fixed_size:
            chunk_kwargs["use_semantic"] = False
        def _print_progress(page_num: int, total: int, _name=path.name) -> None:
            if page_num == 1 or page_num == total or page_num % 10 == 0:
                print(f"  [chunking] {_name}: page {page_num}/{total}")

        chunks = create_chunks(
            document_id=document.id,
            course_id=args.course_id,
            document_name=path.name,
            pages=cleaned_pages,
            progress_callback=_print_progress,
            **chunk_kwargs,
        )
        count = add_chunks_to_vector_store(chunks)

        document.status = "indexed"
        db.commit()

        for chunk in chunks:
            all_chunk_rows.append(
                {
                    "chunk_id": chunk["chunk_id"],
                    "document_id": chunk["document_id"],
                    "document_name": chunk["document_name"],
                    "page": chunk["page"],
                    "chunk_index": chunk["chunk_index"],
                    "n_chars": len(str(chunk["text"])),
                    "text": chunk["text"],
                }
            )

        print(f"[OK] {path.name}: document_id={document.id}, pages={len(cleaned_pages)}, "
              f"chars={doc_chars}, chunks={count}")

    db.close()

    if all_chunk_rows:
        chunks_csv = EVAL_DIR / "chunks_full.csv"
        with chunks_csv.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(
                f, fieldnames=["chunk_id", "document_id", "document_name", "page", "chunk_index", "n_chars", "text"]
            )
            writer.writeheader()
            writer.writerows(all_chunk_rows)
        print(f"\nWrote {len(all_chunk_rows)} chunk row(s) to {chunks_csv}")

    lengths = [row["n_chars"] for row in all_chunk_rows]
    print("\n=== Corpus summary ===")
    print(f"documents: {len(files)}")
    print(f"pages: {total_pages}")
    print(f"chars: {total_chars}")
    print(f"chunks: {len(all_chunk_rows)}")
    print(f"chroma collection.count(): {vector_store.get_collection_count()}")
    if lengths:
        print(f"chunk length mean/min/max: {sum(lengths) / len(lengths):.0f} / {min(lengths)} / {max(lengths)}")


if __name__ == "__main__":
    main()
