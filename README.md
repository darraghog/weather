# Weather MCP Server

A dual-interface weather application providing **worldwide weather forecasts** and **US weather alerts** through both a web GUI and MCP (Model Context Protocol) server interface.

![Architecture](https://img.shields.io/badge/Python-3.13+-blue.svg)
![Tests](https://img.shields.io/badge/tests-19%20passing-brightgreen.svg)
![Coverage](https://img.shields.io/badge/coverage-100%25-brightgreen.svg)

## Features

- 🌍 **Worldwide Weather Coverage** - Open-Meteo API for international locations, NWS for US
- 🏙️ **220+ Pre-configured Cities** - Major cities across all continents
- 🔍 **Dynamic City Discovery** - Automatically geocodes unknown cities via OpenStreetMap Nominatim
- 🌐 **Web GUI** - User-friendly interface with autocomplete city search
- 🤖 **MCP Server** - Integrates with AI assistants (Claude Desktop, ChatGPT Custom GPT)
- ⚡ **Smart Caching** - In-memory cache for geocoded cities
- 📊 **Comprehensive Tests** - 19 tests covering all functionality

## Table of Contents

- [Quick Start](#quick-start)
- [Installation](#installation)
- [Running Locally](#running-locally)
- [Deploying with ngrok](#deploying-with-ngrok)
- [LLM Client Integration](#llm-client-integration)
  - [Claude Desktop (MCP)](#claude-desktop-mcp)
  - [ChatGPT Custom GPT](#chatgpt-custom-gpt)
- [API Documentation](#api-documentation)
- [Testing](#testing)
- [Architecture](#architecture)

---

## Quick Start

```bash
# Clone the repository
git clone https://github.com/darraghog/weather.git
cd weather

# Install dependencies
uv sync

# Run the web server
uv run python web_server.py

# Visit http://localhost:5000 in your browser
```

---

## Installation

### Prerequisites

- **Python 3.13+**
- **uv** package manager ([installation guide](https://github.com/astral-sh/uv))
- **ngrok** (for public deployment) - [download here](https://ngrok.com/download)

### Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/darraghog/weather.git
   cd weather
   ```

2. **Install dependencies using uv:**
   ```bash
   uv sync
   ```

   This installs:
   - `fastmcp[cli]` - MCP server framework
   - `flask` - Web framework
   - `httpx` - Async HTTP client
   - `pytest`, `pytest-asyncio` - Testing

3. **Verify installation:**
   ```bash
   uv run pytest -v
   ```
   You should see: `19 passed`

---

## Running Locally

### Web Server (Flask)

Start the web interface on port 5000:

```bash
uv run python web_server.py
```

Access at: **http://localhost:5000**

The web GUI provides:
- City name search with autocomplete (220+ cities)
- Coordinate-based forecast lookup
- Dynamic city discovery with geocoding
- US weather alerts by state

### MCP Server (for AI Assistants)

Run the MCP server for Claude Desktop or other MCP clients:

```bash
uv run python weather.py
```

Or use the main entry point:

```bash
uv run python main.py
```

---

## Deploying with ngrok

ngrok creates a secure public tunnel to your local server, making it accessible from anywhere.

### Step 1: Install ngrok

**Option A - Download Binary:**
```bash
# Linux/WSL
wget https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-amd64.tgz
tar -xvzf ngrok-v3-stable-linux-amd64.tgz
chmod +x ngrok
```

**Option B - Package Manager:**
```bash
# macOS
brew install ngrok

# Linux (Snap)
snap install ngrok
```

### Step 2: Authenticate ngrok

1. **Sign up** at [ngrok.com](https://ngrok.com) (free tier available)
2. **Get your authtoken** from the dashboard
3. **Configure ngrok:**
   ```bash
   ./ngrok config add-authtoken YOUR_AUTHTOKEN_HERE
   ```

### Step 3: Start the Web Server

In one terminal:
```bash
cd weather
uv run python web_server.py
```

The server will start on **http://localhost:5000**

### Step 4: Create ngrok Tunnel

In another terminal:

```bash
./ngrok http 5000
```

**For a permanent custom domain** (ngrok paid plan):
```bash
./ngrok http 5000 --domain=your-custom-domain.ngrok-free.app
```

You'll see output like:
```
Forwarding  https://your-unique-url.ngrok-free.app -> http://localhost:5000
```

### Step 5: Update OpenAPI Configuration

If using with ChatGPT Custom GPT, update the server URL in `openapi.yaml`:

```yaml
servers:
  - url: https://your-unique-url.ngrok-free.app
    description: Production server (ngrok tunnel)
```

### ngrok Tips

- **Keep alive:** ngrok free tier sessions expire after 2 hours - restart the tunnel
- **Permanent domains:** Paid plans ($8/mo) provide permanent custom domains
- **Status page:** Visit http://localhost:4040 to see request logs and replay requests
- **Multiple tunnels:** Use `ngrok.yml` config file for multiple services

---

## LLM Client Integration

### Claude Desktop (MCP)

The MCP server provides two tools for Claude Desktop integration.

#### Configuration

1. **Locate Claude Desktop config:**
   - **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

2. **Add the weather server:**
   ```json
   {
     "mcpServers": {
       "weather": {
         "command": "uv",
         "args": [
           "--directory",
           "/absolute/path/to/weather",
           "run",
           "python",
           "weather.py"
         ]
       }
     }
   }
   ```

3. **Replace `/absolute/path/to/weather`** with your actual path:
   ```bash
   # Get the absolute path
   cd weather
   pwd
   ```

4. **Restart Claude Desktop**

#### Available MCP Tools

**1. get_forecast(latitude, longitude)**
- Get weather forecast for any location worldwide
- Returns 5-day forecast with current conditions
- Smart API selection (NWS for US, Open-Meteo for international)

**2. get_alerts(state)**
- Get active weather alerts for US states
- Takes two-letter state code (e.g., "CA", "NY")
- Returns detailed alert information

#### Usage Examples

In Claude Desktop, you can ask:

```
"What's the weather forecast for New York City?"
"Get weather alerts for California"
"What's the temperature in Tokyo, Japan?"
"Show me the forecast for 40.7128, -74.0060"
```

Claude will automatically use the MCP tools to fetch weather data.

---

### ChatGPT Custom GPT

Configure this application as a ChatGPT Custom GPT using the OpenAPI specification.

#### Prerequisites

- ChatGPT Plus subscription ($20/month)
- ngrok tunnel running (see [Deploying with ngrok](#deploying-with-ngrok))

#### Setup Instructions

1. **Start the web server and ngrok tunnel:**
   ```bash
   # Terminal 1
   uv run python web_server.py

   # Terminal 2
   ./ngrok http 5000
   ```

2. **Note your ngrok URL:**
   ```
   https://your-unique-url.ngrok-free.app
   ```

3. **Update `openapi.yaml`:**
   ```yaml
   servers:
     - url: https://your-unique-url.ngrok-free.app
       description: Production server
   ```

4. **Create Custom GPT:**
   - Go to [ChatGPT](https://chat.openai.com)
   - Click your profile → **My GPTs** → **Create a GPT**
   - Go to **Configure** tab

5. **Configure the GPT:**

   **Name:** `Weather Assistant`

   **Description:**
   ```
   Get real-time weather forecasts and alerts for any location worldwide.
   Supports city names, coordinates, and US weather alerts.
   ```

   **Instructions:**
   ```
   You are a helpful weather assistant that provides accurate weather forecasts
   and alerts using real-time data. You can:

   1. Get forecasts for any city worldwide by name (e.g., "Paris, France", "Tokyo, Japan")
   2. Get forecasts for specific coordinates (latitude/longitude)
   3. Get active weather alerts for US states using two-letter codes

   When providing forecasts:
   - Always mention the location name and coordinates
   - Format the weather data in a clear, readable way
   - Highlight any important weather conditions (storms, extreme temperatures, etc.)
   - If a city is newly added to the system, let the user know it's now cached for faster future lookups

   For weather alerts:
   - Summarize the severity and affected areas
   - Include any safety instructions provided
   ```

6. **Add Actions:**
   - Scroll to **Actions** section
   - Click **Create new action**
   - Select **Import from URL** or **Paste schema**

   **Option A - Import from URL:**
   ```
   https://your-unique-url.ngrok-free.app/openapi.yaml
   ```

   **Option B - Paste Schema:**
   Copy the entire contents of `openapi.yaml` and paste it

7. **Configure Authentication:**
   - Set to **None** (the API is public)

8. **Test the GPT:**
   - Click **Test** in the preview panel
   - Try: "What's the weather in London?"
   - Verify it calls your API

9. **Save and Publish:**
   - Click **Save**
   - Choose **Only me** or **Anyone with a link**

#### ChatGPT Usage Examples

```
"What's the weather forecast for Paris, France?"
"Get weather alerts for Texas"
"What's the temperature in Sydney, Australia?"
"Show me the forecast for coordinates 51.5074, -0.1278"
```

#### Troubleshooting ChatGPT Integration

- **"Action not available"** → Check ngrok tunnel is running
- **"Server not responding"** → Verify Flask server is running on port 5000
- **"Invalid schema"** → Validate `openapi.yaml` at [Swagger Editor](https://editor.swagger.io/)
- **Wrong location data** → Check `servers.url` in `openapi.yaml` matches ngrok URL

---

## API Documentation

### REST API Endpoints

#### `GET /`
Serves the web GUI (HTML interface)

#### `POST /api/forecast`
Get weather forecast for a location

**Request:**
```json
{
  "city": "Paris, France"
}
// OR
{
  "latitude": 48.8566,
  "longitude": 2.3522
}
```

**Response:**
```json
{
  "location": {
    "city": "Paris, France",
    "latitude": 48.8566,
    "longitude": 2.3522,
    "newly_added": false
  },
  "result": "Current Weather:\nTemperature: 45°F\n..."
}
```

#### `POST /api/alerts`
Get active US weather alerts

**Request:**
```json
{
  "state": "CA"
}
```

**Response:**
```json
{
  "result": "Event: High Wind Warning\nArea: San Francisco Bay Area\n..."
}
```

#### `GET /api/cities`
Get list of all available cities

**Response:**
```json
{
  "cities": ["Auckland, New Zealand", "Bangkok, Thailand", ...]
}
```

#### `POST /api/city-coordinates`
Geocode a city name to coordinates

**Request:**
```json
{
  "city": "Dublin, Ireland"
}
```

**Response:**
```json
{
  "city": "Dublin, Ireland",
  "latitude": 53.3498,
  "longitude": -6.2603,
  "newly_added": false
}
```

### MCP Tools

#### `get_forecast(latitude: float, longitude: float) -> str`
Get weather forecast for coordinates

**Example:**
```python
result = await get_forecast(40.7128, -74.0060)
```

#### `get_alerts(state: str) -> str`
Get weather alerts for a US state

**Example:**
```python
result = await get_alerts("CA")
```

---

## Testing

### Run All Tests

```bash
uv run pytest -v
```

### Test Suites

1. **test_dynamic_cities.py** (8 tests)
   - City caching logic
   - Static/dynamic city integration
   - `newly_added` flag behavior

2. **test_web_integration.py** (7 tests)
   - API endpoint integration
   - Forecast request flow
   - City list updates

3. **test_dropdown_refresh.py** (4 tests)
   - Dropdown refresh workflow
   - City search functionality
   - Persistence across requests

### Run Specific Test File

```bash
uv run pytest test_dynamic_cities.py -v
```

### Test Coverage

```bash
uv run pytest --cov=. --cov-report=html
```

View coverage report: `open htmlcov/index.html`

---

## Architecture

### High-Level Overview

```
┌─────────────────┐
│  Web Browser    │
│  Claude Desktop │
│  ChatGPT GPT    │
└────────┬────────┘
         │
    ┌────┴─────┐
    │          │
┌───▼──┐   ┌──▼────┐
│ Flask│   │  MCP  │
│  API │   │Server │
└───┬──┘   └──┬────┘
    │         │
    └────┬────┘
         │
┌────────▼─────────┐
│ Business Logic   │
│ - City Geocoding │
│ - Weather Fetch  │
│ - Smart Caching  │
└────────┬─────────┘
         │
    ┌────┴────┐
    │         │
┌───▼──┐  ┌──▼────┐  ┌──────┐
│ NWS  │  │Open   │  │Nomin-│
│ API  │  │Meteo  │  │atim  │
└──────┘  └───────┘  └──────┘
```

### Key Components

- **Web Server Layer** - Flask REST API + HTML frontend
- **MCP Server Layer** - FastMCP tools for AI assistants
- **Business Logic** - Three-tier city lookup (dynamic → static → geocoding)
- **HTTP Client Layer** - Unified API request handling
- **External APIs** - NWS (US), Open-Meteo (worldwide), Nominatim (geocoding)

### Data Flow

1. User requests forecast for "Galway, Ireland"
2. Check dynamic cache → Not found
3. Check static cities (220+) → Not found
4. Geocode via Nominatim → (53.2744, -9.0491)
5. Cache coordinates in memory
6. Detect international location → Use Open-Meteo API
7. Return formatted forecast + location info
8. Frontend refreshes city list (dropdown now includes Galway)

See [architecture.md](architecture.md) for complete technical specifications.

---

## Project Structure

```
weather/
├── weather.py              # MCP server with forecast tools
├── web_server.py           # Flask web application
├── cities.py               # City geocoding and caching
├── main.py                 # Simple entry point
├── openapi.yaml            # OpenAPI spec for ChatGPT
├── pyproject.toml          # Dependencies and config
├── README.md               # This file
├── architecture.md         # Complete technical specification
├── CONSOLIDATION_SUMMARY.md # Code consolidation details
├── DROPDOWN_FIX.md         # Dropdown refresh implementation
├── TEST_README.md          # Testing documentation
├── templates/
│   └── index.html          # Web GUI (HTML/CSS/JS)
├── test_dynamic_cities.py      # Unit tests (8 tests)
├── test_web_integration.py     # Integration tests (7 tests)
├── test_dropdown_refresh.py    # Dropdown tests (4 tests)
└── test_web_server.py          # Basic web server tests
```

---

## Performance

- **Initial load:** < 1 second
- **City search:** Instant (client-side filtering)
- **Geocoding:** ~500ms (first time only, then cached)
- **Weather fetch:** 1-3 seconds (API dependent)
- **Cache hit:** < 10ms (in-memory)

---

## External APIs

### National Weather Service (NWS)
- **Coverage:** United States only
- **Rate Limits:** Generous, no hard limits
- **Authentication:** None (User-Agent required)
- **Docs:** https://www.weather.gov/documentation/services-web-api

### Open-Meteo
- **Coverage:** Worldwide
- **Rate Limits:** 10,000 requests/day (free tier)
- **Authentication:** None
- **Docs:** https://open-meteo.com/en/docs

### OpenStreetMap Nominatim
- **Coverage:** Worldwide geocoding
- **Rate Limits:** 1 request/second
- **Authentication:** None (User-Agent required)
- **Docs:** https://nominatim.org/release-docs/develop/api/Overview/

---

## Security Considerations

⚠️ **Current Status:** Development mode - NOT production-ready

**Current Limitations:**
- Flask debug mode enabled (remote code execution risk)
- No rate limiting (vulnerable to abuse)
- No request size limits
- In-memory cache unbounded (memory leak)
- Bare exception handling (silent failures)
- No logging infrastructure

**See:** [CONSOLIDATION_SUMMARY.md](CONSOLIDATION_SUMMARY.md) for detailed production readiness analysis.

**Before Production:**
1. Use production WSGI server (gunicorn/uwsgi)
2. Implement rate limiting (Flask-Limiter)
3. Add structured logging
4. Implement cache eviction (TTL, max size)
5. Add proper error handling
6. Enable HTTPS
7. Add monitoring/metrics

---

## Troubleshooting

### "Module not found" errors
```bash
# Ensure you're using uv to run commands
uv sync
uv run python web_server.py
```

### Web server won't start
```bash
# Check if port 5000 is already in use
lsof -i :5000
# Kill the process or use a different port
```

### MCP tools not appearing in Claude Desktop
1. Verify config path is correct (absolute path)
2. Check Claude Desktop logs: `~/Library/Logs/Claude/`
3. Restart Claude Desktop completely
4. Test server manually: `uv run python weather.py`

### Geocoding not working
- Check internet connection (Nominatim requires external API)
- Verify User-Agent is set (required by Nominatim TOS)
- Rate limit: 1 request/second (wait between requests)

### ngrok tunnel keeps expiring
- Free tier: 2-hour sessions, need to restart
- Upgrade to paid plan ($8/mo) for permanent domains
- Use `ngrok http 5000 --domain=your-domain.ngrok-free.app`

---

## Acknowledgments

- **National Weather Service** - US weather data
- **Open-Meteo** - Worldwide weather API
- **OpenStreetMap Nominatim** - Geocoding service
- **FastMCP** - Model Context Protocol framework
- **Flask** - Web framework

---

## Contact

**Author:** Darragh O'Grady
**GitHub:** [@darraghog](https://github.com/darraghog)
**Repository:** https://github.com/darraghog/weather

---

## Version History

### v2.0.0 (Current)
- ✨ Added web GUI with autocomplete city search
- 🌍 Worldwide weather support via Open-Meteo
- 🔍 Dynamic city discovery with geocoding
- 📚 Comprehensive documentation and architecture
- ✅ 19 automated tests
- 🎨 Code consolidation (-60 lines duplicate code)

### v1.0.0
- 🚀 Initial release
- 🇺🇸 US-only weather via NWS API
- 🤖 MCP server for Claude Desktop
