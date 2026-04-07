"""
rule_injector.py — Terminology rule scanner and prompt builder for the Bilingual Translator CLI.

Phase 3 responsibilities:
  • Scan each chunk's text for dictionary terms that appear in it.
  • Inject matching terms as a [Terminology Rules] block into the prompt template.
  • Write the final prompt string to chunks/<id>.txt so the user can copy-paste it.

The prompt template is read from the project's config.yaml (via the Config class)
and must contain two placeholders:
    {rules_block}   — replaced with matched terminology lines (or empty)
    {source_block}  — replaced with indexed paragraph lines [1] text …
"""

import re
from pathlib import Path
from typing import Dict, List

from src.models import Chunk, Paragraph
from src.config import Config


# ──────────────────────────────────────────────────────────────────────────── #
# Term scanner                                                                 #
# ──────────────────────────────────────────────────────────────────────────── #


def _scan_rules(chunk: Chunk, dictionary: Dict[str, str]) -> Dict[str, str]:
    """Return the subset of *dictionary* whose keys appear in *chunk*'s text.

    Matching is case-insensitive and whole-word-boundary aware.
    """
    if not dictionary:
        return {}

    combined_text = " ".join(p.text for p in chunk.paragraphs)
    matched: Dict[str, str] = {}
    for term, translation in dictionary.items():
        pattern = re.compile(r"\b" + re.escape(term) + r"\b", re.IGNORECASE)
        if pattern.search(combined_text):
            matched[term] = translation
    return matched


# ──────────────────────────────────────────────────────────────────────────── #
# Prompt builder                                                               #
# ──────────────────────────────────────────────────────────────────────────── #


def _build_prompt(chunk: Chunk, config: Config) -> str:
    """Render the prompt string for *chunk* using *config*'s template and dictionary."""
    # 1. Scan for relevant terminology rules
    rules = _scan_rules(chunk, config.dictionary)
    chunk.rules = rules  # persist onto the chunk for later use

    # 2. Build the [Terminology Rules] block (empty string if no matches)
    if rules:
        rule_lines = "\n".join(f"- {k}: {v}" for k, v in rules.items())
        rules_block = f"[Terminology Rules]\n{rule_lines}\n\n"
    else:
        rules_block = ""

    # 3. Build the indexed [Source Text] block
    source_lines = "\n".join(f"[{p.index}] {p.text}" for p in chunk.paragraphs)

    # 4. Fill in the template
    prompt = config.prompt_template.format(
        rules_block=rules_block,
        source_block=source_lines,
    )
    return prompt


# ──────────────────────────────────────────────────────────────────────────── #
# Public: write chunk files                                                    #
# ──────────────────────────────────────────────────────────────────────────── #


def write_chunk_files(
    chunks: List[Chunk],
    config: Config,
    chunks_dir: Path,
) -> None:
    """Generate one .txt prompt file per chunk inside *chunks_dir*.

    Each file is named with zero-padded chunk IDs (e.g. 001.txt, 002.txt).

    Args:
        chunks: List of Chunk objects returned by the chunker.
        config: Loaded project Config with prompt_template and dictionary.
        chunks_dir: Directory where .txt files will be written (created if absent).
    """
    chunks_dir = Path(chunks_dir)
    chunks_dir.mkdir(parents=True, exist_ok=True)

    pad = len(str(len(chunks)))  # pad width based on total chunk count

    for chunk in chunks:
        prompt = _build_prompt(chunk, config)
        filename = chunks_dir / f"{str(chunk.id).zfill(pad)}.txt"
        filename.write_text(prompt, encoding="utf-8")

    print(f"[injector] Wrote {len(chunks)} chunk file(s) to '{chunks_dir}'.")
