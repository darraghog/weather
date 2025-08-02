#!/usr/bin/env python3
"""Simple test script for the weather MCP server."""

import asyncio
from weather import get_alerts, get_forecast

async def test_server():
    """Test the weather server functions directly."""
    print("Testing weather server functions...\n")
    
    # Test get_alerts
    print("Testing get_alerts for California (CA):")
    alerts = await get_alerts("CA")
    print(alerts)
    print("\n" + "="*50 + "\n")
    
    # Test get_forecast for San Francisco coordinates
    print("Testing get_forecast for San Francisco (37.7749, -122.4194):")
    forecast = await get_forecast(37.7749, -122.4194)
    print(forecast)

if __name__ == "__main__":
    asyncio.run(test_server())