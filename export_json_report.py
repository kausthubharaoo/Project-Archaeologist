import json

def export_json_report(data, stats, filename="archeologist_report.json"):
    """Exports structured output into JSON file."""
    try:
        output = dict(data) if isinstance(data, dict) else {}
        output["calculated_stats"] = stats

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=4)
        print(f"\nSuccessfully saved JSON report to '{filename}'")
    except Exception as e:
        print(f"\nFailed to export JSON report: {e}")

if __name__ == "__main__":
    # Example test call with dummy data
    sample_data = {"project": "Archaeologist", "status": "active"}
    sample_stats = {"total_files": 10, "lines_of_code": 450}

    export_json_report(sample_data, sample_stats)