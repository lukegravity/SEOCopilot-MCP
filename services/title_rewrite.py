import os
import json
import requests
from typing import List, Dict
import logging
import re

logger = logging.getLogger(__name__)

import os
import json
import requests
from typing import List, Dict
import logging
import re

logger = logging.getLogger(__name__)

def suggest_better_titles(query: str, user_title: str, competitor_titles: List[str]) -> Dict:
    """Generate SEO title suggestions using Claude (Anthropic) API"""

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key or not api_key.strip():
        logger.error("ANTHROPIC_API_KEY environment variable not set or empty")
        raise RuntimeError("ANTHROPIC_API_KEY environment variable not set or empty")

    top_titles = competitor_titles[:10]
    prompt = (
        "You are an expert SEO assistant.\n\n"
        f"Your task is to suggest 5 **click-optimized** meta titles and descriptions for the query: \"{query}\".\n"
        f"The current page title is:\n\"{user_title}\"\n\n"
        "Here are current top SERP titles:\n"
        + '\n'.join(f"- {t}" for t in top_titles) + "\n\n"
        "🧠 Use this data to guide your suggestions — aim to outperform these titles with better structure, CTR appeal, and relevance.\n\n"
        "🎯 Follow these rules strictly:\n"
        "- Return **exactly 5** suggestions\n"
        "- Titles: 50–65 characters\n"
        "- Descriptions: 120–160 characters\n"
        "- Emojis only if SERP uses them (at start or end)\n"
        "- Each suggestion must include: title, description, rationale\n\n"
        "📦 Format your response **exactly** like this:\n"
        "```json\n"
        "{\n"
        "  \"suggestions\": [\n"
        "    {\n"
        "      \"title\": \"Example title\",\n"
        "      \"description\": \"Example description\",\n"
        "      \"rationale\": \"Reason this works\"\n"
        "    },\n"
        "    ... (5 total)\n"
        "  ]\n"
        "}\n"
        "```\n"
        "Return **only this JSON block**, no commentary or text outside it."
    )

    headers = {
        "x-api-key": api_key,
        "content-type": "application/json",
        "anthropic-version": "2023-06-01"
    }

    data = {
        "model": "claude-3-haiku-20240307",
        "max_tokens": 2000,
        "temperature": 0.7,
        "system": "You are an expert SEO assistant that provides helpful, accurate, and well-structured title and description suggestions.",
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ]
    }

    try:
        logger.info("Sending request to Claude API...")
        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers=headers,
            json=data,
            timeout=30
        )
        response.raise_for_status()
        result = response.json()

        content = result.get("content", [{}])[0].get("text", "")
        logger.info("Parsing Claude response...")

        parsed = None

        # Try extracting JSON from ```json ... ``` block
        match = re.search(r'```json\s*({.*?})\s*```', content, re.DOTALL)
        if match:
            try:
                parsed = json.loads(match.group(1))
                logger.info("Parsed Claude response from JSON code block")
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON from code block: {e}")
        else:
            # Try parsing full content as raw JSON
            try:
                parsed = json.loads(content)
                logger.info("Parsed Claude response as direct JSON")
            except json.JSONDecodeError as e:
                logger.error("Claude response was not valid JSON")
                logger.debug(f"Raw content: {content[:300]}...")
                parsed = {"suggestions": []}

        if not parsed or "suggestions" not in parsed:
            logger.warning("Claude response missing 'suggestions' key")
            parsed = {"suggestions": []}

        if len(parsed["suggestions"]) != 5:
            logger.warning(f"Claude returned {len(parsed['suggestions'])} suggestions instead of 5")

        return {
            "query": query,
            "user_title": user_title,
            "top_serp_titles": top_titles,
            "suggestions": parsed["suggestions"]
        }

    except requests.exceptions.RequestException as e:
        logger.error(f"Request error: {e}")
        raise RuntimeError(f"Claude API error: {str(e)}")

