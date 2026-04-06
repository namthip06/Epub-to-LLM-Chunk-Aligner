### **Implementation Plan: Bilingual CLI Translator**

#### **Phase 1: Environment & Core Models**
* **Setup:** Create a Python project (or Node.js, whichever you prefer) and manage dependencies (e.g., `EbookLib` for ePub, `PyPDF2` for PDF).
* **Models:** Define the data structure for `Paragraph` and `Chunk`.
* `Paragraph`: `{ index: int, text: str, chapter: str }`
* `Chunk`: `{ id: int, content: List[Paragraph], rules: Dict }`
* **Config:** Load a `config.yaml` file to store prompt templates and dictionary mapping.

#### **Phase 2: Source Parsers & Chunking Engine**
* **Parsers:** Write the module. To read content from ePub, PDF, and Markdown and display it as a `List[Paragraph]`, clearly separating it into chapters.
* **Buffer Logic:** Develop an algorithm. **Buffer-Aware Splitter**
* Iterate through paragraph by paragraph.
* Calculate Character Count.
* Truncate a chunk when it reaches a limit (e.g., 5,000 chars) without cutting in the middle of a paragraph.
* **CLI Command:** `extract <file>` to create a `.txt` file in the `/chunks` folder.

#### **Phase 3: Rule Injector & Prompt Templating**
* **Scanner:** Write a Regex system to scan for words in the Dictionary that appear in each Chunk.
* **Template Engine:** Combine Source Text + Dynamic Rules with Prompt Template.
* **Output Formatting:** Generate a `.txt` file with Index numbers `[1]`, `[2]` before each paragraph so that the User can copy it immediately.

#### **Phase 4: Assembly & Validation**
* **Parser (Translated):** Write a Module to read a file from `/translated` using Regex to extract the content after the Index number. `[n]`
* **Alignment Check:** Function to check if the number of paragraphs in `translated/001.txt` matches `chunks/001.txt`.
* **Bilingual Merging:** Merging [Eng] + [Thai] together, removing the index numbers.
* **ePub Generator:** Assemble bilingual content back into an ePub file, maintaining the chapter structure (Table of Contents).

#### **Phase 5: Refinement & Testing**
* **Testing:** Test with an ePub file containing images or tables (to ensure it doesn't break).
* **CLI UX:** Refine the CLI commands for easier use (e.g., with a progress bar or a summary of the number of words translated).
* **CLI Command:** `assemble <project-folder>` to finish the process.