# schema.py or sample_data.py
MOCK_INTEGRATED_DATA = {
    # From Member 1: CLI + Command System (Metadata)
    "meta": {
        "target_path": "/path/to/repo",
        "generated_at": "2026-08-29T10:00:00"
    },
    
    # From Member 2: File + Code Analysis
    "file_analysis": {
        "total_files": 42,
        "total_lines": 3500,
        "file_types": {".py": 30, ".md": 5, ".json": 7},
        "file_sizes": [120, 450, 800, 230], # line counts for stats
        "todos": [
            {"file": "main.py", "line": 45, "text": "TODO: fix auth leak"}
        ]
    },

    # From Member 3: Git + Relationship Analysis
    "git_analysis": {
        "total_commits": 128,
        "active_branches": 3,
        "frequently_changed_files": [
            {"file": "app.py", "commit_count": 45},
            {"file": "utils.py", "commit_count": 30}
        ]
    }
}
