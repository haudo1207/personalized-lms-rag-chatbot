"""Build a gold-label candidate pool for eval_questions.csv from topic-tagged chunks.

Two-step human-in-the-loop labelling, designed so the labeller never has to read
question x chunk pairs (20 x ~100), only chunk x topic once (~100):

  1. You read data/eval/chunks_full.csv (produced by ingest_corpus.py) once and tag
     every chunk with the topic(s) it covers, into data/eval/chunk_topics.csv:
         chunk_id,document_name,page,chunk_index,topics
     `topics` is a ';'-separated list drawn from the 5 topics already in
     eval_questions.csv (Khóa chính, Khóa ngoại, SQL JOIN, Chuẩn hóa cơ sở dữ liệu, ERD).
     A chunk can have zero, one, or several topics.

  2. This script joins each question's `topic` column against chunk_topics.csv to build
     a small per-question candidate pool -> data/eval/gold_candidates.csv. You then open
     that file, mark relevance 0/1 for the (usually 2-10) candidates per question, add any
     row you believe is missing, and save the result as data/eval/gold_chunks.csv:
         question_id,document_name,page,chunk_index,relevance,label_source,label_note

Deliberately, no embedding or BM25 model is used anywhere in this candidate generation --
that would make the resulting "gold" labels circular with the system being evaluated.

Usage:
    python scripts/build_gold_labels.py --init-topics     # scaffold chunk_topics.csv to fill in
    python scripts/build_gold_labels.py --candidates       # build gold_candidates.csv from chunk_topics.csv
"""

import argparse
import csv
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
os.chdir(PROJECT_ROOT)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

EVAL_DIR = Path("data/eval")
CHUNKS_FULL_CSV = EVAL_DIR / "chunks_full.csv"
CHUNK_TOPICS_CSV = EVAL_DIR / "chunk_topics.csv"
QUESTIONS_CSV = EVAL_DIR / "eval_questions.csv"
CANDIDATES_CSV = EVAL_DIR / "gold_candidates.csv"


def guard_cwd() -> None:
    if not Path("backend").is_dir():
        print("ERROR: run this from the project root.", file=sys.stderr)
        sys.exit(2)


def init_topics() -> None:
    if not CHUNKS_FULL_CSV.exists():
        print(f"ERROR: {CHUNKS_FULL_CSV} not found. Run scripts/ingest_corpus.py first.", file=sys.stderr)
        sys.exit(1)

    with QUESTIONS_CSV.open(encoding="utf-8") as f:
        topics = sorted({row["topic"] for row in csv.DictReader(f)})
    print(f"Known topics from {QUESTIONS_CSV.name}: {topics}")

    with CHUNKS_FULL_CSV.open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    if CHUNK_TOPICS_CSV.exists():
        print(f"{CHUNK_TOPICS_CSV} already exists -- not overwriting. Delete it first if you want to regenerate.")
        sys.exit(1)

    with CHUNK_TOPICS_CSV.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["chunk_id", "document_name", "page", "chunk_index", "topics", "preview"])
        writer.writeheader()
        for row in rows:
            preview = row["text"][:120].replace("\n", " ")
            writer.writerow(
                {
                    "chunk_id": row["chunk_id"],
                    "document_name": row["document_name"],
                    "page": row["page"],
                    "chunk_index": row["chunk_index"],
                    "topics": "",
                    "preview": preview,
                }
            )

    print(f"Wrote {len(rows)} row(s) to {CHUNK_TOPICS_CSV}.")
    print(f"Open it and fill the 'topics' column with ';'-separated values from: {topics}")
    print("Leave blank for chunks that cover none of the 5 exam topics.")


def build_candidates() -> None:
    if not CHUNK_TOPICS_CSV.exists():
        print(f"ERROR: {CHUNK_TOPICS_CSV} not found. Run with --init-topics first and fill it in.", file=sys.stderr)
        sys.exit(1)

    with CHUNK_TOPICS_CSV.open(encoding="utf-8") as f:
        chunk_rows = list(csv.DictReader(f))

    untagged = sum(1 for r in chunk_rows if not r["topics"].strip())
    if untagged:
        print(f"WARNING: {untagged}/{len(chunk_rows)} chunk(s) in {CHUNK_TOPICS_CSV.name} have no topic tag yet.")

    topic_to_chunks: dict[str, list[dict]] = {}
    for row in chunk_rows:
        for topic in (t.strip() for t in row["topics"].split(";")):
            if topic:
                topic_to_chunks.setdefault(topic, []).append(row)

    with QUESTIONS_CSV.open(encoding="utf-8") as f:
        questions = list(csv.DictReader(f))

    candidate_rows = []
    no_candidates: list[str] = []
    for q in questions:
        pool = topic_to_chunks.get(q["topic"], [])
        if not pool:
            no_candidates.append(q["id"])
        for chunk in pool:
            candidate_rows.append(
                {
                    "question_id": q["id"],
                    "question": q["question"],
                    "topic": q["topic"],
                    "document_name": chunk["document_name"],
                    "page": chunk["page"],
                    "chunk_index": chunk["chunk_index"],
                    "preview": chunk["preview"],
                    "relevance": "",
                    "label_source": "topic_auto",
                    "label_note": "",
                }
            )

    with CANDIDATES_CSV.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "question_id", "question", "topic", "document_name", "page", "chunk_index",
                "preview", "relevance", "label_source", "label_note",
            ],
        )
        writer.writeheader()
        writer.writerows(candidate_rows)

    print(f"Wrote {len(candidate_rows)} candidate row(s) across {len(questions)} question(s) to {CANDIDATES_CSV}.")
    if no_candidates:
        print(f"WARNING: question id(s) with zero candidates (topic not tagged on any chunk): {no_candidates}")
    print(f"\nNext: open {CANDIDATES_CSV}, set 'relevance' to 1 (relevant) or 0 (reviewed, not relevant) for "
          f"each row, add any missing chunk you believe is relevant with label_source=human_add, then save "
          f"the reviewed file as data/eval/gold_chunks.csv (only rows you set relevance=1 need to be kept, "
          f"but keeping 0 rows too is a useful audit trail).")


def main() -> None:
    guard_cwd()
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--init-topics", action="store_true")
    group.add_argument("--candidates", action="store_true")
    args = parser.parse_args()

    if args.init_topics:
        init_topics()
    else:
        build_candidates()


if __name__ == "__main__":
    main()
