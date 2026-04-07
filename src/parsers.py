"""
parsers.py — Source-file parsers for the Bilingual Book Translator CLI.

Supports three input formats:
  • ePub  — via EbookLib + BeautifulSoup4
  • PDF   — via PyPDF2
  • Markdown — stdlib only

Each parser exposes a single public function:
    parse(file_path: Path) -> List[Paragraph]

Paragraphs are returned in reading order with a global sequential index
starting at 1. Chapter/section metadata is preserved where the format allows.
"""

import re
import sys
from pathlib import Path
from typing import List

from src.models import Paragraph

# ──────────────────────────────────────────────────────────────────────────── #
# Optional dependency guards — we import lazily so the tool still works for   #
# file types whose library is not installed.                                   #
# ──────────────────────────────────────────────────────────────────────────── #


def _require(package: str, install_hint: str) -> None:
    """Abort with a helpful message if *package* is missing."""
    import importlib.util

    if importlib.util.find_spec(package) is None:
        sys.exit(f"Missing dependency '{package}'. Install with: {install_hint}")


# ──────────────────────────────────────────────────────────────────────────── #
# ePub parser                                                                  #
# ──────────────────────────────────────────────────────────────────────────── #


def _parse_epub(file_path: Path) -> List[Paragraph]:
    """Extract paragraphs from an ePub file, preserving chapter names."""
    _require("ebooklib", "pip install ebooklib")
    _require("bs4", "pip install beautifulsoup4")

    import ebooklib
    from ebooklib import epub
    from bs4 import BeautifulSoup

    book = epub.read_epub(str(file_path))
    paragraphs: List[Paragraph] = []
    global_index = 1

    for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
        soup = BeautifulSoup(item.get_content(), "html.parser")

        # Determine chapter name from the first heading in the item
        heading = soup.find(re.compile(r"^h[1-6]$"))
        chapter_name = heading.get_text(strip=True) if heading else item.get_name()

        for tag in soup.find_all(["p", "li"]):
            text = tag.get_text(separator=" ", strip=True)
            if not text:
                continue
            paragraphs.append(
                Paragraph(index=global_index, text=text, chapter=chapter_name)
            )
            global_index += 1

    return paragraphs


# ──────────────────────────────────────────────────────────────────────────── #
# PDF parser                                                                   #
# ──────────────────────────────────────────────────────────────────────────── #


def _parse_pdf(file_path: Path) -> List[Paragraph]:
    """Extract paragraphs from a PDF, treating blank-line-separated blocks as paragraphs."""
    _require("PyPDF2", "pip install PyPDF2")

    import PyPDF2

    paragraphs: List[Paragraph] = []
    global_index = 1

    with open(file_path, "rb") as fh:
        reader = PyPDF2.PdfReader(fh)
        for page_num, page in enumerate(reader.pages, start=1):
            raw = page.extract_text() or ""
            # Split on one or more blank lines to get paragraph-like blocks
            blocks = re.split(r"\n{2,}", raw)
            for block in blocks:
                text = block.replace("\n", " ").strip()
                if not text:
                    continue
                chapter = f"Page {page_num}"
                paragraphs.append(
                    Paragraph(index=global_index, text=text, chapter=chapter)
                )
                global_index += 1

    return paragraphs


# ──────────────────────────────────────────────────────────────────────────── #
# Markdown parser                                                              #
# ──────────────────────────────────────────────────────────────────────────── #


def _parse_markdown(file_path: Path) -> List[Paragraph]:
    """Extract paragraphs from a Markdown file using heading-aware splitting."""
    text = file_path.read_text(encoding="utf-8")
    lines = text.splitlines()

    paragraphs: List[Paragraph] = []
    global_index = 1
    current_chapter = "Introduction"
    buffer: List[str] = []

    def flush_buffer() -> None:
        nonlocal global_index
        joined = " ".join(buffer).strip()
        if joined:
            paragraphs.append(
                Paragraph(index=global_index, text=joined, chapter=current_chapter)
            )
            global_index += 1
        buffer.clear()

    for line in lines:
        heading_match = re.match(r"^(#{1,6})\s+(.*)", line)
        if heading_match:
            flush_buffer()
            current_chapter = heading_match.group(2).strip()
            continue

        stripped = line.strip()
        if stripped == "":
            flush_buffer()
        else:
            buffer.append(stripped)

    flush_buffer()
    return paragraphs


# ──────────────────────────────────────────────────────────────────────────── #
# Public dispatch                                                               #
# ──────────────────────────────────────────────────────────────────────────── #

_PARSERS = {
    ".epub": _parse_epub,
    ".pdf": _parse_pdf,
    ".md": _parse_markdown,
    ".markdown": _parse_markdown,
}


def parse(file_path: Path) -> List[Paragraph]:
    """Parse *file_path* into an ordered ``List[Paragraph]``.

    Args:
        file_path: Path to an ePub, PDF, or Markdown source file.

    Returns:
        List of Paragraph objects in reading order, each with a unique index.

    Raises:
        ValueError: If the file extension is not supported.
        FileNotFoundError: If the file does not exist.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"Source file not found: '{file_path}'")

    suffix = file_path.suffix.lower()
    parser_fn = _PARSERS.get(suffix)
    if parser_fn is None:
        supported = ", ".join(_PARSERS.keys())
        raise ValueError(f"Unsupported file type '{suffix}'. Supported: {supported}")

    print(f"[parser] Parsing '{file_path.name}' as {suffix.upper()} …")
    paragraphs = parser_fn(file_path)
    print(f"[parser] Found {len(paragraphs)} paragraphs.")
    return paragraphs
