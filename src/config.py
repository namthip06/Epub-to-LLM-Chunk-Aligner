"""
config.py — Configuration loader for the Bilingual Book Translator CLI.

Reads `config.yaml` from a project folder and exposes the prompt template
and the terminology dictionary so other modules can import them cleanly.

Expected config.yaml layout
----------------------------
prompt_template: |
  [System Instructions]
  You are a professional translator …

  [Terminology Rules]
  {rules_block}

  [Source Text]
  {source_block}

dictionary:
  Transformer: ทรานส์ฟอร์เมอร์
  Neural Network: โครงข่ายประสาทเทียม
"""

import sys
from pathlib import Path
from typing import Dict

try:
    import yaml
except ImportError:
    sys.exit(
        "PyYAML is not installed. Run: pip install pyyaml"
    )


# --------------------------------------------------------------------------- #
# Default template used when config.yaml is absent or template key is missing  #
# --------------------------------------------------------------------------- #

DEFAULT_PROMPT_TEMPLATE = """\
[System Instructions]
You are a professional English-to-Thai translator working on a book.
Your task is to translate the source text accurately and naturally.
IMPORTANT: Keep the index numbers [n] before each paragraph — do NOT remove them.
Output format must mirror the source: one translated paragraph per index.

{rules_block}
[Source Text]
{source_block}"""


class Config:
    """Wraps the contents of a project's config.yaml file."""

    def __init__(self, project_dir: Path) -> None:
        self.project_dir = Path(project_dir)
        self.config_path = self.project_dir / "config.yaml"
        self.prompt_template: str = DEFAULT_PROMPT_TEMPLATE
        self.dictionary: Dict[str, str] = {}
        self._load()

    # ------------------------------------------------------------------ #
    # Public interface                                                     #
    # ------------------------------------------------------------------ #

    def _load(self) -> None:
        """Parse config.yaml; fall back to defaults on any error."""
        if not self.config_path.exists():
            print(
                f"[config] '{self.config_path}' not found — using defaults."
            )
            return

        with self.config_path.open("r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh) or {}

        self.prompt_template = data.get("prompt_template", DEFAULT_PROMPT_TEMPLATE)
        self.dictionary = data.get("dictionary", {})

    @classmethod
    def write_default(cls, project_dir: Path) -> None:
        """Create a starter config.yaml in *project_dir* if one doesn't exist."""
        config_path = Path(project_dir) / "config.yaml"
        if config_path.exists():
            return

        content = (
            "prompt_template: |\n"
            "  [System Instructions]\n"
            "  You are a professional English-to-Thai translator working on a book.\n"
            "  Keep the index numbers [n] before each paragraph.\n"
            "\n"
            "  {rules_block}\n"
            "  [Source Text]\n"
            "  {source_block}\n"
            "\n"
            "dictionary:\n"
            "  # Add terms below (source: translation)\n"
            "  # Example:\n"
            "  # Transformer: ทรานส์ฟอร์เมอร์\n"
        )
        config_path.write_text(content, encoding="utf-8")
        print(f"[config] Created default config at '{config_path}'")
