from fastapi import FastAPI
from pydantic import BaseModel
from services.analysis import analyze_serp_data
from services.suggestions import generate_suggestions
from services.parser import extract_organic_results, extract_serp_titles
from services.title_rewrite import suggest_better_titles
from config import DOMAIN
import json

app = FastAPI()

@app.get("/")
def root():
    return {"status": "SEO Copilot MCP Server running"}


@app.get("/analyze")
def analyze():
    try:
        with open("data/serp-sample.json", "r", encoding="utf-8") as f:
            raw_data = json.load(f)

        serp_entries = extract_organic_results(raw_data)
        analysis = analyze_serp_data(serp_entries)
        suggestions = generate_suggestions(serp_entries, DOMAIN)

        return {
            "domain": DOMAIN,
            "analysis": analysis,
            "suggestions": suggestions
        }
    except Exception as e:
        return {"error": str(e)}


# ✅ Add this new POST-based endpoint for user title improvement
class SimplifiedAnalyzeRequest(BaseModel):
    query: str
    user_title: str
    serp_json: dict

@app.post("/analyze")
def simplified_title_analysis(request: SimplifiedAnalyzeRequest):
    try:
        titles = extract_serp_titles(request.serp_json)
        response = suggest_better_titles(request.query, request.user_title, titles)
        return response
    except Exception as e:
        return {"error": str(e)}