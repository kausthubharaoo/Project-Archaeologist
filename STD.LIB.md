# Standard Library Usage & Dependency Proof

This project strictly adheres to a zero-dependency policy and relies exclusively on Python's built-in Standard Library modules.

## Modules Used
* **`os` / `sys` / `pathlib`**: File system manipulation and CLI argument handling.
* **`json`**: Reading and generating project analysis reports (`report.json`).
* **`subprocess`**: Executing Git commands directly for repository scanning.
* **`unittest`**: Running automated test suites in `tests/`.

## Verification
* No third-party packages are installed or required.
* `requirements.txt` is intentionally kept empty to satisfy zero-dependency constraints.