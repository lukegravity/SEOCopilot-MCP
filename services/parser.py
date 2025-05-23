from typing import List, Dict

def extract_serp_titles(dataforseo_response: Dict) -> List[str]:
    """
    Extract organic titles from DataForSEO response
    
    Args:
        dataforseo_response: The SERP result block from DataForSEO (already unwrapped)
    
    Returns:
        List of organic result titles
    """
    # The response is already the result block, so we can access items directly
    items = dataforseo_response.get("items", [])
    
    titles = []
    for item in items:
        if item.get("type") == "organic" and "title" in item:
            titles.append(item["title"])
    
    return titles

def extract_paa_questions(dataforseo_response: Dict) -> List[str]:
    """
    Extract People Also Ask questions from DataForSEO response
    
    Args:
        dataforseo_response: The SERP result block from DataForSEO
    
    Returns:
        List of PAA questions
    """
    items = dataforseo_response.get("items", [])
    paa_questions = []
    
    for item in items:
        if item.get("type") == "people_also_ask":
            # Extract questions from PAA items
            paa_items = item.get("items", [])
            for paa_item in paa_items:
                if paa_item.get("type") == "people_also_ask_element":
                    question = paa_item.get("title", "")
                    if question:
                        paa_questions.append(question)
    
    return paa_questions

def extract_organic_results(dataforseo_response: Dict) -> List[Dict]:
    """
    Extract detailed organic results from DataForSEO response
    
    Args:
        dataforseo_response: The SERP result block from DataForSEO
        
    Returns:
        List of organic result dictionaries with comprehensive data
    """
    keyword = dataforseo_response.get("keyword", "Unknown")
    location_name = dataforseo_response.get("location_name", "Unknown")
    language_code = dataforseo_response.get("language_code", "en")

    items = dataforseo_response.get("items", [])
    
    organic_results = []

    for item in items:
        if item.get("type") != "organic":
            continue

        organic_results.append({
            "keyword": keyword,
            "title": item.get("title", ""),
            "url": item.get("url", ""),
            "domain": item.get("domain", ""),
            "description": item.get("description", ""),
            "position": item.get("rank_group", 0),
            "rank_absolute": item.get("rank_absolute", 0),
            "language": language_code,
            "location_name": location_name,
            "breadcrumb": item.get("breadcrumb", ""),
            "website_name": item.get("website_name", ""),
            "is_featured_snippet": item.get("is_featured_snippet", False),
            "rating": item.get("rating", None),
            "highlighted": item.get("highlighted", []),
            "links": item.get("links", []),
            "faq": item.get("faq", None),
            "timestamp": item.get("timestamp", None)
        })

    return organic_results