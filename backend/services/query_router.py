import re

# Cheap, zero-LLM gate for Query Decomposition -- "on-demand" only pays off if this
# check itself doesn't cost an LLM round-trip (decompose_query's own prompt already
# no-ops on simple questions, but still costs ~3.5s of Gemini latency every time it's
# called; that unconditional call is exactly why Config E was slow for every question,
# not just the comparison ones).
#
# Validated against the current 50-question eval set: only question_id 3 ("INNER JOIN
# khac LEFT JOIN nhu the nao?") and 15 ("RIGHT JOIN khac LEFT JOIN o diem nao?") trigger,
# matching the two genuinely comparison-style questions in that set. Two lessons baked in:
#   - question_id 36 ("... mot phu toi thieu KHAC nhan duoc la gi?") uses "khac" to mean
#     "another/different [X]", not "differs from" -- a bare "khac" substring is NOT enough.
#   - question_id 30 ("... duoc PHAN BIET dua tren co so nao?") uses "phan biet" but is a
#     single-concept question (asking about specialization basis), not a genuine A-vs-B
#     comparison -- bare "phan biet" is NOT enough either, it needs a following "voi".
_STRONG_PHRASES = (
    "so sánh",
    "khác nhau",
    "khác gì",
    "khác biệt",
    "giống nhau và khác nhau",
    "ưu và nhược",
    "ưu nhược điểm",
)
_PHAN_BIET_VOI_RE = re.compile(r"phân biệt\b.*\bvới\b", re.IGNORECASE)
# "X khac Y <cau hoi so sanh>" -- requires "khac" to be followed eventually by a
# comparison-style question tail, not just any "khac" (see question_id 36 above).
_KHAC_COMPARISON_RE = re.compile(r"khác\s+.*\b(như thế nào|ở điểm nào|ra sao)\b", re.IGNORECASE)


def is_complex_question(question: str) -> bool:
    """Heuristic (no LLM call) for whether a question is comparison/multi-part and
    would benefit from Query Decomposition, vs. a single-concept question that's
    better served by plain retrieval. Deliberately conservative -- false negatives
    just fall back to normal RAG (no harm), false positives cost one extra Gemini
    call (~3.5s), so precision matters more than recall here."""
    text = question.lower()
    if any(phrase in text for phrase in _STRONG_PHRASES):
        return True
    if _PHAN_BIET_VOI_RE.search(text):
        return True
    if _KHAC_COMPARISON_RE.search(text):
        return True
    return False
