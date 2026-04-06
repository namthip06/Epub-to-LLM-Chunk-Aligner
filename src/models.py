"""
models.py — Core data models for the Bilingual Book Translator CLI.

Defines the `Paragraph` and `Chunk` dataclasses that flow through every
stage of the pipeline: parsing → chunking → prompt injection → assembly.
"""

from dataclasses import dataclass, field
from typing import List, Dict


@dataclass
class Paragraph:
    """A single paragraph extracted from the source document.

    Attributes:
        index: Global sequential index (1-based) across the entire book.
        text: Raw text content of the paragraph.
        chapter: Chapter title or identifier this paragraph belongs to.
    """
    index: int
    text: str
    chapter: str = ""


@dataclass
class Chunk:
    """A group of consecutive paragraphs that fit within the character limit.

    Attributes:
        id: Sequential chunk number (1-based), used as the output filename stem.
        paragraphs: Ordered list of Paragraph objects in this chunk.
        rules: Terminology dictionary entries that appear in this chunk
               (key = source term, value = preferred translation).
    """
    id: int
    paragraphs: List[Paragraph] = field(default_factory=list)
    rules: Dict[str, str] = field(default_factory=dict)

    # ------------------------------------------------------------------ #
    # Convenience helpers                                                  #
    # ------------------------------------------------------------------ #

    @property
    def char_count(self) -> int:
        """Total character length of all paragraph texts in this chunk."""
        return sum(len(p.text) for p in self.paragraphs)

    @property
    def paragraph_count(self) -> int:
        return len(self.paragraphs)
