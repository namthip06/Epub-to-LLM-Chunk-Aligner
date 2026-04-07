"""
assembler.py — Translation alignment, validation, and bilingual ePub builder.

Phase 4 responsibilities:
  1. Parse translated .txt files from /translated, extracting [n]-indexed paragraphs.
  2. Validate that translated index count matches the corresponding chunk file.
  3. Strip [n] index markers from both English and Thai content.
  4. Merge English + Thai paragraph pairs into bilingual HTML.
  5. Build a full bilingual ePub (with chapter structure / ToC) via EbookLib.

Entry point:
    assemble_project(project_dir: Path) -> None
"""

import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple

# ──────────────────────────────────────────────────────────────────────────── #
# Regex helpers                                                                #
# ──────────────────────────────────────────────────────────────────────────── #

_INDEX_RE = re.compile(r"^\[(\d+)\]\s*(.+)", re.MULTILINE)


def _extract_indexed_paragraphs(text: str) -> Dict[int, str]:
    """Return a dict mapping index → paragraph text extracted from *text*.

    Matches lines starting with [n] where n is an integer.
    """
    result: Dict[int, str] = {}
    for match in _INDEX_RE.finditer(text):
        idx = int(match.group(1))
        content = match.group(2).strip()
        result[idx] = content
    return result


# ──────────────────────────────────────────────────────────────────────────── #
# Alignment validator                                                          #
# ──────────────────────────────────────────────────────────────────────────── #

def _validate_alignment(
    chunk_indices: List[int],
    translated_indices: List[int],
    filename: str,
) -> None:
    """Raise a ValueError with a clear report if indices don't match.

    Args:
        chunk_indices: List of expected paragraph indices from the source chunk file.
        translated_indices: List of paragraph indices found in the translated file.
        filename: Stem name used in the error message (e.g. "001").

    Raises:
        ValueError: With a human-readable diff of missing / extra indices.
    """
    expected = set(chunk_indices)
    found = set(translated_indices)

    missing = sorted(expected - found)
    extra = sorted(found - expected)

    if missing or extra:
        msg_parts = [f"[validate] Alignment error in '{filename}':"]
        if missing:
            msg_parts.append(f"  Missing indices in translation: {missing}")
        if extra:
            msg_parts.append(f"  Extra (unexpected) indices in translation: {extra}")
        raise ValueError("\n".join(msg_parts))


# ──────────────────────────────────────────────────────────────────────────── #
# Bilingual paragraph merger                                                   #
# ──────────────────────────────────────────────────────────────────────────── #

def _merge_pairs(
    source_paras: Dict[int, str],
    translated_paras: Dict[int, str],
) -> List[Tuple[str, str]]:
    """Return ordered list of (english, thai) tuples sorted by index."""
    ordered = []
    for idx in sorted(source_paras.keys()):
        eng = source_paras[idx]
        tha = translated_paras.get(idx, "")
        ordered.append((eng, tha))
    return ordered


def _pairs_to_html(pairs: List[Tuple[str, str]], chapter: str) -> str:
    """Convert a list of (english, thai) pairs into a styled HTML section."""
    lines = [f"<h2>{chapter}</h2>"]
    for eng, tha in pairs:
        lines.append(
            f'<div class="bilingual-pair">'
            f'<p class="en">{eng}</p>'
            f'<p class="th">{tha}</p>'
            f"</div>"
        )
    return "\n".join(lines)


# ──────────────────────────────────────────────────────────────────────────── #
# ePub builder                                                                 #
# ──────────────────────────────────────────────────────────────────────────── #

_EPUB_CSS = """\
body { font-family: serif; font-size: 1em; line-height: 1.6; margin: 1em 2em; }
h2   { font-size: 1.3em; border-bottom: 1px solid #ccc; margin-top: 2em; }
.bilingual-pair { margin-bottom: 1.2em; }
.en  { color: #222; }
.th  { color: #444; font-style: italic; margin-top: 0.3em; }
"""


