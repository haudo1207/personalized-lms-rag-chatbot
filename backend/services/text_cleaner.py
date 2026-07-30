import re

# Table-of-contents dot-leader lines (e.g. "Định nghĩa...........9") carry no
# information but get embedded/indexed like real content -- 5+ consecutive dots
# is specific enough to normal prose that false positives are effectively zero.
TOC_DOT_LEADER_RE = re.compile(r"^.*\.{5,}.*$", re.MULTILINE)

# Document-sharing site watermark lines (e.g. "Downloaded by ... (email)" /
# "lOMoARcPSD|39992437") injected into the PDF text layer -- present on ~30% of
# chunks in the real corpus used for this project, pure noise, no informational value.
WATERMARK_LINE_RE = re.compile(r"^.*(Downloaded by|lOMoARcPSD).*$", re.MULTILINE)


def clean_text(text: str) -> str:
    text = text.replace("\x00", " ")
    text = TOC_DOT_LEADER_RE.sub("", text)
    text = WATERMARK_LINE_RE.sub("", text)
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
