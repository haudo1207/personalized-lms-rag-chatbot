import re


def clean_text(text: str) -> str:
    text = text.replace("\x00", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def clean_pages(pages: list[dict[str, str | int]]) -> list[dict[str, str | int]]:
    cleaned_pages: list[dict[str, str | int]] = []
    for page in pages:
        cleaned_pages.append(
            {
                "page": page["page"],
                "text": clean_text(str(page["text"])),
            }
        )
    return cleaned_pages
