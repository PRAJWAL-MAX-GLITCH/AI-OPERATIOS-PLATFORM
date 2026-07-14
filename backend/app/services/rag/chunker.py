"""
Chunking Engine
===============
Splits cleaned text into overlapping chunks for embedding.
Supports: recursive, fixed-size, sentence, paragraph, token-estimate modes.
"""
from __future__ import annotations
import re
from dataclasses import dataclass, field
from typing import Literal
import structlog

logger = structlog.get_logger(__name__)

ChunkStrategy = Literal["recursive", "fixed", "sentence", "paragraph", "token"]


@dataclass
class Chunk:
    text:         str
    chunk_index:  int
    char_start:   int
    char_end:     int
    page_number:  int | None = None
    token_estimate: int = field(init=False)
    metadata:     dict = field(default_factory=dict)

    def __post_init__(self):
        # Rough token estimate: 1 token ≈ 4 chars
        self.token_estimate = max(1, len(self.text) // 4)


class ChunkingEngine:

    def __init__(
        self,
        chunk_size: int = 512,
        chunk_overlap: int = 64,
        strategy: ChunkStrategy = "recursive",
    ):
        self.chunk_size    = chunk_size
        self.chunk_overlap = chunk_overlap
        self.strategy      = strategy

    def chunk(self, text: str, doc_metadata: dict | None = None) -> list[Chunk]:
        if self.strategy == "recursive":
            chunks = self._recursive_split(text)
        elif self.strategy == "fixed":
            chunks = self._fixed_split(text)
        elif self.strategy == "sentence":
            chunks = self._sentence_split(text)
        elif self.strategy == "paragraph":
            chunks = self._paragraph_split(text)
        elif self.strategy == "token":
            chunks = self._token_split(text)
        else:
            chunks = self._recursive_split(text)

        logger.info("chunking_complete", strategy=self.strategy, n_chunks=len(chunks), doc_chars=len(text))
        return chunks

    # ------------------------------------------------------------------
    # Strategies
    # ------------------------------------------------------------------

    def _recursive_split(self, text: str) -> list[Chunk]:
        """Split on paragraphs → sentences → characters, maintaining chunk_size."""
        separators = ["\n\n", "\n", ". ", "! ", "? ", " ", ""]
        return self._split_with_separators(text, separators)

    def _fixed_split(self, text: str) -> list[Chunk]:
        """Naive character-based fixed-size split."""
        pieces, start = [], 0
        idx = 0
        while start < len(text):
            end = min(start + self.chunk_size, len(text))
            pieces.append(Chunk(
                text=text[start:end],
                chunk_index=idx,
                char_start=start,
                char_end=end,
            ))
            start = max(start + 1, end - self.chunk_overlap)
            idx += 1
        return pieces

    def _sentence_split(self, text: str) -> list[Chunk]:
        """Split on sentence boundaries, then group into chunk_size windows."""
        sentences = re.split(r"(?<=[.!?])\s+", text)
        return self._group_into_chunks(sentences, text)

    def _paragraph_split(self, text: str) -> list[Chunk]:
        """Split on blank lines, group into chunk_size windows."""
        paragraphs = [p.strip() for p in re.split(r"\n{2,}", text) if p.strip()]
        return self._group_into_chunks(paragraphs, text)

    def _token_split(self, text: str) -> list[Chunk]:
        """Token-estimate based split (1 token ≈ 4 chars)."""
        char_size = self.chunk_size * 4
        overlap   = self.chunk_overlap * 4
        pieces, start, idx = [], 0, 0
        while start < len(text):
            end = min(start + char_size, len(text))
            pieces.append(Chunk(
                text=text[start:end],
                chunk_index=idx,
                char_start=start,
                char_end=end,
            ))
            start = max(start + 1, end - overlap)
            idx += 1
        return pieces

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _group_into_chunks(self, units: list[str], original_text: str) -> list[Chunk]:
        """Groups sentence/paragraph units into chunks of up to chunk_size chars."""
        chunks, buffer, buf_start, cursor, idx = [], [], 0, 0, 0
        for unit in units:
            if len(" ".join(buffer + [unit])) > self.chunk_size and buffer:
                chunk_text = " ".join(buffer)
                chunks.append(Chunk(
                    text=chunk_text,
                    chunk_index=idx,
                    char_start=buf_start,
                    char_end=buf_start + len(chunk_text),
                ))
                idx += 1
                # Overlap: keep last unit
                buffer = buffer[-1:] + [unit] if self.chunk_overlap > 0 else [unit]
                buf_start = cursor
            else:
                if not buffer:
                    buf_start = cursor
                buffer.append(unit)
            cursor += len(unit) + 1

        if buffer:
            chunk_text = " ".join(buffer)
            chunks.append(Chunk(
                text=chunk_text,
                chunk_index=idx,
                char_start=buf_start,
                char_end=buf_start + len(chunk_text),
            ))
        return chunks

    def _split_with_separators(self, text: str, separators: list[str]) -> list[Chunk]:
        """Recursively tries separators to produce chunks ≤ chunk_size."""
        if not text:
            return []

        sep = separators[0]
        if sep:
            splits = text.split(sep)
        else:
            splits = list(text)

        chunks, buffer, idx = [], "", 0
        result: list[Chunk] = []

        for split in splits:
            candidate = buffer + (sep if buffer else "") + split
            if len(candidate) <= self.chunk_size:
                buffer = candidate
            else:
                if buffer:
                    result.append(Chunk(
                        text=buffer.strip(),
                        chunk_index=idx,
                        char_start=text.find(buffer),
                        char_end=text.find(buffer) + len(buffer),
                    ))
                    idx += 1

                if len(split) > self.chunk_size and len(separators) > 1:
                    sub = self._split_with_separators(split, separators[1:])
                    for s in sub:
                        s.chunk_index = idx
                        idx += 1
                        result.append(s)
                    buffer = ""
                else:
                    buffer = split

        if buffer:
            result.append(Chunk(
                text=buffer.strip(),
                chunk_index=idx,
                char_start=text.rfind(buffer),
                char_end=len(text),
            ))

        return [c for c in result if c.text.strip()]
