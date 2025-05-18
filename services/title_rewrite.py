import openai
import os
from typing import List, Dict

def suggest_better_titles(query: str, user_title: str, competitor_titles: List[str]) -> Dict:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY environment variable not set.")

    openai.api_key = api_key

    top_titles = competitor_titles[:10]

    prompt = f"""
You are an expert SEO assistant.

Your task is to generate a set of compelling and optimized meta titles and meta descriptions for the query: "{query}".

The page currently uses this title:
"{user_title}"

Here are the top titles currently ranking in Google for this query:
{chr(10).join(f"- {t}" for t in top_titles)}

Use the SERP data above to guide your suggestions — match the tone, length, and structure where needed, but aim to **outperform these** by being more relevant, clickable, and unique.

Follow these principles:
- Prioritize **CTR (click-through rate)** above all — drive user intent
- Titles must be between **50–60 characters**
- Descriptions must be between **120–160 characters**
- If the SERP includes **emojis**, include tasteful, relevant emoji suggestions too
- Consider **average SERP title length** and adjust suggestions to match Google’s presentation
- Look for angles that the current titles may be missing: CTAs, emotional appeal, specificity, or uniqueness

Return:
- **5 meta title suggestions**
- **5 meta description suggestions**
- A short explanation (1–2 lines) of what each pair aims to achieve — e.g., “emotional CTA”, “commercial offer”, “clear USP”, etc.

Respond in markdown format.
"""


    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
    )

    content = response["choices"][0]["message"]["content"]
    suggestions = [line.strip("- ").strip() for line in content.strip().splitlines() if line.strip().startswith("-")]

    return {
        "query": query,
        "user_title": user_title,
        "similarity_score": None,
        "top_serp_titles": top_titles,
        "suggestions": suggestions
    }
