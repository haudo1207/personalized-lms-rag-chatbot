"""Measure generation quality (Faithfulness, Answer Relevancy) for real, RAGAS-lite.

Complements evaluate_retrieval.py, which only measures retrieval (HitRate/MRR/nDCG) --
it never checks whether Gemini's final answer is actually faithful to the retrieved
context or on-topic for the question. Uses Gemini itself as the LLM judge (same model
already configured via GEMINI_API_KEY) instead of a second API key for GPT-4, following
the RAGAS methodology (Faithfulness + Answer Relevancy formulas) described in the AI
Vietnam "RAG Tutorial" reference read for this upgrade pass.

Context Precision / Context Recall are deliberately NOT reimplemented here -- they're
already covered by HitRate/Recall/nDCG in evaluate_retrieval.py against the same gold
labels, so redoing them with an LLM judge would just be a noisier duplicate metric.

Usage:
    python scripts/evaluate_generation.py --config D
    python scripts/evaluate_generation.py --config C --limit 5
"""

import argparse
import csv
import json
import os
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
os.chdir(PROJECT_ROOT)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from backend.services.embedding_service import embed_text  # noqa: E402
from backend.services.llm_service import generate_answer  # noqa: E402
from backend.services.prompt_template import INSUFFICIENT_INFORMATION_ANSWER, build_rag_prompt  # noqa: E402
from backend.services.rag_pipeline import format_context  # noqa: E402
from backend.services.retriever import retrieve_ranked  # noqa: E402

EVAL_DIR = Path("data/eval")
QUESTIONS_CSV = EVAL_DIR / "eval_questions.csv"
OUT_DIR = Path("reports/eval")

CONFIGS = {
    "C": {"label": "Hybrid + Reranker", "use_bm25": True, "use_reranker": True, "use_multi_query": False},
    "D": {"label": "Hybrid + Reranker + Multi-Query", "use_bm25": True, "use_reranker": True, "use_multi_query": True},
}

N_REVERSE_QUESTIONS = 3

FAITHFULNESS_PROMPT = """Bạn là người đánh giá độc lập. Nhiệm vụ: tách CÂU TRẢ LỜI dưới đây thành các \
phát biểu (claim) độc lập, rồi với mỗi claim, xác định claim đó CÓ hay KHÔNG thể suy ra từ NGỮ CẢNH.

NGỮ CẢNH:
{context}

CÂU TRẢ LỜI:
{answer}

Trả về đúng định dạng JSON, không giải thích gì thêm, theo mẫu:
{{"claims": [{{"text": "...", "supported": true}}, {{"text": "...", "supported": false}}]}}"""

REVERSE_QUESTION_PROMPT = """Dựa vào CÂU TRẢ LỜI dưới đây, hãy sinh ra {n} câu hỏi khác nhau mà câu trả lời \
này có thể là lời giải đáp phù hợp nhất. Mỗi câu hỏi trên một dòng, không đánh số, không giải thích gì thêm.

CÂU TRẢ LỜI:
{answer}

{n} câu hỏi:"""


def guard_cwd() -> None:
    if not Path("backend").is_dir():
        print("ERROR: run this from the project root.", file=sys.stderr)
        sys.exit(2)


def load_questions() -> list[dict]:
    with QUESTIONS_CSV.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def cosine(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))  # embeddings are already normalized


def extract_json(text: str) -> dict:
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip())
    return json.loads(text)


def score_faithfulness(answer: str, context: str) -> tuple[float | None, int, int]:
    if not answer.strip() or answer.strip() == INSUFFICIENT_INFORMATION_ANSWER:
        return None, 0, 0
    prompt = FAITHFULNESS_PROMPT.format(context=context, answer=answer)
    try:
        parsed = extract_json(generate_answer(prompt))
        claims = parsed.get("claims", [])
    except Exception as exc:
        print(f"[WARN] Faithfulness judge failed: {exc}")
        return None, 0, 0
    if not claims:
        return None, 0, 0
    supported = sum(1 for c in claims if c.get("supported"))
    return supported / len(claims), supported, len(claims)


def score_answer_relevancy(question: str, answer: str, n: int = N_REVERSE_QUESTIONS) -> float | None:
    if not answer.strip() or answer.strip() == INSUFFICIENT_INFORMATION_ANSWER:
        return None
    prompt = REVERSE_QUESTION_PROMPT.format(answer=answer, n=n)
    try:
        raw = generate_answer(prompt)
    except Exception as exc:
        print(f"[WARN] Answer Relevancy judge failed: {exc}")
        return None
    reverse_questions = [line.strip("-•* ").strip() for line in raw.strip().splitlines()]
    reverse_questions = [q for q in reverse_questions if q][:n]
    if not reverse_questions:
        return None

    q_emb = embed_text(question)
    sims = [cosine(q_emb, embed_text(rq)) for rq in reverse_questions]
    return sum(sims) / len(sims)


