from typing import List, Dict

def extract_serp_titles(dataforseo_response: Dict) -> List[str]:
    items = dataforseo_response["result"][0]["items"]
    return [item["title"] for item in items if item["type"] == "organic" and "title" in item]

def extract_organic_results(dataforseo_response: Dict) -> List[Dict]:
    keyword = dataforseo_response["result"][0]["keyword"]
    location_name = dataforseo_response["data"].get("location_name", "Unknown")
    language_code = dataforseo_response["data"].get("language_code", "en")

    items = dataforseo_response["result"][0]["items"]
    
    organic_results = []

    for item in items:
        if item["type"] != "organic":
            continue

        organic_results.append({
            "keyword": keyword,
            "title": item.get("title", ""),
            "url": item.get("url", ""),
            "position": item.get("rank_group", 0),
            "language": language_code,
            "location_name": location_name
        })

    return organic_results
