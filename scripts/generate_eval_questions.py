"""Grow the eval question set by generating questions FROM specific known chunks.

The 20 hand-written questions in eval_questions.csv needed gold labels reconstructed
after the fact (auto_build_gold_chunks.py, keyword rules) -- a real but imperfect proxy
for human judgment. Here the causality runs the other way: pick a chunk first, ask Gemini
for a question whose answer lives in that exact chunk, so the gold label is the source
chunk itself -- exact by construction, no proxy needed. Same idea as RAGAS's
TestsetGenerator, scaled down to single-hop/single-chunk questions (no knowledge-graph
multi-hop synthesis).

Must be run AFTER ingest_corpus.py + build_gold_labels.py + auto_tag_chunk_topics.py for
the CURRENT chunk boundaries, since it samples from chunk_topics.csv.

Usage:
    python scripts/generate_eval_questions.py --per-topic 6
"""

import argparse
import csv
import os
import random
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
os.chdir(PROJECT_ROOT)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from backend.services.llm_service import generate_answer  # noqa: E402

EVAL_DIR = Path("data/eval")
CHUNKS_FULL_CSV = EVAL_DIR / "chunks_full.csv"
CHUNK_TOPICS_CSV = EVAL_DIR / "chunk_topics.csv"
QUESTIONS_CSV = EVAL_DIR / "eval_questions.csv"
GOLD_CSV = EVAL_DIR / "gold_chunks.csv"

QUESTION_TYPES = ["definition", "comparison", "reasoning", "constraint", "behavior", "usage"]
MIN_CHUNK_CHARS_FOR_QUESTION = 150

GENERATE_PROMPT = """Dựa CHỈ VÀO đoạn văn bản sau (trích từ giáo trình Cơ sở dữ liệu), hãy đặt \
1 câu hỏi mà đoạn văn bản này chứa đủ thông tin để trả lời, cùng với câu trả lời ngắn gọn, chuẩn xác.

Đoạn văn bản:
{text}

Trả về đúng 2 dòng, không thêm gì khác:
Câu hỏi: <câu hỏi>
Trả lời: <câu trả lời ngắn gọn>"""


def guard_cwd() -> None:
    if not Path("backend").is_dir():
        print("ERROR: run this from the project root.", file=sys.stderr)
        sys.exit(2)


def parse_generated(raw: str) -> tuple[str, str] | None:
    question, answer = None, None
    for line in raw.strip().splitlines():
        line = line.strip()
        if line.lower().startswith("câu hỏi:"):
            question = line.split(":", 1)[1].strip()
        elif line.lower().startswith("trả lời:"):
            answer = line.split(":", 1)[1].strip()
    if question and answer:
        return question, answer
    return None


def main() -> None:
    guard_cwd()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--course-id", type=int, default=1)
    parser.add_argument("--per-topic", type=int, default=6)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    with CHUNKS_FULL_CSV.open(encoding="utf-8") as f:
        text_by_key = {
            (row["document_name"], row["page"], row["chunk_index"]): row["text"]
            for row in csv.DictReader(f)
        }

    with CHUNK_TOPICS_CSV.open(encoding="utf-8") as f:
        chunk_rows = list(csv.DictReader(f))

    by_topic: dict[str, list[dict]] = {}
    for row in chunk_rows:
        text = text_by_key.get((row["document_name"], row["page"], row["chunk_index"]), "")
        if len(text) < MIN_CHUNK_CHARS_FOR_QUESTION:
            continue
        for topic in (t.strip() for t in row["topics"].split(";")):
            if topic:
                by_topic.setdefault(topic, []).append(row)

    rng = random.Random(args.seed)
    with QUESTIONS_CSV.open(encoding="utf-8") as f:
        existing_questions = list(csv.DictReader(f))
        q_fieldnames = list(existing_questions[0].keys())
    next_id = max(int(q["id"]) for q in existing_questions) + 1

    with GOLD_CSV.open(encoding="utf-8") as f:
        existing_gold = list(csv.DictReader(f))
        gold_fieldnames = list(existing_gold[0].keys())

    new_questions, new_gold, skipped = [], [], 0
    for topic, rows in by_topic.items():
        sample = rng.sample(rows, min(args.per_topic, len(rows)))
        for row in sample:
            key = (row["document_name"], row["page"], row["chunk_index"])
            text = text_by_key[key]
            try:
                parsed = parse_generated(generate_answer(GENERATE_PROMPT.format(text=text)))
            except Exception as exc:
                print(f"[WARN] generation failed for {key}: {exc}")
                parsed = None
            if parsed is None:
                skipped += 1
                continue
            question, ground_truth = parsed
            qid = str(next_id)
            next_id += 1
            new_questions.append(
                {
                    "id": qid,
                    "course_id": args.course_id,
                    "question": question,
                    "ground_truth": ground_truth,
                    "topic": topic,
                    "question_type": rng.choice(QUESTION_TYPES),
                }
            )
            new_gold.append(
                {
                    "question_id": qid,
                    "question": question,
                    "topic": topic,
                    "document_name": row["document_name"],
                    "page": row["page"],
                    "chunk_index": row["chunk_index"],
                    "preview": text[:120].replace("\n", " "),
                    "relevance": "1",
                    "label_source": "auto_generated_from_source_chunk",
                    "label_note": "",
                }
            )
            print(f"[{topic}] {question}")

    with QUESTIONS_CSV.open("a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=q_fieldnames)
        writer.writerows(new_questions)

    with GOLD_CSV.open("a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=gold_fieldnames)
        writer.writerows(new_gold)

    print(f"\nAdded {len(new_questions)} question(s) across {len(by_topic)} topic(s) "
          f"({skipped} skipped due to generation/parse failure).")
    print(f"Wrote to {QUESTIONS_CSV} and {GOLD_CSV}.")


if __name__ == "__main__":
    main()
