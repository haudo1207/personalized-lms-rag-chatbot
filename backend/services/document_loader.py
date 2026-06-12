from pathlib import Path

import fitz
from docx import Document


PageText = dict[str, str | int]


def load_pdf(file_path: str) -> list[PageText]:
    pages: list[PageText] = []
    with fitz.open(file_path) as pdf:
        for page_index, page in enumerate(pdf):
            pages.append(
                {
                    "page": page_index + 1,
                    "text": page.get_text(),
                }
            )
    return pages


def load_docx(file_path: str) -> list[PageText]:
    doc = Document(file_path)
    text = "\n".join(paragraph.text for paragraph in doc.paragraphs)
    return [{"page": 1, "text": text}]


def load_txt(file_path: str) -> list[PageText]:
    with open(file_path, encoding="utf-8") as file:
        text = file.read()
    return [{"page": 1, "text": text}]


def load_document(file_path: str) -> list[PageText]:
    suffix = Path(file_path).suffix.lower()

    if suffix == ".pdf":
        return load_pdf(file_path)
    if suffix == ".docx":
        return load_docx(file_path)
    if suffix == ".txt":
        return load_txt(file_path)

    raise ValueError(f"Unsupported file type: {suffix or 'unknown'}")
