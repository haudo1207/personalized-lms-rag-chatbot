"""Sweep the semantic chunking breakpoint percentile and measure retrieval quality.

SEMANTIC_BREAKPOINT_PERCENTILE=95 (chunking.py) was never tuned for this corpus --
this script re-ingests the corpus at several percentiles, rebuilds gold labels for
the 20 original hand-written questions (keyword-rule pipeline, chunk-boundary
agnostic), and measures Config C (Hybrid+Reranker, no LLM calls) on exactly those
20 questions -- same method already used to compare fixed-size vs regex-semantic
vs underthesea-semantic chunking, so the numbers here are directly comparable.

The 30 auto-generated questions (id > 20) are NOT used here: their gold labels are
tied to specific chunk boundaries that shift with the percentile, so comparing on
them would not be apples-to-apples across percentiles. --allow-stale-gold is passed
to evaluate_retrieval.py so those questions are simply excluded from n_with_gold
instead of aborting the run.

Usage:
    python scripts/sweep_semantic_percentile.py --percentiles 70,80,85,90,95
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
os.chdir(PROJECT_ROOT)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

EVAL_DIR = Path("data/eval")
PER_QUERY_CSV = Path("reports/eval/retrieval_eval_per_query.csv")
SUMMARY_JSON = Path("reports/eval/retrieval_eval_summary.json")
OLD_QUESTION_MAX_ID = 20

FIXED_SIZE_BASELINE = {"hit_1": 0.70, "hit_3": 0.80, "hit_5": 0.85, "hit_10": 0.90, "mrr": 0.760, "ndcg": 0.734}
REGEX_SEMANTIC_BASELINE = {"hit_1": 0.65, "hit_3": 0.75, "hit_5": 0.75, "hit_10": 0.90, "mrr": 0.714, "ndcg": 0.717}
UNDERTHESEA_P95_BASELINE = {"hit_1": 0.60, "hit_3": 0.70, "hit_5": 0.75, "hit_10": 0.90, "mrr": 0.675, "ndcg": 0.708}


def run(cmd: list[str]) -> None:
    print(f"  $ {' '.join(cmd)}")
    result = subprocess.run([sys.executable] + cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(result.stdout[-3000:])
        print(result.stderr[-3000:], file=sys.stderr)
        raise RuntimeError(f"command failed: {' '.join(cmd)}")


def metrics_on_old_questions() -> dict:
    import csv

    with PER_QUERY_CSV.open(encoding="utf-8") as f:
        rows = [r for r in csv.DictReader(f) if r["config"] == "C" and r["repeat"] == "0"
                and int(r["question_id"]) <= OLD_QUESTION_MAX_ID]
    n = len(rows)
    if n == 0:
        return {}
    return {
        "n": n,
        "hit_1": sum(1 for r in rows if r["hit_1"] == "1") / n,
        "hit_3": sum(1 for r in rows if r["hit_3"] == "1") / n,
        "hit_5": sum(1 for r in rows if r["hit_5"] == "1") / n,
        "hit_10": sum(1 for r in rows if r["hit_10"] == "1") / n,
        "mrr": sum(float(r["reciprocal_rank"]) for r in rows) / n,
        "ndcg": sum(float(r["ndcg_at_10"]) for r in rows) / n,
    }


def fmt_row(label: str, m: dict) -> str:
    if not m:
        return f"| {label} | - | - | - | - | - | - |"
    return (f"| {label} | {m['hit_1']*100:.0f}% | {m['hit_3']*100:.0f}% | {m['hit_5']*100:.0f}% | "
            f"{m['hit_10']*100:.0f}% | {m['mrr']:.3f} | {m['ndcg']:.3f} |")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--course-id", type=int, default=1)
    parser.add_argument("--user-id", type=int, default=1)
    parser.add_argument("--percentiles", default="70,80,85,90,95")
    args = parser.parse_args()

    percentiles = [float(p) for p in args.percentiles.split(",")]
    results: dict[float, dict] = {}

    for pct in percentiles:
        print(f"\n=== percentile={pct} ===")
        run(["scripts/ingest_corpus.py", "--course-id", str(args.course_id), "--user-id", str(args.user_id),
             "--reset", "--yes", "--percentile", str(pct)])
        # init_topics() refuses to run if chunk_topics.csv already exists (by design,
        # to protect a human's hand-tagging) -- safe to delete here since this whole
        # pipeline re-derives it automatically every round anyway.
        (EVAL_DIR / "chunk_topics.csv").unlink(missing_ok=True)
        run(["scripts/build_gold_labels.py", "--init-topics"])
        run(["scripts/auto_tag_chunk_topics.py"])
        run(["scripts/build_gold_labels.py", "--candidates"])
        run(["scripts/auto_build_gold_chunks.py"])
        run(["scripts/evaluate_retrieval.py", "--configs", "C", "--repeats", "1", "--allow-stale-gold"])
        results[pct] = metrics_on_old_questions()
        print(f"  -> {results[pct]}")

    lines = ["", "=== Percentile sweep vs baselines (đúng 20 câu hỏi gốc) ===", "",
             "| Cấu hình | Hit@1 | Hit@3 | Hit@5 | Hit@10 | MRR | nDCG |",
             "|---|---|---|---|---|---|---|",
             fmt_row("Fixed-size (baseline gốc)", FIXED_SIZE_BASELINE),
             fmt_row("Semantic + regex tách câu", REGEX_SEMANTIC_BASELINE),
             fmt_row("Semantic + underthesea, percentile=95 (trước sweep)", UNDERTHESEA_P95_BASELINE)]
    for pct in percentiles:
        lines.append(fmt_row(f"Semantic + underthesea, percentile={pct}", results[pct]))
    print("\n".join(lines))

    out_path = Path("reports/eval/percentile_sweep_table.md")
    out_path.write_text("\n".join(lines), encoding="utf-8")
    with Path("reports/eval/percentile_sweep_summary.json").open("w", encoding="utf-8") as f:
        json.dump({str(k): v for k, v in results.items()}, f, ensure_ascii=False, indent=2)
    print(f"\nWrote:\n  {out_path}\n  reports/eval/percentile_sweep_summary.json")


if __name__ == "__main__":
    main()
