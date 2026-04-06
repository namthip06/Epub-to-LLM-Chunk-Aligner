# Bilingual Book Translator CLI

A command-line tool to assist in translating books and documents by dividing the content into manageable chunks for AI/LLM translation, and then automatically reassembling the results into a structured, bilingual ePub file (paragraph-by-paragraph).

Supports reading from **ePub**, **PDF**, and **Markdown** formats.

## 📦 Installation

To get started, clone the repository or download the project files, and install the required Python dependencies:

```bash
pip install -r requirements.txt
```

This will install the libraries needed for reading and writing files:
- `ebooklib` (for reading/writing ePub files)
- `beautifulsoup4` (for HTML parsing in ePub files)
- `PyPDF2` (for parsing PDFs)
- `PyYAML` (for loading configurations)

## 🚀 How to Run the Project (Workflow)

The intended process is structured into four main steps: project initialization, chunk extraction, manual LLM translation, and book assembly.

### 1. Initialize a New Project

Start by initializing a project directory to hold the config rules and the output pipeline.

```bash
python main.py init ./my-book-project
```

This creates the following directory scaffold:
```text
/my-book-project/
├── config.yaml    # Stores your dictionary terms and prompt template
├── source/        # Place your original source files here
├── chunks/        # The CLI generates prompt chunks here
├── translated/    # You place translated chunks here
└── output/        # The final compiled bilingual ePub goes here
```

> **Tip:** You can optionally place your source `.epub`, `.md` or `.pdf` inside `source/`, though the extraction command accepts any valid path.

### 2. Extract and Chunk Source Text

Extract text from your document. The chunker logically groups paragraphs within a safe character limit (default 5,000 characters) without cutting a paragraph in half. It injects terminology rules specifically needed for each chunk.

```bash
python main.py extract /path/to/my-book.epub ./my-book-project --limit 5000
```

* This will output numbered text files (e.g., `001.txt`, `002.txt`) in your `./my-book-project/chunks/` directory.
* Each file contains a ready-to-copy LLM Prompt, formatting instructions, specific translation rules, and the indexed source text.

### 3. Translate via LLM

This is a manual step emphasizing copy-pasting for strict control:
1. Open a generated chunk file (e.g. `chunks/001.txt`).
2. Copy its entire content into your favorite LLM or Chat UI.
3. Once the LLM translates the text, create a file with the exact same name in the `translated` folder (e.g. `translated/001.txt`).
4. Paste the LLM's response into it. Ensure the `[n]` index numbers are intact!

### 4. Assemble the Bilingual ePub

Once all chunk files have equivalent files in the `translated/` directory, you can merge everything back together into a final bilingual ePub output.

```bash
python main.py assemble ./my-book-project
```

* The assembler pairs up the English and Thai versions of text utilizing the `[n]` index tags.
* It verifies that the translated indices match the source indices, letting you know exactly if anything was truncated or skipped!
* The final compiled book will be saved as `output/bilingual.epub`.

## ⚙️ Configuration (`config.yaml`)

Inside your project root (`./my-book-project/config.yaml`), you'll find the configuration file.

### Custom Dictionary Rules
You can enforce consistent terminology across translations by adding rules under the `dictionary` block. For example:
```yaml
dictionary:
  Transformer: ทรานส์ฟอร์เมอร์
  Neural Network: โครงข่ายประสาทเทียม
  Generative AI: ปัญญาประดิษฐ์เชิงรู้สร้าง
```
During the *extraction* phase, if any chunk contains the English word "Transformer", the CLI will automatically inject a rule instructing the LLM to use the specified Thai counterpart.

### Prompt Template Customization
You can tweak the `prompt_template` as needed. Just be sure to leave `{rules_block}` and `{source_block}` intact inside the file.
