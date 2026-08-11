"""Tests for the MCP tool layer exposed over SSE (unified_server.py mounts
weather.mcp.sse_app()).

Rather than requiring a live server and a real SSE connection, these tests
exercise the same FastMCP tool-dispatch path (registration + `call_tool`)
in-process. That's what actually matters for correctness; the raw SSE
transport plumbing is framework code (Starlette/FastMCP), not app logic.
"""
import httpx

from weather import mcp


class TestToolRegistration:
    async def test_expected_tools_are_registered(self):
        tools = await mcp.list_tools()
        tool_names = {tool.name for tool in tools}

        assert "get_alerts" in tool_names
        assert "get_forecast" in tool_names


class TestToolDispatch:
    async def test_call_tool_get_alerts(self, mock_nws_alerts):
        mock_nws_alerts(state="NY", features=[])

        result = await mcp.call_tool("get_alerts", {"state": "NY"})

        assert len(result) == 1
        assert result[0].text == "No active alerts for this state."

    async def test_call_tool_get_forecast(self, mock_nws_forecast):
        mock_nws_forecast(
            40.7128,
            -74.0060,
            periods=[
                {
                    "name": "This Afternoon",
                    "temperature": 75,
                    "temperatureUnit": "F",
                    "windSpeed": "12 mph",
                    "windDirection": "S",
                    "detailedForecast": "Partly sunny.",
                }
            ],
        )

        result = await mcp.call_tool(
            "get_forecast", {"latitude": 40.7128, "longitude": -74.0060}
        )

        assert len(result) == 1
        assert "This Afternoon" in result[0].text
        assert "Partly sunny." in result[0].text
