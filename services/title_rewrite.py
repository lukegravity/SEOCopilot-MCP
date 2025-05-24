import os
import json
import requests
from typing import List, Dict

def suggest_better_titles(query: str, user_title: str, competitor_titles: List[str]) -> Dict:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY environment variable not set.")

    top_titles = competitor_titles[:10]

    # Use triple quotes and avoid f-string formatting issues
    prompt = """You are an expert SEO assistant.

Your task is to generate a set of compelling and optimized meta titles and meta descriptions for the query: "{query}".

The page currently uses this title:
"{user_title}"

Here are the top titles currently ranking in Google for this query:
{competitor_titles}

Use the SERP data above to guide your suggestions — match the tone, length, and structure where needed, but aim to **outperform these** by being more relevant, clickable, and unique.

Follow these principles:
- Prioritize **CTR (click-through rate)** above all — drive user intent
- Titles should be between **50–65 characters**, unless the SERP data suggests that titles are generally shorter than this; be sure to include the rationale in your response.
- Descriptions must be between **120–160 characters**
- If the SERP includes **emojis**, include tasteful, relevant emoji suggestions too
- Emojis should always be at the **start** or the **end** of the title
- Consider **average SERP title length** and adjust suggestions to match Google's presentation - this can override the 50 character minimum as required
- Look for angles that the current titles may be missing: CTAs, emotional appeal, specificity, or uniqueness

Return exactly 5 suggestions, each with:
- A meta title
- A meta description
- A short explanation (1–2 lines) of what the suggestion aims to achieve

Format your response as a structured JSON with the following format:
```json
{{
  "suggestions": [
    {{
      "title": "Suggested title 1",
      "description": "Suggested description 1",
      "rationale": "Rationale for suggestion 1"
    }},
    {{
      "title": "Suggested title 2",
      "description": "Suggested description 2",
      "rationale": "Rationale for suggestion 2"
    }}
  ]
}}
```

Only return the JSON, no other text.""".format(
        query=query,
        user_title=user_title,
        competitor_titles='\n'.join(f"- {t}" for t in top_titles)
    )

    headers = {
        "x-api-key": api_key,
        "content-type": "application/json",
        "anthropic-version": "2023-06-01"
    }

    data = {
        "model": "claude-3-haiku-20240307",  # Cheaper model - was claude-3-opus-20240229
        "max_tokens": 2000,
        "temperature": 0.7,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "system": "You are an expert SEO assistant that provides helpful, accurate, and well-structured title and description suggestions."
    }

    try:
        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers=headers,
            json=data
        )
        response.raise_for_status()
        result = response.json()
        
        # Extract content from Claude's response
        content = result.get("content", [{}])[0].get("text", "")
        
        # Parse JSON from the response
        try:
            # Try to parse the entire response as JSON
            parsed_content = json.loads(content)
        except json.JSONDecodeError:
            # If that fails, try to extract JSON from markdown code blocks
            import re
            json_match = re.search(r'```(?:json)?\s*(.*?)\s*```', content, re.DOTALL)
            if json_match:
                try:
                    parsed_content = json.loads(json_match.group(1))
                except json.JSONDecodeError:
                    # If JSON parsing fails, return a default structure
                    parsed_content = {"suggestions": []}
            else:
                # If no JSON block found, return default structure
                parsed_content = {"suggestions": []}
        
        # Ensure we have the expected structure
        if "suggestions" not in parsed_content:
            parsed_content = {"suggestions": []}
            
        return {
            "query": query,
            "user_title": user_title,
            "similarity_score": None,
            "top_serp_titles": top_titles,
            "suggestions": parsed_content["suggestions"]
        }
    except Exception as e:
        raise RuntimeError(f"Error calling Claude API: {str(e)}")