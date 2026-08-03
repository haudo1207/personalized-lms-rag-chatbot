"""Paired significance test between two retrieval configs, on the SAME questions.

evaluate_retrieval.py already reports a Wilson 95% CI per config independently
(is HitRate@3 different from zero, roughly). That's the wrong tool for "is
config A actually better than config B?" -- two independent CIs can overlap
even when A beats B on every single question, and can look "different" even
when the gap is just noise, because it throws away the pairing (same question,
two configs) that a paired test exploits.

This script uses the pairing: for each question, take config A's score minus
config B's score, then (1) a Wilcoxon signed-rank test on those paired
differences, and (2) a paired bootstrap 95% CI on the mean difference (resample
questions with replacement, not the raw scores -- the question is the unit of
observation). If the bootstrap CI for the difference straddles zero, report
"no significant difference" rather than picking a winner from noise.

Usage:
    python scripts/eval_significance.py --csv reports/eval/retrieval_eval_per_query.csv \
        --config-a C --config-b D --metric reciprocal_rank
"""

import argparse
import csv
import sys
from pathlib import Path

import numpy as np
from scipy.stats import wilcoxon

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BOOTSTRAP_SEED = 0  # fixed for reproducibility -- rerunning this script must give the same CI


def load_paired_scores(csv_path: Path, config_a: str, config_b: str, metric: str) -> list[tuple[str, float, float]]:
    """Returns [(question_id, score_a, score_b), ...] for repeat==0 rows with
    gold labels (n_gold > 0), restricted to questions both configs answered."""
    by_config: dict[str, dict[str, float]] = {config_a: {}, config_b: {}}
    with csv_path.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row.get("repeat") != "0":
                continue
            if row["config"] not in by_config:
                continue
            if int(row.get("n_gold", 0)) <= 0:
                continue
            by_config[row["config"]][row["question_id"]] = float(row[metric])

    shared_ids = sorted(set(by_config[config_a]) & set(by_config[config_b]), key=int)
    return [(qid, by_config[config_a][qid], by_config[config_b][qid]) for qid in shared_ids]


def paired_bootstrap_ci(diffs: np.ndarray, n_bootstrap: int, seed: int) -> tuple[float, float]:
    rng = np.random.default_rng(seed)
    n = len(diffs)
    resampled_means = np.empty(n_bootstrap)
    for i in range(n_bootstrap):
        sample = rng.choice(diffs, size=n, replace=True)
        resampled_means[i] = sample.mean()
    lo, hi = np.percentile(resampled_means, [2.5, 97.5])
    return float(lo), float(hi)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", default="reports/eval/retrieval_eval_per_query.csv")
    parser.add_argument("--config-a", required=True)
    parser.add_argument("--config-b", required=True)
    parser.add_argument("--metric", default="reciprocal_rank", choices=[
        "reciprocal_rank", "hit_1", "hit_3", "hit_5", "hit_10", "ndcg_at_10", "recall_at_10",
    ])
    parser.add_argument("--n-bootstrap", type=int, default=2000)
    args = parser.parse_args()

    pairs = load_paired_scores(Path(args.csv), args.config_a, args.config_b, args.metric)
    if not pairs:
        print(f"ERROR: no shared, gold-labeled questions found for configs "
              f"{args.config_a!r}/{args.config_b!r} in {args.csv}", file=sys.stderr)
        sys.exit(1)

    scores_a = np.array([p[1] for p in pairs])
    scores_b = np.array([p[2] for p in pairs])
    diffs = scores_a - scores_b
    n = len(diffs)
    mean_diff = float(diffs.mean())

    ci_lo, ci_hi = paired_bootstrap_ci(diffs, args.n_bootstrap, BOOTSTRAP_SEED)

    if np.all(diffs == 0):
        wilcoxon_stat, wilcoxon_p = float("nan"), 1.0
    else:
        wilcoxon_stat, wilcoxon_p = wilcoxon(scores_a, scores_b)

    significant = not (ci_lo <= 0.0 <= ci_hi)

    print(f"Paired comparison: config {args.config_a!r} vs config {args.config_b!r}, "
          f"metric={args.metric}, n={n} questions (matched, gold-labeled, repeat=0)\n")
    print(f"  mean({args.config_a}) = {scores_a.mean():.4f}")
    print(f"  mean({args.config_b}) = {scores_b.mean():.4f}")
    print(f"  mean difference ({args.config_a} - {args.config_b}) = {mean_diff:+.4f}")
    print(f"  95% bootstrap CI on the difference (n_bootstrap={args.n_bootstrap}, seed={BOOTSTRAP_SEED}): "
          f"[{ci_lo:+.4f}, {ci_hi:+.4f}]")
    print(f"  Wilcoxon signed-rank: statistic={wilcoxon_stat:.2f}, p={wilcoxon_p:.4f}\n")

    if significant:
        direction = args.config_a if mean_diff > 0 else args.config_b
        print(f"VERDICT: statistically significant difference (95% CI excludes 0) -- "
              f"{direction!r} scores higher on {args.metric}.")
    else:
        print(f"VERDICT: NOT statistically significant (95% CI includes 0) -- "
              f"on this question set, cannot conclude {args.config_a!r} and {args.config_b!r} differ. "
              f"Report this as 'no significant difference found', not as one config beating the other.")


if __name__ == "__main__":
    main()
