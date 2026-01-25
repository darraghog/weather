#!/usr/bin/env python3
"""Test script to verify the SSE endpoint is accessible."""

import asyncio
import httpx

async def test_sse_endpoint():
    """Test the SSE endpoint."""
    url = "http://localhost:5000/sse"

    print(f"Testing SSE endpoint at {url}...")

    async with httpx.AsyncClient() as client:
        try:
            # Test basic connectivity
            response = await client.get(url, timeout=5.0)
            print(f"Status Code: {response.status_code}")
            print(f"Headers: {response.headers}")

            if response.status_code == 200:
                print("✓ SSE endpoint is accessible!")
            else:
                print(f"✗ Unexpected status code: {response.status_code}")
                print(f"Response: {response.text[:200]}")

        except httpx.ConnectError:
            print("✗ Connection failed. Is the server running?")
            print("  Start the server with: ./start_server.sh")
        except Exception as e:
            print(f"✗ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_sse_endpoint())
