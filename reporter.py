import datetime
import json
import statistics
import textwrap
from mock_data import MOCK_INTEGRATED_DATA


#------- HELPER FUNCTIONS -------
def calculate_summary_stats(file_data):
    """Calculate average and median line counts using standard statistics."""
    sizes = file_data.get("file_sizes", [])
    if not sizes:
        return {"avg_lines": 0, "median_lines": 0}
    
    return {
        "avg_lines": round(statistics.mean(sizes), 1),
        "median_lines": statistics.median(sizes)
    }
def generate_cli_view(data, stats):
    """Format and wrap the terminal report using textwrap."""
    # Safe extraction of dictionaries
    data = data if isinstance(data, dict) else {}
    stats = stats if isinstance(stats, dict) else {}

    meta = data.get("meta", {}) if isinstance(data.get("meta"), dict) else {}
    files = data.get("file_analysis", {}) if isinstance(data.get("file_analysis"), dict) else {}
    git = data.get("git_analysis", {}) if isinstance(data.get("git_analysis"), dict) else {}

    header = "=" * 60 + "\n" + " PROJECT ARCHAEOLOGIST REPORT ".center(60) + "\n" + "=" * 60

    overview = f"""
    Target Path  : {meta.get('target_path', 'N/A')}
    Generated At : {meta.get('generated_at', 'N/A')}

    [ FILE & CODE METRICS ]
    Total Files   : {files.get('total_files', 0)}
    Total Lines   : {files.get('total_lines', 0)}
    Avg Lines/File: {stats.get('avg_lines', 0)}
    Median Lines  : {stats.get('median_lines', 0)}

    [ GIT METRICS ]
    Total Commits : {git.get('total_commits', 0)}
    Active Branches: {git.get('active_branches', 0)}
    """
    
    # Format TODOs neatly with textwrap
    todos_header = "\n[ TODO HOTSPOTS ]\n"
    formatted_todos = []
    todos = files.get("todos", []) if isinstance(files, dict) else []
    for todo in todos:
    # Your todo processing code here
        raw_text = f"• [{todo['file']}:{todo['line']}] {todo['text']}"
        formatted_todos.append(textwrap.fill(raw_text, width=58, subsequent_indent="  "))
        
    return textwrap.dedent(header + overview) + todos_header + "\n".join(formatted_todos)


def export_json_report(data, stats, filename="archeologist_report.json"):
    """Export the processed summary into a JSON file."""
    output = dict(data)
    output["calculated_stats"] = stats
    
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=4)
    print(f"\n Successfully saved JSON report to '{filename}'")


def generate_chatgpt_prompt(data):
    """Create an AI prompt for quick refactoring suggestions."""
    data = data if isinstance(data, dict) else {}
    files = data.get("file_analysis", {}) if isinstance(data.get("file_analysis"), dict) else {}
    git = data.get("git_analysis", {}) if isinstance(data.get("git_analysis"), dict) else {}

    total_files = files.get('total_files', 0)
    total_lines = files.get('total_lines', 0)
    churn_files = [f.get('file', '') for f in git.get('frequently_changed_files', []) if isinstance(f, dict)]
    todo_count = len(files.get('todos', [])) if isinstance(files.get('todos'), list) else 0

    prompt = f"""
--- CHATGPT PROMPT (Copy & Paste below into ChatGPT) ---
Act as a Senior Software Architect. Analyze this project breakdown and give 3 key refactoring actions:
- Total Files: {total_files} ({total_lines} lines)
- Frequent Churn Files: {churn_files}
- Open TODO Count: {todo_count}
--------------------------------------------------
"""
    return prompt.strip()


#----- THE MAIN PACKAGE FUNTION ----
# This is the single function Member 1 will call when the whole app runs.

def generate_report(meta_data, file_data, git_data):
    """Main function called by the CLI Lead during final integration."""
    combined_data = {
        "meta": meta_data,
        "file_analysis": file_data,
        "git_analysis": git_data
    }
    
    # 1. Process stats
    stats = calculate_summary_stats(file_data)
    
    # 2. Render CLI report
    cli_output = generate_cli_view(combined_data, stats)
    print(cli_output)
    
    # 3. Print ChatGPT prompt
    print("\n" + generate_chatgpt_prompt(combined_data))
    
    # 4. Save JSON export
    export_json_report(combined_data, stats)


if __name__ == "__main__":
    # Test using your mock data ONLY when running this file directly
    from mock_data import MOCK_INTEGRATED_DATA
    
    generate_report(
        MOCK_INTEGRATED_DATA["meta"],
        MOCK_INTEGRATED_DATA["file_analysis"],
        MOCK_INTEGRATED_DATA["git_analysis"]
    )

if __name__ == "__main__":
    from mock_data import MOCK_INTEGRATED_DATA
    
    print("--- TEST 1: Normal Mock Data ---")
    generate_report(
        MOCK_INTEGRATED_DATA["meta"],
        MOCK_INTEGRATED_DATA["file_analysis"],
        MOCK_INTEGRATED_DATA["git_analysis"]
    )

    print("\n--- TEST 2: Empty/Corrupted Input Defense ---")
    generate_report({}, {}, {})  # Tests completely empty input without crashing