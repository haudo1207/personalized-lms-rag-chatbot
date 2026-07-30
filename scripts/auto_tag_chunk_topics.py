"""Fill data/eval/chunk_topics.csv with keyword-based topic tags.

build_gold_labels.py --init-topics deliberately asks a human to tag each chunk so the
resulting gold labels aren't circular with the embedding/BM25 system under evaluation.
With 443 real chunks, tagging by hand is impractical for this project, so this script
does the tagging with an explicit, reproducible keyword rulebook instead of a human --
still independent of the dense/BM25/reranker pipeline being measured, but not a true
independent human annotation. Document this as a limitation in the report.

Usage:
    python scripts/auto_tag_chunk_topics.py
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
CHUNK_TOPICS_CSV = EVAL_DIR / "chunk_topics.csv"

# Keyword rulebook -- a chunk gets a topic if any of its patterns match (case-insensitive).
TOPIC_KEYWORDS: dict[str, list[str]] = {
    "Khóa chính": [r"kho[aá]\s*ch[íi]nh", r"primary\s*key"],
    "Khóa ngoại": [r"kho[aá]\s*ngo[aạ]i", r"kho[aá]\s*ngo[aà]i", r"foreign\s*key"],
    "SQL JOIN": [
        r"\bjoin\b", r"inner\s*join", r"left\s*join", r"right\s*join",
        r"full\s*outer\s*join", r"ph[eé]p\s*n[oố]i", r"to[aá]n\s*t[uử]\s*n[oố]i",
    ],
    "Chuẩn hóa cơ sở dữ liệu": [
        r"chu[aẩ]n\s*h[oó]a", r"d[aạ]ng\s*chu[aẩ]n", r"\b1nf\b", r"\b2nf\b", r"\b3nf\b",
        r"\bbcnf\b", r"ph[uụ]\s*thu[oộ]c\s*h[aà]m", r"d[uư]\s*th[uừ][aồ]?\s*d[uữ]\s*li[eệ]u",
    ],
    "ERD": [
        r"\berd\b", r"th[uự]c\s*th[eể]", r"m[oô]\s*h[iì]nh\s*(thực\s*thể|e-?r)",
        r"quan\s*h[eệ]\s*(gi[uữ]a|m[oộ]t-nhi[eề]u|nhi[eề]u-nhi[eề]u)", r"l[uượ][cợ]\s*đ[oồ]",
    ],
}
COMPILED = {topic: [re.compile(p, re.IGNORECASE) for p in pats] for topic, pats in TOPIC_KEYWORDS.items()}


def tag_text(text: str) -> str:
    hits = [topic for topic, patterns in COMPILED.items() if any(p.search(text) for p in patterns)]
    return ";".join(hits)


def main() -> None:
    with CHUNKS_FULL_CSV.open(encoding="utf-8") as f:
        text_by_id = {row["chunk_id"]: row["text"] for row in csv.DictReader(f)}

    with CHUNK_TOPICS_CSV.open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
        fieldnames = list(rows[0].keys())

    counts: dict[str, int] = {topic: 0 for topic in TOPIC_KEYWORDS}
    n_tagged = 0
    for row in rows:
        text = text_by_id.get(row["chunk_id"], "")
        topics = tag_text(text)
        row["topics"] = topics
        if topics:
            n_tagged += 1
            for topic in topics.split(";"):
                counts[topic] += 1

    with CHUNK_TOPICS_CSV.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Tagged {n_tagged}/{len(rows)} chunk(s) with at least one topic.")
    for topic, count in counts.items():
        print(f"  {topic}: {count} chunk(s)")


if __name__ == "__main__":
    main()
