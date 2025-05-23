import requests
from typing import Optional
from config import DATAFORSEO_LOGIN, DATAFORSEO_PASSWORD

def fetch_live_serp(
    keyword: str, 
    location_code: int, 
    language_code: str, 
    device: str = "desktop",
    user_dataforseo_login: Optional[str] = None,
    user_dataforseo_password: Optional[str] = None
) -> dict:
    # Use user credentials if provided, otherwise fall back to default
    login = user_dataforseo_login or DATAFORSEO_LOGIN
    password = user_dataforseo_password or DATAFORSEO_PASSWORD

    if not login or not password:
        raise RuntimeError("Missing DataForSEO credentials. Please provide credentials in the MCP configuration.")

    url = "https://api.dataforseo.com/v3/serp/google/organic/live/advanced"

    payload = [
        {
            "keyword": keyword,
            "location_code": location_code,
            "language_code": language_code,
            "device": device
        }
    ]

    try:
        response = requests.post(
            url,
            auth=(login, password),
            json=payload
        )

        if response.status_code == 401:
            raise RuntimeError("DataForSEO API authentication failed. Please check your credentials.")
        
        if response.status_code != 200:
            raise RuntimeError(f"DataForSEO API error: {response.status_code} - {response.text}")

        data = response.json()

        # Check for errors in the API response
        if data.get("status_code") != 20000:
            error_message = data.get("status_message", "Unknown error")
            raise RuntimeError(f"DataForSEO API error: {error_message}")

        try:
            return data["tasks"][0]["result"][0]  # This is the actual SERP result block
        except (KeyError, IndexError):
            raise RuntimeError("Malformed DataForSEO response")
            
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Request to DataForSEO failed: {str(e)}")