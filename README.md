# CodeScan CLI - Project & Code Analysis Tool

A lightweight, zero-dependency Command Line Interface (CLI) tool built using standard Python libraries. `CodeScan` recursively inspects project repositories, gathers file metrics, extracts `TODO` items, tracks line counts, and parses Python Abstract Syntax Trees (`ast`) to summarize classes, functions, and imports.

---

## Key Features

* **Directory Traversals:** Recursively scans folders while ignoring hidden paths (`.git`, `.vscode`).
* **Code & File Metrics:** Aggregates line counts, file sizes, and file-type breakdowns.
* **TODO Tracker:** Identifies inline `TODO` tags across source code with line-level accuracy.
* **AST Code Analysis:** Parses Python syntax trees to extract functions, classes, and dependencies.
* **JSON Output Support:** Generates structured JSON output for easy integration into LLMs (ChatGPT/Copilot).

---

## Tech Stack

* **Language:** Python 3.8+
* **Standard Modules:** `argparse`, `os`, `sys`, `pathlib`, `re`, `collections`, `json`, `ast`

---

## Quick Start

### 1. Requirements
No external dependencies required. Standard Python installation is all you need.

### 2. Run Analysis on Current Directory
```bash
python analyzer.py