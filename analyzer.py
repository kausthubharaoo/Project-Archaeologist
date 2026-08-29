import argparse
import ast
import json
import os
import re
import sys
from collections import Counter
from pathlib import Path

# File extensions to scan for general line counts and TODO comments
TEXT_EXTENSIONS = {
    ".py", ".js", ".ts", ".html", ".css", ".json", ".md", ".txt",
    ".c", ".cpp", ".h", ".java", ".go", ".rs", ".pyw", ".sh"
}

def analyze_python_ast(file_path):
    """Parses a Python file into an Abstract Syntax Tree to extract structural metrics."""
    metrics = {
        "classes": [],
        "functions": [],
        "imports": []
    }
    
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            tree = ast.parse(f.read(), filename=str(file_path))

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                metrics["classes"].append(node.name)
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                metrics["functions"].append(node.name)
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    metrics["imports"].append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    metrics["imports"].append(node.module)
    except Exception:
        pass  # Skip files with syntax errors

    return metrics

def scan_project(root_path):
    """Recursively scans directory and aggregates metadata, AST metrics, and code stats."""
    total_files = 0
    total_folders = 0
    total_size_bytes = 0
    total_lines = 0
    total_todos = 0
    
    file_types = Counter()
    todo_list = []
    
    ast_summary = {
        "total_python_files": 0,
        "classes": [],
        "functions": [],
        "imports": Counter()
    }

    for dirpath, dirnames, filenames in os.walk(root_path):
        # Exclude hidden directories like .git or .vscode
        dirnames[:] = [d for d in dirnames if not d.startswith(".")]
        total_folders += len(dirnames)

        for fname in filenames:
            if fname.startswith("."):
                continue
            
            file_path = Path(dirpath) / fname
            total_files += 1

            try:
                total_size_bytes += file_path.stat().st_size
            except OSError:
                pass

            ext = file_path.suffix.lower() or "no_extension"
            file_types[ext] += 1

            # Process readable source code files
            if ext in TEXT_EXTENSIONS:
                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        lines = f.readlines()
                        total_lines += len(lines)

                        for idx, line in enumerate(lines, start=1):
                            if "TODO" in line.upper():
                                total_todos += 1
                                todo_list.append({
                                    "file": str(file_path.relative_to(root_path)),
                                    "line": idx,
                                    "content": line.strip()
                                })
                except Exception:
                    pass

            # AST parsing for Python files
            if ext == ".py":
                ast_summary["total_python_files"] += 1
                py_metrics = analyze_python_ast(file_path)
                ast_summary["classes"].extend(py_metrics["classes"])
                ast_summary["functions"].extend(py_metrics["functions"])
                for imp in py_metrics["imports"]:
                    ast_summary["imports"][imp] += 1

    return {
        "summary": {
            "root_directory": str(root_path),
            "total_folders": total_folders,
            "total_files": total_files,
            "total_size_kb": round(total_size_bytes / 1024, 2),
            "total_lines": total_lines,
            "total_todos": total_todos
        },
        "file_types": dict(file_types),
        "ast_analysis": {
            "python_files": ast_summary["total_python_files"],
            "total_classes": len(ast_summary["classes"]),
            "total_functions": len(ast_summary["functions"]),
            "top_imports": dict(ast_summary["imports"].most_common(5)),
            "class_names": ast_summary["classes"][:10],
            "function_names": ast_summary["functions"][:10]
        },
        "todos": todo_list
    }

def print_summary(data):
    """Prints formatted output directly to terminal."""
    summary = data["summary"]
    ast_info = data["ast_analysis"]

    print("\n" + "=" * 55)
    print("           PROJECT & CODE ANALYSIS REPORT          ")
    print("=" * 55)
    print(f"Directory Analyzed : {summary['root_directory']}")
    print(f"Total Folders      : {summary['total_folders']}")
    print(f"Total Files        : {summary['total_files']}")
    print(f"Total Size         : {summary['total_size_kb']} KB")
    print(f"Total Lines of Code: {summary['total_lines']}")
    print(f"Total TODOs Found  : {summary['total_todos']}")
    
    print("\n--- File Types Breakdown ---")
    for ext, count in data["file_types"].items():
        print(f"  {ext:<15}: {count} file(s)")

    print("\n--- Python AST Metrics ---")
    print(f"  Python Files Parsed: {ast_info['python_files']}")
    print(f"  Classes Detected   : {ast_info['total_classes']}")
    print(f"  Functions Detected : {ast_info['total_functions']}")
    if ast_info["top_imports"]:
        print(f"  Top Imports        : {', '.join(ast_info['top_imports'].keys())}")

    if data["todos"]:
        print("\n--- Found TODOs ---")
        for item in data["todos"][:5]:
            print(f"  [{item['file']}:{item['line']}] {item['content']}")
        if len(data["todos"]) > 5:
            print(f"  ... and {len(data['todos']) - 5} more TODOs.")
    print("=" * 55 + "\n")

def main():
    parser = argparse.ArgumentParser(
        description="CLI tool for scanning projects, file analysis, and code metrics."
    )
    
    parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Path to target directory (default: current directory)"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON formatted string"
    )

    args = parser.parse_args()
    target_path = Path(args.path).resolve()

    if not target_path.exists() or not target_path.is_dir():
        print(f"Error: Target directory '{args.path}' does not exist or is invalid.", file=sys.stderr)
        sys.exit(1)

    analysis = scan_project(target_path)

    if args.json:
        print(json.dumps(analysis, indent=4))
    else:
        print_summary(analysis)

    sys.exit(0)

if __name__ == "__main__":
    main()