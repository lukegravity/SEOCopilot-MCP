from typing import List, Dict
from models.serp import SerpEntry

def generate_suggestions(serp_data: List[Dict], domain: str) -> Dict:
    entries = [SerpEntry(**item) for item in serp_data]

    suggestions = {}

    for entry in entries:
        if not entry.keyword or not entry.title:
            continue

        base_keyword = entry.keyword.strip().capitalize()
        suggestions[entry.keyword] = {
            "original_title": entry.title,
            "proposed_title": f"{base_keyword} | {domain}"
        }

    return suggestions
