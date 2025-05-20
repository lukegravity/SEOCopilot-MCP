import requests
from config import DATAFORSEO_LOGIN, DATAFORSEO_PASSWORD

def fetch_live_serp(keyword: str, location_code: int, language_code: str, device: str = "desktop") -> dict:
    if not DATAFORSEO_LOGIN or not DATAFORSEO_PASSWORD:
        raise RuntimeError("Missing DataForSEO credentials")

    url = "https://api.dataforseo.com/v3/serp/google/organic/live/advanced"

    payload = [
        {
            "keyword": keyword,
            "location_code": location_code,
            "language_code": language_code,
            "device": device
        }
    ]

    response = requests.post(
        url,
        auth=(DATAFORSEO_LOGIN, DATAFORSEO_PASSWORD),
        json=payload
    )

    if response.status_code != 200:
        raise RuntimeError(f"DataForSEO API error: {response.status_code} - {response.text}")

    data = response.json()

    try:
        return data["tasks"][0]["result"][0]  # This is the actual SERP result block
    except (KeyError, IndexError):
        raise RuntimeError("Malformed DataForSEO response")
