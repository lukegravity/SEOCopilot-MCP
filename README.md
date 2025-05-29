# SEO Copilot MCP Server

## Overview

SEO Copilot is an MCP (Model Context Protocol) server that provides SEO analysis and title suggestions based on SERP (Search Engine Results Page) data. It uses Claude via the Anthropic API to generate intelligent title and description recommendations.

## Features

- Fetch live SERP data using DataForSEO API
- Generate SEO title and description suggestions using Claude
- Provides an MCP-compatible server for integration with AI assistants

## Prerequisites

- Python 3.8+
- Anthropic API Key
- DataForSEO API Credentials

## Installation

1. Clone the repository
```bash
git clone https://github.com/lukegravity/SEOCopilot-MCP/seo-copilot-mcp.git
cd seo-copilot-mcp
```

2. Create a virtual environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
```

3. Install dependencies
```bash
pip install -r requirements.txt
```

4. Copy the example environment file and fill in your credentials
```bash
cp .env.example .env
```

5. Edit the `.env` file with your:
   - Anthropic API Key
   - DataForSEO API Login and Password
   - Optional location and language defaults

## Running the Server

```bash
uvicorn main:app --reload
```

The server will start on `http://localhost:8000`

## MCP Server Endpoints

- `/mcp`: Get server information
- `/mcp/tools/analyze_title`: Analyze and suggest improvements for a webpage title
- `/mcp/resources/sample_serp_data`: Access sample SERP data

## Configuration

The MCP server can be configured via the `mcp_config.json` file, which defines server connection details.

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

Distributed under the MIT License. See `LICENSE` for more information.

## Contact

Your Name - your.email@example.com

Project Link: [https://github.com/yourusername/seo-copilot-mcp](https://github.com/yourusername/seo-copilot-mcp)
