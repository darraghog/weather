#!/bin/bash
# Start the unified weather server (Web GUI + MCP Streamable HTTP endpoint)

echo "Starting unified weather server on port 5000..."
echo "  - Web GUI: http://localhost:5000"
echo "  - MCP endpoint: http://localhost:5000/mcp"
echo ""
echo "To access via ngrok: https://carole-unrealizable-thermochemically.ngrok-free.dev"
echo "  - Web GUI: https://carole-unrealizable-thermochemically.ngrok-free.dev/"
echo "  - MCP endpoint: https://carole-unrealizable-thermochemically.ngrok-free.dev/mcp"
echo ""

cd "$(dirname "$0")"
if [ -f .env ]; then
  set -a
  . ./.env
  set +a
fi
uv run python unified_server.py
