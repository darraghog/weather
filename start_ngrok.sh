#!/bin/bash
# Start ngrok tunnel for the weather MCP server

echo "Starting ngrok tunnel on port 5000..."
echo "Domain: carole-unrealizable-thermochemically.ngrok-free.dev"
echo ""

# Check if unified server is running
if ! lsof -i :5000 >/dev/null 2>&1; then
    echo "WARNING: No server detected on port 5000"
    echo "Start the unified server first with: ./start_server.sh"
    echo ""
fi

ngrok http 5000 --domain=carole-unrealizable-thermochemically.ngrok-free.dev
