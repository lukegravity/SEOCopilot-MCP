from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
import json

from services.dataforseo import fetch_live_serp
from services.parser import extract_serp_titles
from services.title_rewrite import suggest_better_titles
from config import (
    DEFAULT_LOCATION_CODE,
    DEFAULT_LANGUAGE_CODE,
    DEFAULT_DEVICE,
    OPENAI_API_KEY,
)

# --- MCP SCHEMAS ---

class MCPToolParameter(BaseModel):
    name: str
    type: str
    description: str
    required: bool = False

class MCPToolSchema(BaseModel):
    name: str
    description: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]

class MCPResourceSchema(BaseModel):
    uri: str
    description: str

class MCPServerInfo(BaseModel):
    name: str
    description: str
    tools: List[MCPToolSchema]
    resources: List[MCPResourceSchema]

# --- TOOL INPUT/OUTPUT SCHEMAS ---

class AnalyzeTitleInput(BaseModel):
    query: str = Field(..., description="The search query to analyze")
    user_title: str = Field(..., description="The current title of the user's page")
    location_code: Optional[int] = Field(None, description="Location code for SERP data (default: US)")
    language_code: Optional[str] = Field(None, description="Language code for SERP data (default: en)")
    device: Optional[str] = Field(None, description="Device type for SERP data (default: desktop)")

class TitleSuggestion(BaseModel):
    title: str = Field(..., description="Suggested title")
    description: str = Field(..., description="Suggested meta description")
    rationale: str = Field(..., description="Rationale for the suggestion")

class AnalyzeTitleOutput(BaseModel):
    query: str = Field(..., description="The search query that was analyzed")
    user_title: str = Field(..., description="The current title of the user's page")
    competitor_titles: List[str] = Field(..., description="Titles of competing pages in search results")
    suggestions: List[TitleSuggestion] = Field(..., description="List of title suggestions with rationales")
    model_used: str = Field(..., description="The AI model used for generating suggestions")

# --- MCP SERVER IMPLEMENTATION ---

class MCPServer:
    def __init__(self):
        self.server_info = MCPServerInfo(
            name="SEO Copilot",
            description="An MCP server that provides SEO analysis and title suggestions based on SERP data",
            tools=[
                MCPToolSchema(
                    name="analyze_title",
                    description="Analyzes a webpage title and suggests improvements based on SERP data",
                    input_schema={
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "The search query to analyze"},
                            "user_title": {"type": "string", "description": "The current title of the user's page"},
                            "location_code": {"type": "integer", "description": "Location code for SERP data (default: US)"},
                            "language_code": {"type": "string", "description": "Language code for SERP data (default: en)"},
                            "device": {"type": "string", "description": "Device type for SERP data (default: desktop)"}
                        },
                        "required": ["query", "user_title"]
                    },
                    output_schema={
                        "type": "object",
                        "properties": {
                            "query": {"type": "string"},
                            "user_title": {"type": "string"},
                            "competitor_titles": {"type": "array", "items": {"type": "string"}},
                            "suggestions": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "title": {"type": "string"},
                                        "description": {"type": "string"},
                                        "rationale": {"type": "string"}
                                    }
                                }
                            },
                            "model_used": {"type": "string"}
                        }
                    }
                )
            ],
            resources=[
                MCPResourceSchema(
                    uri="sample_serp_data",
                    description="Sample SERP data for testing"
                )
            ]
        )

    def get_server_info(self) -> Dict:
        return self.server_info.dict()

    async def execute_tool(self, tool_name: str, arguments: Dict) -> Dict:
        if tool_name == "analyze_title":
            return await self._analyze_title(arguments)
        else:
            raise ValueError(f"Unknown tool: {tool_name}")

    async def get_resource(self, uri: str) -> Dict:
        if uri == "sample_serp_data":
            try:
                with open("data/serp-sample.json", "r") as f:
                    return json.load(f)
            except Exception as e:
                raise ValueError(f"Error loading sample SERP data: {str(e)}")
        else:
            raise ValueError(f"Unknown resource URI: {uri}")

    async def _analyze_title(self, arguments: Dict) -> Dict:
        # Validate input
        input_data = AnalyzeTitleInput(**arguments)
        
        # Resolve fallbacks
        location = input_data.location_code or DEFAULT_LOCATION_CODE
        language = input_data.language_code or DEFAULT_LANGUAGE_CODE
        device = input_data.device or DEFAULT_DEVICE

        try:
            # Fetch SERP
            serp = fetch_live_serp(
                keyword=input_data.query,
                location_code=location,
                language_code=language,
                device=device
            )

            # Extract titles
            titles = extract_serp_titles(serp)

            # Generate suggestions
            raw = suggest_better_titles(
                query=input_data.query,
                user_title=input_data.user_title,
                competitor_titles=titles
            )

            # Format suggestions
            structured_suggestions = [
                TitleSuggestion(
                    title=s.get("title", ""),
                    description=s.get("description", ""),
                    rationale=s.get("rationale", "")
                )
                for s in raw.get("suggestions", [])
            ]

            # Create output
            output = AnalyzeTitleOutput(
                query=input_data.query,
                user_title=input_data.user_title,
                competitor_titles=titles,
                suggestions=structured_suggestions,
                model_used="openai:gpt-4"
            )

            return output.dict()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error analyzing title: {str(e)}")

# Create FastAPI app with MCP server
app = FastAPI(title="SEO Copilot MCP Server")
mcp_server = MCPServer()

@app.get("/")
def root():
    return {"status": "SEO Copilot MCP Server running"}

@app.get("/mcp")
def get_mcp_info():
    return mcp_server.get_server_info()

@app.post("/mcp/tools/{tool_name}")
async def execute_tool(tool_name: str, request: Request):
    try:
        body = await request.json()
        arguments = body.get("arguments", {})
        result = await mcp_server.execute_tool(tool_name, arguments)
        return JSONResponse(content={"result": result})
    except ValueError as e:
        return JSONResponse(status_code=400, content={"error": str(e)})
    except HTTPException as e:
        return JSONResponse(status_code=e.status_code, content={"error": e.detail})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"Internal server error: {str(e)}"})

@app.get("/mcp/resources/{uri}")
async def get_resource(uri: str):
    try:
        resource = await mcp_server.get_resource(uri)
        return JSONResponse(content={"resource": resource})
    except ValueError as e:
        return JSONResponse(status_code=400, content={"error": str(e)})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"Internal server error: {str(e)}"})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
