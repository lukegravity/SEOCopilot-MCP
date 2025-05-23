#!/usr/bin/env python3
"""
SEO Copilot MCP Server - stdio-based for Claude Desktop integration
"""

import asyncio
import json
import logging
from typing import Any, List, Dict, Optional
from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.types import (
    Resource,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
)
from pydantic import AnyUrl
import mcp.types as types

# Import your existing services
from services.dataforseo import fetch_live_serp
from services.parser import extract_serp_titles
from services.title_rewrite import suggest_better_titles
from config import (
    DEFAULT_LOCATION_CODE,
    DEFAULT_LANGUAGE_CODE,
    DEFAULT_DEVICE,
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("seo-copilot-mcp")

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
                    "location_code": {
                        "type": "integer",
                        "description": "Location code for SERP data (default: 2840 for US)"
                    },
                    "language_code": {
                        "type": "string",
                        "description": "Language code for SERP data (default: en)"
                    },
                    "device": {
                        "type": "string",
                        "description": "Device type for SERP data (default: desktop)"
                    },
                    "use_test_data": {
                        "type": "boolean",
                        "description": "Use local test data instead of live API call"
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
        # Extract arguments
        query = arguments.get("query")
        user_title = arguments.get("user_title")
        location_code = arguments.get("location_code", DEFAULT_LOCATION_CODE)
        language_code = arguments.get("language_code", DEFAULT_LANGUAGE_CODE)
        device = arguments.get("device", DEFAULT_DEVICE)
        use_test_data = arguments.get("use_test_data", False)
        
        logger.info(f"Analyzing title for query: {query}")
        
        # Check if we should use test data (automatically use for sweepstakes casinos)
        if use_test_data or query.lower() == "sweepstakes casinos":
            # Use local test data
            try:
                with open("data/payload.json", "r", encoding="utf-8") as f:
                    test_data = json.load(f)
                # Extract the SERP result from the payload structure
                serp = test_data.get("serp_json", {})
                logger.info("Using local test data from payload.json")
            except Exception as e:
                raise RuntimeError(f"Error loading test data: {str(e)}")
        else:
            # Fetch live SERP data
            serp = fetch_live_serp(
                keyword=query,
                location_code=location_code,
                language_code=language_code,
                device=device
            )
            logger.info("Using live SERP data from DataForSEO API")

        # Extract competitor titles and full SERP data
        titles = extract_serp_titles(serp)
        logger.info(f"Extracted {len(titles)} competitor titles")

        # Extract detailed organic results for analysis
        from services.parser import extract_organic_results, extract_paa_questions
        organic_results = extract_organic_results(serp)
        paa_questions = extract_paa_questions(serp)

        # Generate AI suggestions
        suggestions_data = suggest_better_titles(
            query=query,
            user_title=user_title,
            competitor_titles=titles
        )
        
        # Format the response with comprehensive data
        response_text = f"# SEO Title Analysis Results\n\n"
        response_text += f"**Query analyzed:** {query}\n"
        response_text += f"**Current title:** {user_title}\n"
        response_text += f"**Competitor titles found:** {len(titles)}\n"
        response_text += f"**Total organic results:** {len(organic_results)}\n"
        response_text += f"**People Also Ask questions:** {len(paa_questions)}\n\n"
        
        # Include People Also Ask section
        if paa_questions:
            response_text += "## People Also Ask Questions:\n\n"
            for i, question in enumerate(paa_questions, 1):
                response_text += f"{i}. {question}\n"
            response_text += "\n"
        
        # Include detailed competitor analysis
        response_text += "## Detailed Competitor Analysis:\n\n"
        for i, result in enumerate(organic_results[:10], 1):  # Top 10 results
            response_text += f"### Result #{i}\n"
            response_text += f"**Title:** {result.get('title', 'N/A')}\n"
            response_text += f"**URL:** {result.get('url', 'N/A')}\n"
            response_text += f"**Domain:** {result.get('url', '').split('/')[2] if result.get('url') else 'N/A'}\n"
            response_text += f"**Description:** {result.get('description', 'N/A')}\n"
            response_text += f"**Position:** {result.get('position', 'N/A')}\n\n"
        
        response_text += "\n## SEO Title Suggestions:\n\n"
        
        suggestions = suggestions_data.get("suggestions", [])
        if suggestions:
            for i, suggestion in enumerate(suggestions, 1):
                response_text += f"### Suggestion {i}\n"
                response_text += f"**Title:** {suggestion.get('title', 'N/A')}\n"
                response_text += f"**Meta Description:** {suggestion.get('description', 'N/A')}\n"
                response_text += f"**Rationale:** {suggestion.get('rationale', 'N/A')}\n\n"
        else:
            response_text += "No suggestions were generated. Please check your API configuration.\n"

        # Include raw data for further analysis
        response_text += "\n## Additional SERP Data for Analysis\n"
        response_text += f"**Total SERP results:** {serp.get('se_results_count', 'N/A')}\n"
        response_text += f"**Search performed:** {serp.get('datetime', 'N/A')}\n"
        response_text += f"**Location:** {serp.get('location_code', 'N/A')}\n"
        response_text += f"**Device:** {serp.get('device', 'N/A')}\n"
        
        # Include SERP features
        items = serp.get('items', [])
        serp_features = set()
        for item in items:
            if item.get('type') and item.get('type') != 'organic':
                serp_features.add(item.get('type'))
        
        if serp_features:
            response_text += f"**SERP Features present:** {', '.join(sorted(serp_features))}\n"
        
        # Add domain analysis data
        domains = [result.get('url', '').split('/')[2] for result in organic_results if result.get('url')]
        unique_domains = list(set(domains))
        response_text += f"**Unique domains ranking:** {len(unique_domains)}\n"
        
        # Include TLD analysis
        tlds = [domain.split('.')[-1] for domain in domains if domain and '.' in domain]
        tld_counts = {}
        for tld in tlds:
            tld_counts[tld] = tld_counts.get(tld, 0) + 1
        
        if tld_counts:
            response_text += f"**TLD distribution:** {dict(sorted(tld_counts.items(), key=lambda x: x[1], reverse=True))}\n"
        
        return [types.TextContent(type="text", text=response_text)]
        
    except Exception as e:
        import traceback
        logger.error(f"Error in analyze_title_tool: {str(e)}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
        
        # More detailed error for debugging
        error_text = f"Error analyzing title: {str(e)}\n\n"
        error_text += f"Query: {arguments.get('query', 'N/A')}\n"
        error_text += f"Full error details: {traceback.format_exc()}"
        
        return [types.TextContent(type="text", text=error_text)]

@server.list_resources()
async def handle_list_resources() -> List[Resource]:
    """List available resources"""
    return [
        Resource(
            uri=AnyUrl("file://data/payload.json"),
            name="Sample SERP Data",
            description="Sample SERP data for sweepstakes casinos keyword",
            mimeType="application/json"
        )
    ]

@server.read_resource()
async def handle_read_resource(uri: AnyUrl) -> str:
    """Read resource content"""
    if str(uri) == "file://data/payload.json":
        try:
            with open("data/payload.json", "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            raise RuntimeError(f"Error reading sample data: {str(e)}")
    else:
        raise ValueError(f"Unknown resource: {uri}")

async def main():
    """Run the MCP server"""
    # Import the stdio server runner
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