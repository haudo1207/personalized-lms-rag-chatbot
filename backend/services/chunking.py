DEFAULT_CHUNK_SIZE = 700
DEFAULT_OVERLAP = 100


def split_text_with_overlap(
    text: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    overlap: int = DEFAULT_OVERLAP,
) -> list[str]:
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("overlap must be non-negative and smaller than chunk_size")

    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(text):
            break
        start = end - overlap
    return chunks


def create_chunks(
    document_id: int,
    course_id: int,
    document_name: str,
    pages: list[dict[str, str | int]],
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    overlap: int = DEFAULT_OVERLAP,
) -> list[dict[str, str | int]]:
    all_chunks: list[dict[str, str | int]] = []

    for page in pages:
        page_number = int(page["page"])
        page_text = str(page["text"])
        page_chunks = split_text_with_overlap(
            page_text,
            chunk_size=chunk_size,
            overlap=overlap,
        )

        for index, chunk_text in enumerate(page_chunks):
            chunk_id = f"course{course_id}_doc{document_id}_p{page_number}_c{index}"
            all_chunks.append(
                {
                    "chunk_id": chunk_id,
                    "course_id": course_id,
                    "document_id": document_id,
                    "document_name": document_name,
                    "page": page_number,
                    "chunk_index": index,
                    "text": chunk_text,
                }
            )

    return all_chunks


def chunk_text(
    text: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    overlap: int = DEFAULT_OVERLAP,
) -> list[str]:
    return split_text_with_overlap(text, chunk_size=chunk_size, overlap=overlap)
