"""
Text Cleaning Pipeline
======================
Removes noise, broken encoding, excessive whitespace, and repeated lines.
"""
from __future__ import annotations
import re
import unicodedata


def clean_text(text: str) -> str:
    """
    Full cleaning pipeline applied to raw extracted text.
    """
    # 1. Normalize unicode
    text = unicodedata.normalize("NFKD", text)

    # 2. Remove null bytes and other control chars (keep newlines and tabs)
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)

    # 3. Normalize line endings
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # 4. Collapse excessive blank lines (>2 → 2)
    text = re.sub(r"\n{3,}", "\n\n", text)

    # 5. Strip trailing whitespace on each line
    text = "\n".join(line.rstrip() for line in text.split("\n"))

    # 6. Remove very short lines that are likely headers/footers/page numbers
    lines = text.split("\n")
    cleaned_lines = [
        line for line in lines
        if len(line.strip()) > 3 or line.strip() == ""
    ]
    text = "\n".join(cleaned_lines)

    # 7. Collapse multiple spaces within a line
    text = re.sub(r"[ \t]{2,}", " ", text)

    # 8. Strip leading/trailing whitespace overall
    return text.strip()
