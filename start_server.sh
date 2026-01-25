#!/bin/bash
# Start the unified weather server (Web GUI + MCP SSE endpoint)

echo "Starting unified weather server on port 5000..."
echo "  - Web GUI: http://localhost:5000"
echo "  - MCP SSE endpoint: http://localhost:5000/sse"
echo ""
echo "To access via ngrok: https://carole-unrealizable-thermochemically.ngrok-free.dev"
echo "  - Web GUI: https://carole-unrealizable-thermochemically.ngrok-free.dev/"
echo "  - MCP SSE: https://carole-unrealizable-thermochemically.ngrok-free.dev/sse"
echo ""

cd "$(dirname "$0")"
uv run python unified_server.py
