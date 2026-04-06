"""
main.py — CLI entry point for the Bilingual Book Translator.

Commands
--------
  init     <project_dir>           Create project folder structure + config.yaml
  extract  <source_file> <project> Parse source file and write prompt chunks
  assemble <project_dir>           Merge translations into a bilingual ePub

Typical workflow
----------------
  1.  python main.py init     ./my-book
  2.  python main.py extract  book.epub ./my-book
  3.  (copy chunks/*.txt content into your LLM, paste output into translated/)
  4.  python main.py assemble ./my-book
"""

import argparse
import sys
from pathlib import Path

from src.config import Config
from src.parsers import parse
from src.chunker import build_chunks
from src.rule_injector import write_chunk_files
from src.assembler import assemble_project


# ──────────────────────────────────────────────────────────────────────────── #
# Subcommand handlers                                                          #
# ──────────────────────────────────────────────────────────────────────────── #


def cmd_init(args: argparse.Namespace) -> None:
    """Create the project directory layout and a starter config.yaml."""
    project_dir = Path(args.project_dir)
    for sub in ("source", "chunks", "translated", "output"):
        (project_dir / sub).mkdir(parents=True, exist_ok=True)
    Config.write_default(project_dir)
    print(f"[init] Project scaffold created at '{project_dir.resolve()}'")
    print("[init] Edit config.yaml to customise the prompt template and dictionary.")


def cmd_extract(args: argparse.Namespace) -> None:
    """Parse a source file and write prompt chunk files to <project>/chunks/."""
    source_file = Path(args.source_file)
    project_dir = Path(args.project_dir)

    if not source_file.exists():
        sys.exit(f"[extract] Source file not found: '{source_file}'")

    config = Config(project_dir)
    char_limit = args.limit

    # Phase 2: Parse → Chunk
    paragraphs = parse(source_file)
    chunks = build_chunks(paragraphs, char_limit=char_limit)

    # Phase 3: Inject rules → write .txt files
    chunks_dir = project_dir / "chunks"
    write_chunk_files(chunks, config, chunks_dir)

    print(
        f"\n✅  Done! Open '{chunks_dir}' to find your {len(chunks)} chunk file(s).\n"
        f"   Copy each file's content into your LLM, then place the translation\n"
        f"   result in: '{project_dir / 'translated'}/<same filename>'\n"
        f"   Run `assemble` when all translations are ready."
    )


def cmd_assemble(args: argparse.Namespace) -> None:
    """Validate translations and build the final bilingual ePub."""
    assemble_project(Path(args.project_dir))


# ──────────────────────────────────────────────────────────────────────────── #
# Argument parser                                                              #
# ──────────────────────────────────────────────────────────────────────────── #


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="translator",
        description="Bilingual Book Translator CLI — English ↔ Thai ePub/PDF/MD",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python main.py init     ./my-book\n"
            "  python main.py extract  book.epub ./my-book --limit 4000\n"
            "  python main.py assemble ./my-book\n"
        ),
    )
    sub = parser.add_subparsers(dest="command", metavar="<command>")
    sub.required = True

    # ── init ──────────────────────────────────────────────────────────────── #
    p_init = sub.add_parser("init", help="Initialise a new book project folder")
    p_init.add_argument("project_dir", help="Path to the project directory to create")
    p_init.set_defaults(func=cmd_init)

    # ── extract ───────────────────────────────────────────────────────────── #
    p_extract = sub.add_parser(
        "extract",
        help="Parse a source file and generate prompt chunks",
    )
    p_extract.add_argument(
        "source_file", help="Path to the source ePub / PDF / MD file"
    )
    p_extract.add_argument("project_dir", help="Path to the book project folder")
    p_extract.add_argument(
        "--limit",
        type=int,
        default=5_000,
        metavar="N",
        help="Character limit per chunk (default: 5000)",
    )
    p_extract.set_defaults(func=cmd_extract)

    # ── assemble ──────────────────────────────────────────────────────────── #
    p_assemble = sub.add_parser(
        "assemble",
        help="Merge translated files into a bilingual ePub",
    )
    p_assemble.add_argument("project_dir", help="Path to the book project folder")
    p_assemble.set_defaults(func=cmd_assemble)

    return parser


# ──────────────────────────────────────────────────────────────────────────── #
# Entry point                                                                  #
# ──────────────────────────────────────────────────────────────────────────── #


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
