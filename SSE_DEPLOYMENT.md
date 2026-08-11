# MCP Deployment Guide

This guide explains how to deploy the Weather MCP server with Streamable HTTP transport for remote access via ngrok.

## Quick Start

### 1. Start the Unified Server

```bash
./start_server.sh
# or
uv run python unified_server.py
```

This starts a server on port 5000 with:
- **Web GUI**: http://localhost:5000
- **MCP Endpoint**: http://localhost:5000/mcp

### 2. Start ngrok Tunnel

In another terminal:

```bash
ngrok http 5000 --domain=carole-unrealizable-thermochemically.ngrok-free.dev
```

### 3. Test the MCP Endpoint

```bash
uv run pytest test_mcp_http_endpoint.py -v
```

Or test via curl:

```bash
curl -X POST http://localhost:5000/mcp \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json, text/event-stream' \
  -H 'Authorization: Bearer <token>' \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"curl","version":"0"}}}'
```

The `Authorization` header is only required once `WEATHER_MCP_TOKEN` is set on the server (see [Authentication](#authentication-bearer-token-on-mcp-only) below). If it's unset, omit the header entirely.

### 4. Configure MCP Clients

The configuration is already deployed to:
- **Windows**: `C:\users\darra\AppData\Roaming\mcp\mcp.json`
- **Local reference**: `mcp.json`

Configuration:
```json
{
  "mcpServers": {
    "weather": {
      "url": "https://carole-unrealizable-thermochemically.ngrok-free.dev/mcp",
      "transport": "streamable-http",
      "headers": {
        "Authorization": "Bearer <token>"
      }
    }
  }
}
```

`headers` is only needed once `WEATHER_MCP_TOKEN` is set on the server. The
local `mcp.json` in this repo keeps a `<REPLACE_WITH_WEATHER_MCP_TOKEN>`
placeholder since it's git-tracked — put the real token only in untracked,
locally-deployed copies (e.g. the Windows path above), never in the
committed file.

## Available Endpoints

### Web GUI
- Local: http://localhost:5000
- Remote: https://carole-unrealizable-thermochemically.ngrok-free.dev

### MCP Endpoint
- Local: http://localhost:5000/mcp
- Remote: https://carole-unrealizable-thermochemically.ngrok-free.dev/mcp
- Requires `Authorization: Bearer <token>` when `WEATHER_MCP_TOKEN` is set on the server (see [Authentication](#authentication-bearer-token-on-mcp-only)); open otherwise.

### REST API (from web GUI)
- `POST /api/alerts` - Get weather alerts
- `POST /api/forecast` - Get weather forecast
- `GET /api/cities` - Get city list
- `POST /api/city-coordinates` - Get coordinates for a city
- Always unauthenticated, regardless of `WEATHER_MCP_TOKEN` — used by the local web GUI's browser JS and the ChatGPT/GPT-Actions integration, neither of which send an auth header.

## Authentication (bearer token on /mcp only)

The `/mcp` endpoint supports an optional bearer token. The web GUI (`/`) and
`/api/*` stay public in all cases — this only ever gates `/mcp`.

1. Generate a token:
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```
2. Set it in the server's environment before starting, e.g. in a local
   `.env` file (already gitignored) next to `unified_server.py`:
   ```
   WEATHER_MCP_TOKEN=<generated-token>
   ```
   `start_server.sh` sources `.env` automatically if present. You can also
   `export WEATHER_MCP_TOKEN=...` directly in the shell that runs the server.
3. Restart the server. If the variable is unset, `/mcp` stays fully open
   (today's default) and the server logs a startup warning saying so — this
   keeps local dev working with zero setup.
4. Once set, every request to `/mcp` needs `Authorization: Bearer <token>`
   or it gets a `401` with a `WWW-Authenticate: Bearer` header.

**Supplying the token per client:**
- **curl / scripts:** `-H 'Authorization: Bearer <token>'`.
- **Claude Desktop:** the file-based `mcp.json`/config supports a `headers`
  field on the server entry, shown above.
- **Perplexity:** use its connector's custom-header field the same way, if
  the version you're on exposes one.
- **claude.ai web "Add custom connector" UI:** this form may only expose a
  URL field, with no way to attach a custom header. It's also possible that
  seeing `WWW-Authenticate: Bearer` on the 401 makes it attempt OAuth
  discovery instead of prompting for a static token, since that header is
  the standard signal for OAuth-protected resources — this server doesn't
  implement OAuth. **Known limitation:** the bearer-token approach is
  expected to work for Claude Desktop, curl, and Perplexity (if it supports
  headers), but may not work through claude.ai's web connector UI as-is.

**Rollout note:** the live ngrok-tunneled server and any connector configs
pointing at it should be updated together. Set the env var and restart the
server first, verify with curl, *then* update `mcp.json` / Claude Desktop
config / Perplexity config with the real token — otherwise clients get 401s
in the gap between the two.

## MCP Tools Available

1. **get_alerts(state: str)**
   - Get weather alerts for a US state
   - Example: `get_alerts("CA")`

2. **get_forecast(latitude: float, longitude: float)**
   - Get weather forecast for any location worldwide
   - Example: `get_forecast(37.7749, -122.4194)`

## Troubleshooting

### 404 Error on /mcp

If you're getting a 404 error:

1. **Verify the server is running** the `unified_server.py` (not `web_server.py`)
2. **Check the path** - It should be `/mcp`
3. **Verify ngrok is tunneling to port 5000**

```bash
# Check what's running on port 5000
lsof -i :5000

# Should show unified_server.py or uvicorn
```

### 500 Error / "Task group is not initialized"

This means the MCP session manager's lifespan wasn't started. `unified_server.py` merges routes
from `weather_mcp.streamable_http_app()` into its own `Starlette` app, so it must also carry a
`lifespan` that enters `weather_mcp.session_manager.run()` itself — the sub-app's own lifespan is
not invoked automatically just because its routes were merged in. If you see this error, check
that `unified_server.py`'s `Starlette(...)` call still passes `lifespan=lifespan`.

## Architecture

```
unified_server.py (Port 5000)
├── /mcp → MCP Endpoint (weather_mcp.streamable_http_app())
└── /    → Flask Web GUI (wsgi_app)
    ├── /api/alerts
    ├── /api/forecast
    └── /api/cities
```

Sessions are tracked in-memory by a single `StreamableHTTPSessionManager` (stateful mode, the
default). This is correct for the current deployment — one `uvicorn` process behind ngrok, so
every request reaches the same session table. If this is ever scaled out to multiple workers or
processes, either switch to `stateless_http=True` or ensure sticky routing to the same process,
otherwise requests can intermittently fail with "No valid session ID provided".

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
https://carole-unrealizable-thermochemically.ngrok-free.dev/mcp
```
Add an `Authorization: Bearer <token>` header if `WEATHER_MCP_TOKEN` is set on the server — see [Authentication](#authentication-bearer-token-on-mcp-only).

## Files

- `unified_server.py` - Main server combining Flask + MCP Streamable HTTP
- `weather.py` - Original MCP server with stdio transport
- `web_server.py` - Original Flask-only server
- `start_server.sh` - Startup script
- `test_mcp_http_endpoint.py` - Regression test for the mounted MCP endpoint
