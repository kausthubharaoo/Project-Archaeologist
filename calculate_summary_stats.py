import statistics

def calculate_summary_stats(file_data):
    """Safely calculates summary statistics for line counts."""
    # Ensure file_data is a dictionary
    if not isinstance(file_data, dict):
        return {"avg_lines": 0, "median_lines": 0}
        
    sizes = file_data.get("file_sizes", [])
    
    # Check if sizes is empty or invalid
    if not sizes or not isinstance(sizes, list):
        return {"avg_lines": 0, "median_lines": 0}
        
    try:
        return {
            "avg_lines": round(statistics.mean(sizes), 1),
            "median_lines": round(statistics.median(sizes), 1)
        }
    except Exception:
        return {"avg_lines": 0, "median_lines": 0}
   
# Add this at the very bottom of calculate_summary_stats.py

if __name__ == "__main__":
    from mock_data import MOCK_INTEGRATED_DATA
    
    # Extract file_analysis dict from mock data
    file_data = MOCK_INTEGRATED_DATA.get("file_analysis", {})
    
    # Call function and print calculated summary stats
    result = calculate_summary_stats(file_data)
    print("Summary Stats Output:", result)