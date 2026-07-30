"""Build data/eval/gold_chunks.csv with per-question keyword relevance rules.

build_gold_labels.py --candidates produces a topic-level candidate pool (every chunk
tagged with a question's topic). Several topics group multiple sub-questions (e.g.
"Chuan hoa co so du lieu" covers 6 questions: general + 1NF + 2NF + 3NF + redundancy +
functional dependency) that are NOT all relevant to the same chunks. This script applies
one additional, explicit, reproducible keyword rule PER QUESTION on top of the topic-level
pool, matched against full chunk text (not the 120-char preview), to decide relevance.

Still independent of the dense/BM25/reranker system under evaluation (same non-circularity
goal as auto_tag_chunk_topics.py). This is a documented proxy for manual human relevance
judgment -- state as a limitation in the report, not a substitute for it.

Usage:
    python scripts/auto_build_gold_chunks.py
"""

import csv
import os
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
os.chdir(PROJECT_ROOT)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

EVAL_DIR = Path("data/eval")
CHUNKS_FULL_CSV = EVAL_DIR / "chunks_full.csv"
CANDIDATES_CSV = EVAL_DIR / "gold_candidates.csv"
GOLD_CSV = EVAL_DIR / "gold_chunks.csv"

# One keyword rule per question id, applied to the candidate's full chunk text.
# A candidate is relevant iff ANY pattern for its question_id matches.
QUESTION_RULES: dict[str, list[str]] = {
    # Khoa chinh -- single concept, same definition chunks answer all 3 framings.
    "1": [r"kho[aá]\s*ch[íi]nh"],
    "11": [r"kho[aá]\s*ch[íi]nh"],
    "12": [r"kho[aá]\s*ch[íi]nh"],
    # Khoa ngoai -- textbook uses "khoa ngoai" (with "ngoai" not "ngoai").
    "2": [r"kho[aá]\s*ngo[aạà]i"],
    "13": [r"kho[aá]\s*ngo[aạà]i"],
    "19": [r"kho[aá]\s*ngo[aạà]i", r"to[aà]n\s*v[eẹ]n\s*tham\s*chi[eế]u"],
    # SQL JOIN -- corpus is relational-algebra theory (phep noi / noi ngoai), not SQL
    # syntax. Outer-join semantics (keeping unmatched tuples) is the closest match for
    # LEFT/RIGHT/FULL OUTER; plain "phep noi" definition is the closest match for INNER.
    "3": [r"n[oố]i\s*ngo[aà]i", r"kh[oô]ng\s*c[oó]\s*b[oộ]\s*li[eê]n\s*k[eế]t"],
    "14": [r"n[oố]i\s*ngo[aà]i", r"null"],
    "15": [r"n[oố]i\s*ngo[aà]i"],
    "16": [r"n[oố]i\s*ngo[aà]i"],
    "20": [r"ph[eé]p\s*n[oố]i(?!\s*ngo[aà]i)"],
    # Chuan hoa -- 1NF/2NF/3NF have precise, unambiguous notation.
    "4": [r"qu[aá]\s*tr[iì]nh\s*chu[aẩ]n\s*h[oó]a", r"chu[aẩ]n\s*h[oó]a\s*(l[aà]|c[oó]\s*ngh[iĩ]a)"],
    "5": [r"\b1nf\b", r"dạng\s*chuẩn\s*(thứ\s*nhất|1)"],
    "6": [r"\b2nf\b", r"dạng\s*chuẩn\s*(thứ\s*hai|2)"],
    "7": [r"\b3nf\b", r"dạng\s*chuẩn\s*(thứ\s*ba|3)"],
    "17": [r"d[uư]\s*th[uừ][aồ]?\s*d[uữ]\s*li[eệ]u", r"b[aấ]t\s*th[uườ]ờng"],
    "18": [r"ph[uụ]\s*thu[oộ]c\s*h[aà]m"],
    # ERD -- general vs entity vs relationship-cardinality.
    "8": [r"\berd\b", r"m[oô]\s*h[iì]nh\s*(thực\s*thể|e-?r)"],
    "9": [r"th[uự]c\s*th[eể]\s*(l[aà]|là\s*g[iì]|được\s*định\s*nghĩa)"],
    "10": [r"m[oộ]t[\s-]*nhi[eề]u", r"1[\s-]*n\b"],
}


def main() -> None:
    with CHUNKS_FULL_CSV.open(encoding="utf-8") as f:
        text_by_id = {row["chunk_id"]: row["text"] for row in csv.DictReader(f)}

    with CANDIDATES_CSV.open(encoding="utf-8") as f:
        candidates = list(csv.DictReader(f))

    out_rows = []
    n_relevant = 0
    per_question_hits: dict[str, int] = {}
    for row in candidates:
        qid = row["question_id"]
        patterns = QUESTION_RULES.get(qid, [])
        text = text_by_id.get(
            f"course1_doc1_p{row['page']}_c{row['chunk_index']}", ""
        )
        relevant = any(re.search(p, text, re.IGNORECASE) for p in patterns)
        row["relevance"] = "1" if relevant else "0"
        row["label_source"] = "keyword_rule_auto"
        if relevant:
            n_relevant += 1
            per_question_hits[qid] = per_question_hits.get(qid, 0) + 1
        out_rows.append(row)

    fieldnames = list(out_rows[0].keys())
    with GOLD_CSV.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(out_rows)

    print(f"Wrote {len(out_rows)} row(s) to {GOLD_CSV} ({n_relevant} marked relevance=1).")
    print("Relevant chunk count per question_id:")
    for qid in sorted(per_question_hits, key=int):
        print(f"  q{qid}: {per_question_hits[qid]}")
    missing = [qid for qid in QUESTION_RULES if qid not in per_question_hits]
    if missing:
        print(f"WARNING: question id(s) with ZERO relevant chunks found: {missing}")


if __name__ == "__main__":
    main()
