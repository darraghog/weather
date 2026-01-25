# SSE Deployment Guide

This guide explains how to deploy the Weather MCP server with SSE (Server-Sent Events) transport for remote access via ngrok.

## Quick Start

### 1. Start the Unified Server

```bash
./start_server.sh
# or
uv run python unified_server.py
```

This starts a server on port 5000 with:
- **Web GUI**: http://localhost:5000
- **MCP SSE Endpoint**: http://localhost:5000/sse

### 2. Start ngrok Tunnel

In another terminal:

```bash
ngrok http 5000 --domain=carole-unrealizable-thermochemically.ngrok-free.dev
```

### 3. Test the SSE Endpoint

```bash
uv run python test_sse_endpoint.py
```

Or test via curl:

```bash
curl http://localhost:5000/sse
```

### 4. Configure MCP Clients

The configuration is already deployed to:
- **Windows**: `C:\users\darra\AppData\Roaming\mcp\mcp.json`
- **Local reference**: `mcp.json`

Configuration:
```json
{
  "mcpServers": {
    "weather": {
      "url": "https://carole-unrealizable-thermochemically.ngrok-free.dev/sse",
      "transport": "sse"
    }
  }
}
```

## Available Endpoints

### Web GUI
- Local: http://localhost:5000
- Remote: https://carole-unrealizable-thermochemically.ngrok-free.dev

### MCP SSE Endpoint
- Local: http://localhost:5000/sse
- Remote: https://carole-unrealizable-thermochemically.ngrok-free.dev/sse

### REST API (from web GUI)
- `POST /api/alerts` - Get weather alerts
- `POST /api/forecast` - Get weather forecast
- `GET /api/cities` - Get city list
- `POST /api/city-coordinates` - Get coordinates for a city

## MCP Tools Available

1. **get_alerts(state: str)**
   - Get weather alerts for a US state
   - Example: `get_alerts("CA")`

2. **get_forecast(latitude: float, longitude: float)**
   - Get weather forecast for any location worldwide
   - Example: `get_forecast(37.7749, -122.4194)`

## Troubleshooting

### 404 Error on /sse

If you're getting a 404 error:

1. **Verify the server is running** the `unified_server.py` (not `web_server.py`)
2. **Check the path** - It should be `/sse` NOT `/mcp/sse`
3. **Verify ngrok is tunneling to port 5000**

```bash
# Check what's running on port 5000
lsof -i :5000

# Should show unified_server.py or uvicorn
```

### Path Issues with Sub-mounting

FastMCP's `sse_app()` has a known issue when mounted under sub-paths (e.g., `/mcp/sse`). This is why we mount it at `/sse` directly. See:
- [Issue #464](https://github.com/modelcontextprotocol/python-sdk/issues/464)
- [fastmcp-mount middleware](https://github.com/dwayn/fastmcp-mount)

## Architecture

```
unified_server.py (Port 5000)
├── /sse → MCP SSE Endpoint (weather_mcp.sse_app())
└── /    → Flask Web GUI (wsgi_app)
    ├── /api/alerts
    ├── /api/forecast
    └── /api/cities
```

## Using with Different Clients

### Ollama
Place the mcp.json in the appropriate location for your OS, and Ollama will auto-discover the server.

### Claude Desktop
Add the configuration to your Claude Desktop config file:
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`
- Linux: `~/.config/Claude/claude_desktop_config.json`

### Custom Clients
Use any MCP-compatible client by pointing it to:
```
https://carole-unrealizable-thermochemically.ngrok-free.dev/sse
```

## Files

- `unified_server.py` - Main server combining Flask + MCP SSE
- `weather_sse.py` - Standalone MCP SSE server (alternative)
- `weather.py` - Original MCP server with stdio transport
- `web_server.py` - Original Flask-only server
- `start_server.sh` - Startup script
- `test_sse_endpoint.py` - Test script for SSE endpoint
