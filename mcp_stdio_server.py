#!/usr/bin/env python3
"""
SEO Copilot MCP Server - stdio-based for Claude Desktop integration
"""

import asyncio
from datetime import datetime
import logging
from typing import Any, List, Dict, Optional
import os

# Load environment variables FIRST
from dotenv import load_dotenv
load_dotenv()

from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.types import (
    Resource,
    Tool,
)
from pydantic import AnyUrl
import mcp.types as types

# Import your existing services
from services.dataforseo import fetch_live_serp
from services.parser import extract_serp_titles
from services.title_rewrite import suggest_better_titles

# Load config values from environment with fallbacks
DEFAULT_LOCATION_CODE = int(os.getenv("DEFAULT_LOCATION_CODE", "2840"))  # US
DEFAULT_LANGUAGE_CODE = os.getenv("DEFAULT_LANGUAGE_CODE", "en")
DEFAULT_DEVICE = os.getenv("DEFAULT_DEVICE", "desktop")

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("seo-copilot-mcp")

# Log the loaded configuration
logger.info(f"Configuration loaded - Location: {DEFAULT_LOCATION_CODE}, Language: {DEFAULT_LANGUAGE_CODE}, Device: {DEFAULT_DEVICE}")

# Create the MCP server
server = Server("seo-copilot")

@server.list_tools()
async def handle_list_tools() -> List[Tool]:
    """List available tools"""
    return [
        Tool(
            name="analyze_title",
            description="Analyze a webpage title and suggest SEO improvements based on SERP data",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query/keyword to analyze"
                    },
                    "user_title": {
                        "type": "string", 
                        "description": "The current title of the user's page"
                    },
                    "user_domain": {
                        "type": "string",
                        "description": "Your domain (e.g., 'example.com') to exclude from competitor analysis and identify your ranking"
                    },
                    "location_code": {
                        "type": "integer",
                        "description": f"Location code for SERP data (default: {DEFAULT_LOCATION_CODE})"
                    },
                    "language_code": {
                        "type": "string",
                        "description": f"Language code for SERP data (default: {DEFAULT_LANGUAGE_CODE})"
                    },
                    "device": {
                        "type": "string",
                        "description": f"Device type for SERP data (default: {DEFAULT_DEVICE})"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results to analyze in detail (default: 10, max: 100)"
                    }
                },
                "required": ["query", "user_title"]
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> List[types.TextContent]:
    """Handle tool calls"""
    if name == "analyze_title":
        return await analyze_title_tool(arguments)
    else:
        raise ValueError(f"Unknown tool: {name}")

