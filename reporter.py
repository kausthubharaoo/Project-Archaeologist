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
    meta = data["meta"]
    files = data["file_analysis"]
    git = data["git_analysis"]
    
    header = "=" * 60 + "\n" + " PROJECT ARCHAEOLOGIST REPORT ".center(60) + "\n" + "=" * 60
    
    overview = f"""
    Target Path    : {meta['target_path']}
    Generated At   : {meta['generated_at']}
    
    [ FILE & CODE METRICS ]
    Total Files    : {files['total_files']}
    Total Lines    : {files['total_lines']}
    Avg Lines/File : {stats['avg_lines']}
    Median Lines   : {stats['median_lines']}
    
    [ GIT METRICS ]
    Total Commits  : {git['total_commits']}
    Active Branches: {git['active_branches']}
    """
    
    # Format TODOs neatly with textwrap
    todos_header = "\n[ TODO HOTSPOTS ]\n"
    formatted_todos = []
    for todo in files["todos"]:
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
    files = data["file_analysis"]
    git = data["git_analysis"]
    
    prompt = f"""
--- CHATGPT PROMPT (Copy & Paste below into ChatGPT) ---
Act as a Senior Software Architect. Analyze this project breakdown and give 3 key refactoring actions:
- Total Files: {files['total_files']} ({files['total_lines']} lines)
- Frequent Churn Files: {[f['file'] for f in git['frequently_changed_files']]}
- Open TODO Count: {len(files['todos'])}
-------------------------------------------------------
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
