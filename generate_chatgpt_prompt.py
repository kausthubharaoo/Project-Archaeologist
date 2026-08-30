def generate_chatgpt_prompt(data):
    """Generates AI refactoring prompt safely."""
    files = data.get("file_analysis", {}) if isinstance(data, dict) else {}
    git = data.get("git_analysis", {}) if isinstance(data, dict) else {}
    
    churn_files = git.get("frequently_changed_files", [])
    churn_names = [f.get("file", "Unknown") for f in churn_files if isinstance(f, dict)] if isinstance(churn_files, list) else []
    
    todos = files.get("todos", [])
    todo_count = len(todos) if isinstance(todos, list) else 0

    prompt = f"""
--- CHATGPT PROMPT (Copy & Paste into ChatGPT) ---
Act as a Senior Software Architect. Analyze this project breakdown and give 3 key refactoring actions:
- Total Files: {files.get('total_files', 0)} ({files.get('total_lines', 0)} lines)
- Frequent Churn Files: {churn_names}
- Open TODO Count: {todo_count}
--------------------------------------------------
    """
    return prompt.strip()

# --- ADD THIS TO THE BOTTOM OF YOUR FILE ---
if __name__ == "__main__":
    # Test dictionary so the script can run standalone
    sample_data = {
        "total_files": 10,
        "total_lines": 1200,
        "churn_names": ["reporter.py"],
        "todos": ["Fix bug", "Refactor"]
    }
    
    output = generate_chatgpt_prompt(sample_data)
    print(output)