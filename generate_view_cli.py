import textwrap

def generate_cli_view(data, stats):
    """Generates formatted terminal text safely using textwrap."""
    # Safely extract sub-dictionaries
    meta = data.get("meta", {}) if isinstance(data, dict) else {}
    files = data.get("file_analysis", {}) if isinstance(data, dict) else {}
    git = data.get("git_analysis", {}) if isinstance(data, dict) else {}
    stats = stats if isinstance(stats, dict) else {}
    header = "=" * 60 + "\n" + " PROJECT ARCHAEOLOGIST REPORT ".center(60) + "\n" + "=" * 60
    
    overview = f"""
    Target Path    : {meta.get('target_path', 'N/A')}
    Generated At   : {meta.get('generated_at', 'N/A')}
    
    [ FILE & CODE METRICS ]
    Total Files    : {files.get('total_files', 0)}
    Total Lines    : {files.get('total_lines', 0)}
    Avg Lines/File : {stats.get('avg_lines', 0)}
    Median Lines   : {stats.get('median_lines', 0)}
    
    [ GIT METRICS ]
    Total Commits  : {git.get('total_commits', 0)}
    Active Branches: {git.get('active_branches', 0)}
    """
    
    # Process TODOs safely
    todos = files.get("todos", [])
    todos_header = "\n[ TODO HOTSPOTS ]\n"
    formatted_todos = []
    
    if isinstance(todos, list) and todos:
        for todo in todos:
            if isinstance(todo, dict):
                file_name = todo.get("file", "Unknown")
                line_no = todo.get("line", "?")
                text = todo.get("text", "")
                raw_text = f"• [{file_name}:{line_no}] {text}"
                formatted_todos.append(textwrap.fill(raw_text, width=58, subsequent_indent="  "))
    else:
        formatted_todos.append("• No open TODOs found.")

    return textwrap.dedent(header + overview) + todos_header + "\n".join(formatted_todos)

if __name__ == "__main__":
    from mock_data import MOCK_INTEGRATED_DATA
    
    # Optional dummy stats if calculate_summary_stats isn't imported yet
    sample_stats = {"avg_lines": 400.0, "median_lines": 340}

    # Pass the imported mock data to your function
    print(generate_cli_view(MOCK_INTEGRATED_DATA, sample_stats))