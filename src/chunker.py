"""
chunker.py — Buffer-aware paragraph chunking engine for the Bilingual Translator CLI.

Implements the "Atomic Buffer-Aware Splitter" described in the design doc:
  • Groups paragraphs into chunks whose total character count stays ≤ char_limit.
  • Never splits a paragraph across two chunks.
  • If a single paragraph exceeds the limit it gets its own dedicated chunk.

Usage
-----
    from chunker import build_chunks
    chunks = build_chunks(paragraphs, char_limit=5000)
"""

from typing import List

from src.models import Paragraph, Chunk


def build_chunks(
    paragraphs: List[Paragraph],
    char_limit: int = 5_000,
) -> List[Chunk]:
    """Divide *paragraphs* into chunks that respect *char_limit*.

    Args:
        paragraphs: Ordered list of Paragraph objects (typically from a parser).
        char_limit: Maximum number of characters allowed per chunk (default 5 000).

    Returns:
        List of Chunk objects, each with a sequential 1-based ``id``.
    """
    if not paragraphs:
        return []

    chunks: List[Chunk] = []
    current_paragraphs: List[Paragraph] = []
    current_char_count = 0
    chunk_id = 1

    def _flush() -> None:
        nonlocal chunk_id, current_char_count
        if current_paragraphs:
            chunks.append(Chunk(id=chunk_id, paragraphs=list(current_paragraphs)))
            chunk_id += 1
            current_paragraphs.clear()
            current_char_count = 0

    for para in paragraphs:
        para_len = len(para.text)

        # If adding this paragraph would exceed the limit, close the current chunk first
        if current_paragraphs and (current_char_count + para_len) > char_limit:
            _flush()

        current_paragraphs.append(para)
        current_char_count += para_len

        # Edge case: a single paragraph that is itself larger than the limit —
        # flush it immediately so it forms its own dedicated chunk.
        if current_char_count >= char_limit:
            _flush()

    # Flush any remaining paragraphs
    _flush()

    print(
        f"[chunker] {len(paragraphs)} paragraphs → "
        f"{len(chunks)} chunks (limit={char_limit:,} chars)."
    )
    return chunks