def main() -> None:
    guard_cwd()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--course-id", type=int, default=1)
    parser.add_argument("--config", default="D", choices=list(CONFIGS.keys()))
    parser.add_argument("--limit", type=int, default=None, help="only evaluate the first N questions (cost control)")
    parser.add_argument("--out-dir", default=str(OUT_DIR))
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    cfg = CONFIGS[args.config]

    questions = load_questions()
    questions = [q for q in questions if int(q["course_id"]) == args.course_id]
    if args.limit:
        questions = questions[: args.limit]

    rows = []
    for i, q in enumerate(questions, start=1):
        print(f"[{i}/{len(questions)}] {q['question']}")
        chunks = retrieve_ranked(
            q["question"],
            course_id=args.course_id,
            top_k=3,
            use_bm25=cfg["use_bm25"],
            use_reranker=cfg["use_reranker"],
            use_multi_query=cfg["use_multi_query"],
        )
        if not chunks:
            answer, context = INSUFFICIENT_INFORMATION_ANSWER, ""
        else:
            context = format_context(chunks)
            try:
                answer = generate_answer(build_rag_prompt(question=q["question"], context=context))
            except Exception as exc:
                print(f"[WARN] generate_answer failed for question_id={q['id']}: {exc}")
                answer = ""

        faithfulness, n_supported, n_claims = score_faithfulness(answer, context)
        relevancy = score_answer_relevancy(q["question"], answer)

        rows.append(
            {
                "question_id": q["id"],
                "question": q["question"],
                "topic": q["topic"],
                "answer": answer,
                "n_claims": n_claims,
                "n_claims_supported": n_supported,
                "faithfulness": faithfulness,
                "answer_relevancy": relevancy,
            }
        )

    scored_faith = [r["faithfulness"] for r in rows if r["faithfulness"] is not None]
    scored_rel = [r["answer_relevancy"] for r in rows if r["answer_relevancy"] is not None]
    n_insufficient = sum(1 for r in rows if r["faithfulness"] is None and r["answer_relevancy"] is None)

    summary = {
        "config": args.config,
        "label": cfg["label"],
        "n_questions": len(rows),
        "n_insufficient_info_answers": n_insufficient,
        "faithfulness_mean": (sum(scored_faith) / len(scored_faith)) if scored_faith else None,
        "answer_relevancy_mean": (sum(scored_rel) / len(scored_rel)) if scored_rel else None,
        "n_scored_faithfulness": len(scored_faith),
        "n_scored_relevancy": len(scored_rel),
    }

    per_query_csv = out_dir / "generation_eval_per_query.csv"
    with per_query_csv.open("w", encoding="utf-8", newline="") as f:
        fieldnames = list(rows[0].keys()) if rows else []
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    summary_json = out_dir / "generation_eval_summary.json"
    with summary_json.open("w", encoding="utf-8") as f:
        json.dump({"summary": summary, "per_query": rows}, f, ensure_ascii=False, indent=2)

    faith_line = (
        f"| Faithfulness (trung thực với ngữ cảnh) | {summary['faithfulness_mean']:.3f} "
        f"(n={summary['n_scored_faithfulness']}) |"
        if summary["faithfulness_mean"] is not None
        else "| Faithfulness (trung thực với ngữ cảnh) | N/A |"
    )
    rel_line = (
        f"| Answer Relevancy (đúng trọng tâm câu hỏi) | {summary['answer_relevancy_mean']:.3f} "
        f"(n={summary['n_scored_relevancy']}) |"
        if summary["answer_relevancy_mean"] is not None
        else "| Answer Relevancy (đúng trọng tâm câu hỏi) | N/A |"
    )
    lines = [
        f"## Đánh giá chất lượng sinh câu trả lời — Config {args.config} ({summary['label']})",
        "",
        "| Chỉ số | Giá trị |",
        "|---|---|",
        faith_line,
        rel_line,
        f"| Số câu trả lời 'không đủ thông tin' | {n_insufficient}/{len(rows)} |",
    ]
    table_md = out_dir / "generation_eval_table.md"
    table_md.write_text("\n".join(lines), encoding="utf-8")

    print("\n" + "\n".join(lines))
    print(f"\nWrote:\n  {per_query_csv}\n  {summary_json}\n  {table_md}")


if __name__ == "__main__":
    main()
