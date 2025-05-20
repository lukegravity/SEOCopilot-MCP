from typing import List, Optional
from pydantic import BaseModel
from config import (
    DEFAULT_LOCATION_CODE,
    DEFAULT_LANGUAGE_CODE,
    DEFAULT_DEVICE,
    OPENAI_API_KEY,
)
from services.dataforseo import fetch_live_serp
from services.parser import extract_serp_titles
from services.title_rewrite import suggest_better_titles


# --- INPUT SCHEMA ---
class MCPRequest(BaseModel):
    query: str
    user_title: str
    location_code: Optional[int] = None
    language_code: Optional[str] = None
    device: Optional[str] = None


# --- OUTPUT SCHEMA ---
class Suggestion(BaseModel):
    title: str
    description: str
    rationale: str


class MCPResponse(BaseModel):
    query: str
    user_title: str
    competitor_titles: List[str]
    suggestions: List[Suggestion]
    model_used: str


# --- MAIN RUNNER ---
def run_analysis(request: MCPRequest) -> MCPResponse:
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY is not set")

    # Resolve fallbacks
    location = request.location_code or DEFAULT_LOCATION_CODE
    language = request.language_code or DEFAULT_LANGUAGE_CODE
    device = request.device or DEFAULT_DEVICE

    # Fetch SERP
    serp = fetch_live_serp(
        keyword=request.query,
        location_code=location,
        language_code=language,
        device=device
    )

    titles = extract_serp_titles(serp)

    # Generate suggestions (includes rationale + formatting)
    raw = suggest_better_titles(
        query=request.query,
        user_title=request.user_title,
        competitor_titles=titles
    )

    # You’ll eventually parse this better from markdown
    # For now, do simple formatting for structured output
    structured = [
        Suggestion(title=s.get("title"), description=s.get("description"), rationale=s.get("rationale"))
        for s in raw["suggestions"]
    ]

    return MCPResponse(
        query=request.query,
        user_title=request.user_title,
        competitor_titles=titles,
        suggestions=structured,
        model_used="openai:gpt-4"
    )
