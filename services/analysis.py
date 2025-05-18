from typing import List, Dict
from models.serp import SerpEntry

def analyze_serp_data(serp_data: List[Dict]) -> Dict:
    entries = [SerpEntry(**item) for item in serp_data]

    title_lengths = [len(entry.title) for entry in entries if entry.title]

    if not title_lengths:
        return {"error": "No valid titles found in data."}

    return {
        "total_entries": len(entries),
        "avg_title_length": sum(title_lengths) / len(title_lengths),
        "shortest_title": min(title_lengths),
        "longest_title": max(title_lengths)
    }
