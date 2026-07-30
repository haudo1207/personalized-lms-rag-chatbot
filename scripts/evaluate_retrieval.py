"""Measure Recall@K / HitRate@K / MRR / latency for the retrieval pipeline, for real.

Replaces the fabricated "thực nghiệm" table in the report (Recall@3/@10, Faithfulness,
latency for Dense / Hybrid / Hybrid+Reranker) with numbers actually computed against
data/eval/eval_questions.csv and data/eval/gold_chunks.csv.

Faithfulness / generation quality is explicitly OUT OF SCOPE here -- this only measures
what the local embedding model can measure (retrieval), not what the LLM does with it.

Usage:
    python scripts/evaluate_retrieval.py --repeats 3
    python scripts/evaluate_retrieval.py --repeats 3 --configs A,B --allow-stale-gold
"""

import argparse
import csv
import json
import math
import os
import platform
import subprocess
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
os.chdir(PROJECT_ROOT)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from backend.services.embedding_service import MODEL_NAME, embed_text  # noqa: E402
from backend.services.retriever import (  # noqa: E402
    BM25_CANDIDATES,
    DENSE_CANDIDATES,
    RRF_K,
    _get_bm25_index,
    retrieve_ranked,
)
from backend.services.vector_store import get_collection_count, search_chunks  # noqa: E402
from backend.services.chunking import DEFAULT_CHUNK_SIZE, DEFAULT_OVERLAP  # noqa: E402

EVAL_DIR = Path("data/eval")
QUESTIONS_CSV = EVAL_DIR / "eval_questions.csv"
GOLD_CSV = EVAL_DIR / "gold_chunks.csv"
OUT_DIR = Path("reports/eval")

CONFIGS = {
    "A": {"label": "Dense (vector only)", "use_bm25": False, "use_reranker": False, "use_multi_query": False},
    "B": {"label": "Hybrid (vector + BM25 + RRF)", "use_bm25": True, "use_reranker": False, "use_multi_query": False},
    "C": {"label": "Hybrid + Reranker", "use_bm25": True, "use_reranker": True, "use_multi_query": False},
    "D": {"label": "Hybrid + Reranker + Multi-Query", "use_bm25": True, "use_reranker": True, "use_multi_query": True},
}

K_VALUES = (1, 3, 5, 10)


def guard_cwd() -> None:
    if not Path("backend").is_dir():
        print("ERROR: run this from the project root.", file=sys.stderr)
        sys.exit(2)


def load_questions() -> list[dict]:
    with QUESTIONS_CSV.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def load_gold(course_id: int) -> dict[str, set[tuple]]:
    """question_id -> set of (document_name, page, chunk_index) with relevance == 1."""
    gold: dict[str, set[tuple]] = {}
    if not GOLD_CSV.exists():
        return gold
    with GOLD_CSV.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row.get("relevance") not in ("1", 1):
                continue
            key = (row["document_name"], str(row["page"]), str(row["chunk_index"]))
            gold.setdefault(row["question_id"], set()).add(key)
    return gold


def chunk_key(chunk: dict) -> tuple:
    meta = chunk["metadata"]
    return (str(meta["document_name"]), str(meta["page"]), str(meta["chunk_index"]))


def resolve_gold_against_chroma(gold: dict[str, set[tuple]], course_id: int) -> tuple[int, int]:
    """Return (n_resolved, n_unresolved) gold rows against what's actually in Chroma."""
    all_keys: set[tuple] = set()
    # Pull every chunk for the course once, keyed the same way as gold.
    probe = search_chunks("probe", course_id=course_id, top_k=10_000)
    for chunk in probe:
        all_keys.add(chunk_key(chunk))

    resolved = 0
    unresolved: list[tuple[str, tuple]] = []
    for qid, keys in gold.items():
        for key in keys:
            if key in all_keys:
                resolved += 1
            else:
                unresolved.append((qid, key))
    return resolved, unresolved


