"""
RAG Document Loaders — Factory Pattern
=======================================
Each loader handles one file type independently.
Adding a new format = add a new loader class + register it.
No existing code needs to change.
"""
from __future__ import annotations
import re
from pathlib import Path
from typing import Protocol, runtime_checkable
import structlog

logger = structlog.get_logger(__name__)


@runtime_checkable
class DocumentLoader(Protocol):
    """Interface every loader must implement."""
    def load(self, path: str) -> tuple[str, dict]:
        """Returns (raw_text, metadata)."""
        ...


# ---------------------------------------------------------------------------
# Individual Loaders
# ---------------------------------------------------------------------------

class TxtLoader:
    def load(self, path: str) -> tuple[str, dict]:
        p = Path(path)
        text = p.read_text(encoding="utf-8", errors="replace")
        return text, {"source": str(p), "file_type": "txt"}


class MarkdownLoader:
    def load(self, path: str) -> tuple[str, dict]:
        p = Path(path)
        text = p.read_text(encoding="utf-8", errors="replace")
        # Strip Markdown syntax for cleaner text
        text = re.sub(r"#{1,6}\s*", "", text)      # headings
        text = re.sub(r"\*{1,2}([^*]+)\*{1,2}", r"\1", text)  # bold/italic
        text = re.sub(r"`{1,3}[^`]*`{1,3}", "", text)         # code
        text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)  # links
        return text, {"source": str(p), "file_type": "md"}


class HtmlLoader:
    def load(self, path: str) -> tuple[str, dict]:
        from bs4 import BeautifulSoup
        p = Path(path)
        html = p.read_text(encoding="utf-8", errors="replace")
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        text = soup.get_text(separator="\n")
        return text, {"source": str(p), "file_type": "html", "title": soup.title.string if soup.title else ""}


class PdfLoader:
    def load(self, path: str) -> tuple[str, dict]:
        from pypdf import PdfReader
        reader = PdfReader(path)
        pages = []
        for i, page in enumerate(reader.pages):
            page_text = page.extract_text() or ""
            pages.append(page_text)
        text = "\n\n".join(pages)
        meta = {
            "source": path,
            "file_type": "pdf",
            "total_pages": len(reader.pages),
        }
        info = reader.metadata or {}
        meta["title"]  = info.get("/Title", "")
        meta["author"] = info.get("/Author", "")
        return text, meta


class DocxLoader:
    def load(self, path: str) -> tuple[str, dict]:
        import docx
        doc = docx.Document(path)
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        text = "\n\n".join(paragraphs)
        return text, {"source": path, "file_type": "docx"}


# ---------------------------------------------------------------------------
# Loader Factory
# ---------------------------------------------------------------------------

_REGISTRY: dict[str, type] = {
    ".txt":  TxtLoader,
    ".md":   MarkdownLoader,
    ".html": HtmlLoader,
    ".htm":  HtmlLoader,
    ".pdf":  PdfLoader,
    ".docx": DocxLoader,
}


def register_loader(extension: str, loader_class: type) -> None:
    """Register a new loader without modifying existing code."""
    _REGISTRY[extension.lower()] = loader_class


def load_document(path: str) -> tuple[str, dict]:
    """
    Auto-selects the correct loader based on file extension.
    Returns (raw_text, metadata).
    """
    ext = Path(path).suffix.lower()
    loader_cls = _REGISTRY.get(ext)
    if not loader_cls:
        raise ValueError(f"No loader registered for extension '{ext}'. Supported: {list(_REGISTRY)}")
    loader = loader_cls()
    text, meta = loader.load(path)
    meta["file_size_bytes"] = Path(path).stat().st_size
    logger.info("document_loaded", path=path, ext=ext, chars=len(text))
    return text, meta


def supported_extensions() -> list[str]:
    return list(_REGISTRY.keys())
