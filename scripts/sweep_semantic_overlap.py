"""Sweep the semantic chunking sentence-overlap count at the tuned percentile=85.

Fixed-size chunking always shares DEFAULT_OVERLAP chars between adjacent chunks;
semantic grouping (chunking.py::create_semantic_chunks) previously had none between
groups at all. This tests whether carrying the last N sentences of each group into
the next one closes some of the gap to fixed-size, using the exact same method as
scripts/sweep_semantic_percentile.py (Config C only, measured on the 20 original
hand-written questions, gold rebuilt fresh each round).

Usage:
    python scripts/sweep_semantic_overlap.py --overlaps 0,1,2,3
"""

import argparse
import csv
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
OLD_QUESTION_MAX_ID = 20

FIXED_SIZE_BASELINE = {"hit_1": 0.70, "hit_3": 0.80, "hit_5": 0.85, "hit_10": 0.90, "mrr": 0.760, "ndcg": 0.734}
PERCENTILE_85_NO_OVERLAP_BASELINE = {"hit_1": 0.65, "hit_3": 0.75, "hit_5": 0.75, "hit_10": 0.90, "mrr": 0.722, "ndcg": 0.718}


def run(cmd: list[str]) -> None:
    print(f"  $ {' '.join(cmd)}")
    result = subprocess.run([sys.executable] + cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(result.stdout[-3000:])
        print(result.stderr[-3000:], file=sys.stderr)
        raise RuntimeError(f"command failed: {' '.join(cmd)}")


def metrics_on_old_questions() -> dict:
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
    parser.add_argument("--overlaps", default="0,1,2,3")
    args = parser.parse_args()

    overlaps = [int(o) for o in args.overlaps.split(",")]
    results: dict[int, dict] = {}

    for ov in overlaps:
        print(f"\n=== overlap_sentences={ov} ===")
        run(["scripts/ingest_corpus.py", "--course-id", str(args.course_id), "--user-id", str(args.user_id),
             "--reset", "--yes", "--overlap-sentences", str(ov)])
        (EVAL_DIR / "chunk_topics.csv").unlink(missing_ok=True)
        run(["scripts/build_gold_labels.py", "--init-topics"])
        run(["scripts/auto_tag_chunk_topics.py"])
        run(["scripts/build_gold_labels.py", "--candidates"])
        run(["scripts/auto_build_gold_chunks.py"])
        run(["scripts/evaluate_retrieval.py", "--configs", "C", "--repeats", "1", "--allow-stale-gold"])
        results[ov] = metrics_on_old_questions()
        print(f"  -> {results[ov]}")

    lines = ["", "=== Overlap sentences sweep vs baselines (percentile=85, đúng 20 câu hỏi gốc) ===", "",
             "| Cấu hình | Hit@1 | Hit@3 | Hit@5 | Hit@10 | MRR | nDCG |",
             "|---|---|---|---|---|---|---|",
             fmt_row("Fixed-size (baseline gốc)", FIXED_SIZE_BASELINE),
             fmt_row("Semantic p=85, overlap=0 (trước sweep)", PERCENTILE_85_NO_OVERLAP_BASELINE)]
    for ov in overlaps:
        lines.append(fmt_row(f"Semantic p=85, overlap_sentences={ov}", results[ov]))
    print("\n".join(lines))

    out_path = Path("reports/eval/overlap_sweep_table.md")
    out_path.write_text("\n".join(lines), encoding="utf-8")
    with Path("reports/eval/overlap_sweep_summary.json").open("w", encoding="utf-8") as f:
        json.dump({str(k): v for k, v in results.items()}, f, ensure_ascii=False, indent=2)
    print(f"\nWrote:\n  {out_path}\n  reports/eval/overlap_sweep_summary.json")


if __name__ == "__main__":
    main()