def wilson_ci(successes: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (0.0, 0.0)
    p = successes / n
    denom = 1 + z**2 / n
    center = p + z**2 / (2 * n)
    margin = z * math.sqrt(p * (1 - p) / n + z**2 / (4 * n**2))
    lo = (center - margin) / denom
    hi = (center + margin) / denom
    return (max(0.0, lo), min(1.0, hi))


def ndcg_binary(hits: list[int], k: int) -> float:
    dcg = sum(hit / math.log2(i + 2) for i, hit in enumerate(hits[:k]))
    ideal_hits = sorted(hits[:k], reverse=True)
    idcg = sum(hit / math.log2(i + 2) for i, hit in enumerate(ideal_hits))
    return dcg / idcg if idcg > 0 else 0.0


def git_short_hash() -> str:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True, check=True
        )
        return out.stdout.strip()
    except Exception:
        return "unknown"


def percentile(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    s = sorted(values)
    idx = min(len(s) - 1, int(round(pct / 100 * (len(s) - 1))))
    return s[idx]


def main() -> None:
    guard_cwd()

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--course-id", type=int, default=1)
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--configs", default="A,B,C,D")
    parser.add_argument("--allow-stale-gold", action="store_true")
    parser.add_argument("--out-dir", default=str(OUT_DIR))
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    config_keys = args.configs.split(",")

    # --- Preflight ---
    n_total = get_collection_count()
    course_chunks = search_chunks("probe", course_id=args.course_id, top_k=10_000)
    print(f"[preflight] collection.count()={n_total}, chunks for course_id={args.course_id}: {len(course_chunks)}")
    if len(course_chunks) == 0:
        print("ERROR: no chunks indexed for this course. Run scripts/ingest_corpus.py first.", file=sys.stderr)
        sys.exit(1)

    questions = load_questions()
    questions = [q for q in questions if int(q["course_id"]) == args.course_id]
    gold = load_gold(args.course_id)

    if not gold:
        print(f"ERROR: {GOLD_CSV} not found or empty. Run scripts/build_gold_labels.py and label it first.",
              file=sys.stderr)
        sys.exit(1)

    resolved, unresolved = resolve_gold_against_chroma(gold, args.course_id)
    if unresolved:
        print(f"[preflight] {len(unresolved)} gold row(s) do not resolve to any chunk currently in Chroma "
              f"(stale gold -- likely re-indexed since labelling):")
        for qid, key in unresolved[:20]:
            print(f"    question_id={qid}  {key}")
        if not args.allow_stale_gold:
            print("Aborting. Re-run build_gold_labels.py against the current corpus, or pass --allow-stale-gold.",
                  file=sys.stderr)
            sys.exit(1)

    n_with_gold = sum(1 for q in questions if q["id"] in gold and gold[q["id"]])
    print(f"[preflight] n_questions_with_gold = {n_with_gold} of {len(questions)}")

    # --- Warm-up (excluded from all timings) ---
    embed_text("warmup")
    search_chunks("warmup", course_id=args.course_id, top_k=1)
    t_bm25_build = time.perf_counter()
    _get_bm25_index(args.course_id, None)
    bm25_build_ms = (time.perf_counter() - t_bm25_build) * 1000
    print(f"[warmup] BM25 index build (one-off, cached afterward): {bm25_build_ms:.1f} ms")
    if "C" in config_keys:
        from backend.services.reranker import get_reranker_model
        t_rerank_load = time.perf_counter()
        get_reranker_model().predict([("warmup", "warmup")])
        rerank_load_ms = (time.perf_counter() - t_rerank_load) * 1000
        print(f"[warmup] Cross-encoder reranker model load (one-off): {rerank_load_ms:.1f} ms")

    # --- Main loop ---
    per_query_rows: list[dict] = []
    quality_by_config: dict[str, list[dict]] = {k: [] for k in config_keys}

    for rep in range(args.repeats):
        for cfg_key in config_keys:
            cfg = CONFIGS[cfg_key]
            for q in questions:
                qid = q["id"]
                gold_keys = gold.get(qid, set())
                timings: dict[str, float] = {}
                ranked = retrieve_ranked(
                    q["question"],
                    course_id=args.course_id,
                    top_k=10,
                    use_bm25=cfg["use_bm25"],
                    use_reranker=cfg["use_reranker"],
                    use_multi_query=cfg["use_multi_query"],
                    timings=timings,
                )
                retrieved_keys = [chunk_key(c) for c in ranked]
                hits = [1 if key in gold_keys else 0 for key in retrieved_keys]

                n_gold = len(gold_keys)
                rank_of_first = next((i + 1 for i, h in enumerate(hits) if h), None)
                reciprocal_rank = 1.0 / rank_of_first if rank_of_first else 0.0

                row = {
                    "repeat": rep,
                    "config": cfg_key,
                    "question_id": qid,
                    "question": q["question"],
                    "topic": q["topic"],
                    "question_type": q["question_type"],
                    "n_gold": n_gold,
                    "rank_of_first_relevant": rank_of_first or "",
                    "reciprocal_rank": reciprocal_rank,
                    "ndcg_at_10": ndcg_binary(hits, 10),
                    "multi_query_ms": timings.get("multi_query_ms", 0.0),
                    "dense_ms": timings.get("dense_ms", 0.0),
                    "bm25_ms": timings.get("bm25_ms", 0.0),
                    "fusion_ms": timings.get("fusion_ms", 0.0),
                    "rerank_ms": timings.get("rerank_ms", 0.0),
                    "total_ms": timings.get("total_ms", 0.0),
                    "retrieved_chunk_ids": ";".join(c["chunk_id"] for c in ranked),
                }
                for k in K_VALUES:
                    row[f"hit_{k}"] = 1 if any(hits[:k]) else 0
                n_relevant_at_10 = sum(hits[:10])
                row["n_relevant_at_10"] = n_relevant_at_10
                row["recall_at_10"] = (n_relevant_at_10 / n_gold) if n_gold else 0.0
                per_query_rows.append(row)

                if rep == 0:
                    quality_by_config[cfg_key].append(row)
                elif n_gold and rep > 0:
                    # Sanity check: pipeline has no randomness, quality metrics must be stable.
                    first_hits = quality_by_config[cfg_key][
                        [r["question_id"] for r in quality_by_config[cfg_key]].index(qid)
                    ]
                    if first_hits["hit_10"] != row["hit_10"]:
                        print(f"[WARN] non-deterministic result for question_id={qid} config={cfg_key} "
                              f"repeat={rep} (HNSW tie-break drift?) -- quality metrics use repeat 0 only.")

    # --- Aggregate metrics (quality: repeat 0 only; latency: all repeats) ---
    summary_rows = []
    for cfg_key in config_keys:
        cfg = CONFIGS[cfg_key]
        q_rows = [r for r in quality_by_config[cfg_key] if r["n_gold"] > 0]
        n = len(q_rows)
        lat_rows = [r for r in per_query_rows if r["config"] == cfg_key]

        summary = {"config": cfg_key, "label": cfg["label"], "n_questions_with_gold": n}
        for k in K_VALUES:
            hits_k = sum(r[f"hit_{k}"] for r in q_rows)
            lo, hi = wilson_ci(hits_k, n)
            summary[f"hitrate_at_{k}"] = hits_k / n if n else 0.0
            summary[f"hitrate_at_{k}_ci95"] = (round(lo, 3), round(hi, 3))
        summary["recall_at_10_macro"] = sum(r["recall_at_10"] for r in q_rows) / n if n else 0.0
        summary["mrr_at_10"] = sum(r["reciprocal_rank"] for r in q_rows) / n if n else 0.0
        precision_at_3 = sum(min(r["n_relevant_at_10"], 3) / 3 for r in q_rows) / n if n else 0.0
        summary["precision_at_3"] = precision_at_3
        summary["ndcg_at_10"] = sum(r["ndcg_at_10"] for r in q_rows) / n if n else 0.0

        totals = [r["total_ms"] for r in lat_rows]
        summary["latency_mean_ms"] = sum(totals) / len(totals) if totals else 0.0
        summary["latency_median_ms"] = percentile(totals, 50)
        summary["latency_p95_ms"] = percentile(totals, 95)
        summary["stage_ms"] = {
            stage: sum(r[stage] for r in lat_rows) / len(lat_rows) if lat_rows else 0.0
            for stage in ("multi_query_ms", "dense_ms", "bm25_ms", "fusion_ms", "rerank_ms")
        }
        summary_rows.append(summary)

    # --- Per-topic breakdown ---
    topics = sorted({q["topic"] for q in questions})
    topic_breakdown = {}
    for cfg_key in config_keys:
        topic_breakdown[cfg_key] = {}
        for topic in topics:
            rows = [r for r in quality_by_config[cfg_key] if r["topic"] == topic and r["n_gold"] > 0]
            n = len(rows)
            topic_breakdown[cfg_key][topic] = {
                "n": n,
                "hitrate_at_3": (sum(r["hit_3"] for r in rows) / n) if n else None,
            }

    # --- Write outputs ---
    per_query_csv = out_dir / "retrieval_eval_per_query.csv"
    fieldnames = list(per_query_rows[0].keys()) if per_query_rows else []
    with per_query_csv.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(per_query_rows)

    summary_csv = out_dir / "retrieval_eval_summary.csv"
    summary_fieldnames = [k for k in summary_rows[0].keys() if k != "stage_ms"] if summary_rows else []
    with summary_csv.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=summary_fieldnames)
        writer.writeheader()
        for row in summary_rows:
            writer.writerow({k: row[k] for k in summary_fieldnames})

    run_metadata = {
        "timestamp_utc": None,  # fill after the run -- Date.now() unavailable inside orchestration; stamp manually if needed
        "git_commit": git_short_hash(),
        "embedding_model": MODEL_NAME,
        "chunk_size": DEFAULT_CHUNK_SIZE,
        "overlap": DEFAULT_OVERLAP,
        "dense_candidates": DENSE_CANDIDATES,
        "bm25_candidates": BM25_CANDIDATES,
        "rrf_k": RRF_K,
        "collection_count": n_total,
        "n_documents_course": len({c["metadata"]["document_id"] for c in course_chunks}),
        "n_chunks_course": len(course_chunks),
        "n_questions": len(questions),
        "n_questions_with_gold": n_with_gold,
        "repeats": args.repeats,
        "bm25_build_ms_oneoff": round(bm25_build_ms, 1),
        "python_version": sys.version.split()[0],
        "platform_processor": platform.processor(),
    }
    for lib_name in ("torch", "chromadb", "sentence_transformers"):
        try:
            mod = __import__(lib_name)
            run_metadata[f"{lib_name}_version"] = getattr(mod, "__version__", "unknown")
        except Exception:
            run_metadata[f"{lib_name}_version"] = "not installed"

    summary_json = out_dir / "retrieval_eval_summary.json"
    with summary_json.open("w", encoding="utf-8") as f:
        json.dump(
            {"run_metadata": run_metadata, "configs": summary_rows, "topic_breakdown": topic_breakdown},
            f, ensure_ascii=False, indent=2,
        )

    # --- Markdown table ---
    lines = ["| Cấu hình | HitRate@1 | HitRate@3 | HitRate@5 | HitRate@10 | Recall@10 | MRR@10 | "
             "Precision@3 | nDCG@10 | Latency mean/median/p95 (ms) |",
             "|---|---|---|---|---|---|---|---|---|---|"]
    for row in summary_rows:
        ci3 = row["hitrate_at_3_ci95"]
        lines.append(
            f"| {row['label']} | {row['hitrate_at_1']*100:.1f}% | "
            f"{row['hitrate_at_3']*100:.1f}% (95% CI {ci3[0]*100:.0f}-{ci3[1]*100:.0f}%) | "
            f"{row['hitrate_at_5']*100:.1f}% | {row['hitrate_at_10']*100:.1f}% | "
            f"{row['recall_at_10_macro']*100:.1f}% | {row['mrr_at_10']:.3f} | "
            f"{row['precision_at_3']:.3f} | {row['ndcg_at_10']:.3f} | "
            f"{row['latency_mean_ms']:.0f} / {row['latency_median_ms']:.0f} / {row['latency_p95_ms']:.0f} |"
        )
    lines.append("")
    lines.append(f"n = {n_with_gold} of {len(questions)} questions have gold labels "
                 f"(metrics computed on the {n_with_gold} with labels). "
                 f"Chunk size {run_metadata['chunk_size']}/overlap {run_metadata['overlap']}. "
                 f"Commit `{run_metadata['git_commit']}`. Corpus: {run_metadata['n_documents_course']} document(s), "
                 f"{run_metadata['n_chunks_course']} chunk(s). BM25 index build (one-off, excluded from latency): "
                 f"{run_metadata['bm25_build_ms_oneoff']:.0f} ms.")
    table_md = out_dir / "retrieval_eval_table.md"
    table_md.write_text("\n".join(lines), encoding="utf-8")

    print("\n" + "\n".join(lines))
    print(f"\nWrote:\n  {per_query_csv}\n  {summary_csv}\n  {summary_json}\n  {table_md}")


if __name__ == "__main__":
    main()