async def analyze_title_tool(arguments: dict) -> List[types.TextContent]:
    """Analyze title and provide SEO suggestions"""
    try:
        # Extract arguments with proper defaults
        query = arguments.get("query")
        user_title = arguments.get("user_title")
        user_domain = arguments.get("user_domain", "").lower().strip()
        location_code = arguments.get("location_code", DEFAULT_LOCATION_CODE)
        language_code = arguments.get("language_code", DEFAULT_LANGUAGE_CODE)
        device = arguments.get("device", DEFAULT_DEVICE)
        max_results = min(arguments.get("max_results", 10), 100)

        if not query or not query.strip():
            raise ValueError("Query parameter is required and cannot be empty")
        if not user_title or not user_title.strip():
            raise ValueError("User title parameter is required and cannot be empty")

        logger.info(f"Analyzing title for query: {query}")
        logger.info(f"Using location: {location_code}, language: {language_code}, device: {device}")

        try:
            serp = fetch_live_serp(
                keyword=query,
                location_code=location_code,
                language_code=language_code,
                device=device
            )
            logger.info("Using live SERP data from DataForSEO API")
        except Exception as e:
            logger.error(f"Failed to fetch SERP: {e}")
            return [types.TextContent(type="text", text=f"❌ Error fetching SERP data:\n\n{str(e)}")]

        from services.parser import extract_organic_results, extract_paa_questions
        organic_results = extract_organic_results(serp)
        paa_questions = extract_paa_questions(serp)

        user_result = None
        user_ranking = None
        user_duplicates = []
        competitor_results = []

        clean_user_domain = user_domain.replace('www.', '') if user_domain else ''
        for result in organic_results:
            url = result.get('url', '')
            result_domain = url.split('/')[2].lower().replace('www.', '') if url else ''
            rank = result.get('position', result.get('rank_absolute', 0))

            if clean_user_domain and result_domain == clean_user_domain:
                if user_result is None or rank < user_ranking:
                    user_result = result
                    user_ranking = rank
                    logger.info(f"Found user's domain at position {user_ranking}")
                else:
                    user_duplicates.append(result)
            else:
                competitor_results.append(result)

        competitor_titles = [r.get("title", "") for r in competitor_results if r.get("title")]

        api_key = os.getenv("ANTHROPIC_API_KEY")
        use_ai_suggestions = api_key is not None and api_key.strip() != ""

        suggestions_data = None
        if use_ai_suggestions:
            logger.info("Using Anthropic API for AI-generated suggestions")
            try:
                suggestions_data = suggest_better_titles(
                    query=query,
                    user_title=user_title,
                    competitor_titles=competitor_titles
                )
                logger.info(f"AI suggestions generated: {len(suggestions_data.get('suggestions', []))}")
            except Exception as e:
                logger.error(f"Error generating AI suggestions: {str(e)}")
                suggestions_data = None
        else:
            logger.info("No Anthropic API key found - falling back to manual analysis")

        response_text = f"# SEO Title Analysis Results\n\n"
        response_text += f"**Query analyzed:** {query}\n"
        response_text += f"**Current title:** {user_title}\n"
        response_text += f"**Your domain:** {user_domain or 'Not specified'}\n"
        response_text += f"**Search location:** {location_code} ({language_code})\n"
        response_text += f"**Device type:** {device}\n"

        if user_domain and user_ranking is not None:
            response_text += f"**Your current ranking:** Position #{user_ranking}\n"
            response_text += f"**Your current SERP title:** {user_result.get('title', 'N/A')}\n"
        elif user_domain:
            response_text += f"**Your current ranking:** Not found in top {len(organic_results)} results\n"

        response_text += f"**Competitor titles found:** {len(competitor_titles)}\n"
        response_text += f"**Total organic results:** {len(organic_results)}\n"
        response_text += f"**People Also Ask questions:** {len(paa_questions)}\n"
        response_text += f"**Showing detailed analysis for:** Top {min(max_results, len(competitor_results))} competitor results\n"
        response_text += f"**AI Suggestions:** {'Enabled' if use_ai_suggestions else 'Disabled (no API key)'}\n\n"

        if use_ai_suggestions and suggestions_data:
            response_text += "## AI-Generated SEO Title Suggestions:\n\n"
            for i, suggestion in enumerate(suggestions_data.get("suggestions", []), 1):
                response_text += f"### Suggestion {i}\n"
                response_text += f"**Title:** {suggestion.get('title', 'N/A')}\n"
                response_text += f"**Meta Description:** {suggestion.get('description', 'N/A')}\n"
                response_text += f"**Rationale:** {suggestion.get('rationale', 'N/A')}\n\n"
        else:
            response_text += generate_seo_guidelines(query, user_title, competitor_titles, competitor_results, paa_questions, user_ranking)

        if paa_questions:
            response_text += "## People Also Ask Questions:\n\n"
            for i, question in enumerate(paa_questions, 1):
                response_text += f"{i}. {question}\n"
            response_text += "\n"

        results_to_show = competitor_results[:max_results]
        response_text += f"## Detailed Competitor Analysis (Top {len(results_to_show)} competitors):\n\n"
        for i, result in enumerate(results_to_show, 1):
            response_text += f"### Competitor #{i} (Position #{result.get('position', 'N/A')})\n"
            response_text += f"**Title:** {result.get('title', 'N/A')}\n"
            response_text += f"**URL:** {result.get('url', 'N/A')}\n"
            response_text += f"**Domain:** {result.get('url', '').split('/')[2] if result.get('url') else 'N/A'}\n"
            response_text += f"**Description:** {result.get('description', 'N/A')}\n\n"

        enhanced_analysis = generate_enhanced_analysis(organic_results, competitor_titles, query, serp)
        response_text += "\n## Enhanced SERP Analysis\n"
        response_text += enhanced_analysis

        response_text += "\n## Additional SERP Data for Analysis\n"
        response_text += f"**Total SERP results:** {serp.get('se_results_count', 'N/A')}\n"
        response_text += f"**Search performed:** {serp.get('datetime', 'N/A')}\n"
        response_text += f"**Location:** {serp.get('location_code', 'N/A')}\n"
        response_text += f"**Device:** {serp.get('device', 'N/A')}\n"

        logger.info("Returning structured analysis response to client")
        return [types.TextContent(type="text", text=response_text)]

    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        return [types.TextContent(type="text", text=f"❌ Invalid input:\n\n{str(e)}")]
    except Exception as e:
        import traceback
        logger.error(f"Unhandled error: {str(e)}")
        logger.error(traceback.format_exc())
        return [types.TextContent(type="text", text=f"❌ Unexpected error:\n\n{str(e)}")]