def _build_epub(
    chapter_htmls: List[Tuple[str, str]],
    output_path: Path,
) -> None:
    """Assemble chapter HTML sections into a bilingual ePub file.

    Args:
        chapter_htmls: List of (chapter_title, html_body) tuples in order.
        output_path: Destination .epub file path.
    """
    try:
        from ebooklib import epub
    except ImportError:
        sys.exit("EbookLib is required to build ePub. Install: pip install ebooklib")

    book = epub.EpubBook()
    book.set_title("Bilingual Translation")
    book.set_language("en")

    # Add CSS
    css_item = epub.EpubItem(
        uid="style",
        file_name="style/main.css",
        media_type="text/css",
        content=_EPUB_CSS,
    )
    book.add_item(css_item)

    spine = ["nav"]
    toc = []

    for i, (chapter_title, html_body) in enumerate(chapter_htmls, start=1):
        chapter_id = f"chapter_{i:03d}"
        chapter = epub.EpubHtml(
            title=chapter_title,
            file_name=f"{chapter_id}.xhtml",
            lang="en",
        )
        content_str = (
            f"<?xml version='1.0' encoding='utf-8'?>\n"
            f"<html xmlns='http://www.w3.org/1999/xhtml'>\n"
            f"<head><link rel='stylesheet' href='style/main.css'/></head>\n"
            f"<body>\n{html_body}\n</body>\n</html>"
        )
        chapter.content = content_str.encode('utf-8')
        chapter.add_item(css_item)
        book.add_item(chapter)
        spine.append(chapter)
        toc.append(epub.Link(f"{chapter_id}.xhtml", chapter_title, chapter_id))

    book.toc = toc
    book.spine = spine
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())

    epub.write_epub(str(output_path), book)
    print(f"[assembler] ePub saved → '{output_path}'")


# ──────────────────────────────────────────────────────────────────────────── #
# Public entry point                                                           #
# ──────────────────────────────────────────────────────────────────────────── #

def assemble_project(project_dir: Path) -> None:
    """Read all matching chunks + translated files and produce a bilingual ePub.

    Expected layout inside *project_dir*:
        chunks/         source .txt files (e.g. 001.txt, 002.txt …)
        translated/     translated .txt files with matching filenames
        output/         destination directory for the final .epub

    Args:
        project_dir: Root of the book project.
    """
    project_dir = Path(project_dir)
    chunks_dir = project_dir / "chunks"
    translated_dir = project_dir / "translated"
    output_dir = project_dir / "output"
    output_dir.mkdir(parents=True, exist_ok=True)

    chunk_files = sorted(chunks_dir.glob("*.txt"))
    if not chunk_files:
        sys.exit(f"[assembler] No chunk files found in '{chunks_dir}'.")

    chapter_htmls: List[Tuple[str, str]] = []
    total_pairs = 0

    for chunk_file in chunk_files:
        stem = chunk_file.stem
        translated_file = translated_dir / chunk_file.name

        if not translated_file.exists():
            print(
                f"[assembler] WARNING: No translated file for '{stem}' — skipping."
            )
            continue

        source_text = chunk_file.read_text(encoding="utf-8")
        translated_text = translated_file.read_text(encoding="utf-8")

        source_paras = _extract_indexed_paragraphs(source_text)
        translated_paras = _extract_indexed_paragraphs(translated_text)

        # Validate alignment
        _validate_alignment(
            list(source_paras.keys()),
            list(translated_paras.keys()),
            stem,
        )

        pairs = _merge_pairs(source_paras, translated_paras)
        chapter_title = f"Section {stem}"
        html_body = _pairs_to_html(pairs, chapter_title)
        chapter_htmls.append((chapter_title, html_body))
        total_pairs += len(pairs)

    if not chapter_htmls:
        sys.exit("[assembler] Nothing to assemble. Add translated files and retry.")

    output_path = output_dir / "bilingual.epub"
    _build_epub(chapter_htmls, output_path)

    print(
        f"[assembler] Done! {total_pairs} bilingual paragraph pairs assembled "
        f"across {len(chapter_htmls)} section(s)."
    )