def generate_seo_guidelines(query: str, user_title: str, competitor_titles: List[str], competitor_results: List[Dict], paa_questions: List[str], user_ranking: Optional[int] = None) -> str:
    """Generate SEO guidelines and analysis based on SERP data"""
    
    guidelines = "## SEO Analysis & Guidelines\n\n"
    
    # Current position analysis
    if user_ranking:
        guidelines += f"### Your Current Performance\n"
        guidelines += f"- **Current ranking:** Position #{user_ranking}\n"
        guidelines += f"- **Opportunity:** {'Good position - optimize to move higher' if user_ranking <= 10 else 'Significant improvement opportunity'}\n\n"
    else:
        guidelines += f"### Your Current Performance\n"
        guidelines += f"- **Current ranking:** Not found in top results\n"
        guidelines += f"- **Opportunity:** Significant optimization needed to enter top rankings\n\n"
    
    # Title length analysis
    if competitor_titles:
        title_lengths = [len(title) for title in competitor_titles if title]
        if title_lengths:
            avg_length = sum(title_lengths) / len(title_lengths)
            guidelines += f"### Title Length Analysis\n"
            guidelines += f"- **Your title length:** {len(user_title)} characters\n"
            guidelines += f"- **Average competitor length:** {avg_length:.1f} characters\n"
            guidelines += f"- **Competitor range:** {min(title_lengths)} - {max(title_lengths)} characters\n"
            guidelines += f"- **Recommendation:** Optimal title length is 50-60 characters\n\n"
    
    # Keyword analysis
    query_words = query.lower().split()
    titles_with_keyword = sum(1 for title in competitor_titles if any(word in title.lower() for word in query_words))
    
    guidelines += f"### Keyword Usage Analysis\n"
    guidelines += f"- **Competitor titles containing target keyword:** {titles_with_keyword}/{len(competitor_titles)}\n"
    guidelines += f"- **Your title contains keyword:** {'Yes' if any(word in user_title.lower() for word in query_words) else 'No'}\n"
    guidelines += f"- **Recommendation:** Include target keyword near the beginning of title\n\n"
    
    return guidelines

def generate_enhanced_analysis(organic_results: List[Dict], competitor_titles: List[str], query: str, serp: Dict) -> str:
    """Generate enhanced SERP analysis with quick wins"""
    
    analysis = ""
    
    if not competitor_titles:
        return "No competitor titles available for enhanced analysis.\n"
    
    # Power words analysis
    power_words = ['best', 'top', 'ultimate', 'complete', 'proven', 'guaranteed', 'exclusive', 'premium', 'leading', 'trusted', 'expert', 'professional', '#1', 'award', 'rated']
    power_word_usage = {}
    for word in power_words:
        count = sum(1 for title in competitor_titles if word.lower() in title.lower())
        if count > 0:
            power_word_usage[word] = count
    
    if power_word_usage:
        analysis += "### Power Words Analysis\n"
        for word, count in sorted(power_word_usage.items(), key=lambda x: x[1], reverse=True):
            analysis += f"- **'{word}':** used in {count}/{len(competitor_titles)} titles\n"
        analysis += "\n"
    
    # Year and freshness analysis
    current_year = str(datetime.now().year)
    titles_with_current_year = sum(1 for title in competitor_titles if current_year in title)
    titles_with_any_year = sum(1 for title in competitor_titles if any(year in title for year in ['2024', '2025', '2023']))
    
    analysis += "### Freshness & Date Analysis\n"
    analysis += f"- **Titles with {current_year}:** {titles_with_current_year}/{len(competitor_titles)}\n"
    analysis += f"- **Titles with any year:** {titles_with_any_year}/{len(competitor_titles)}\n"
    freshness_recommendation = "Include current year" if titles_with_any_year > len(competitor_titles) * 0.3 else "Year not critical for this query"
    analysis += f"- **Recommendation:** {freshness_recommendation}\n\n"
    
    # Numbers analysis
    titles_with_numbers = sum(1 for title in competitor_titles if any(char.isdigit() for char in title))
    analysis += f"### Numbers Usage\n"
    analysis += f"- **Titles with numbers:** {titles_with_numbers}/{len(competitor_titles)}\n\n"
    
    # Title structure analysis
    titles_with_pipes = sum(1 for title in competitor_titles if '|' in title)
    titles_with_dashes = sum(1 for title in competitor_titles if ' - ' in title)
    
    analysis += "### Title Structure Patterns\n"
    analysis += f"- **Using pipe separators (|):** {titles_with_pipes}/{len(competitor_titles)}\n"
    analysis += f"- **Using dash separators (-):** {titles_with_dashes}/{len(competitor_titles)}\n\n"
    
    return analysis

@server.list_resources()
async def handle_list_resources() -> List[Resource]:
    """List available resources"""
    return []

@server.read_resource()
async def handle_read_resource(uri: AnyUrl) -> str:
    """Read resource content"""
    raise ValueError(f"No resources are available in this MCP server")

async def main():
    """Run the MCP server"""
    from mcp.server.stdio import stdio_server
    
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="seo-copilot",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                )
            )
        )

if __name__ == "__main__":
    asyncio.run(main())