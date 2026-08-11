"""Regression test for the MCP Streamable HTTP endpoint mounted in
unified_server.py.

unified_server.py merges routes from weather_mcp.streamable_http_app() into
its own Starlette app, which means it must also carry its own `lifespan`
that enters weather_mcp.session_manager.run() - the sub-app's lifespan is
not invoked automatically just because its routes were merged in. Forgetting
that wiring makes every /mcp request fail with "Task group is not
initialized". This test exercises the real ASGI app (lifespan included) to
catch that class of bug.

It also covers the bearer-token auth check on /mcp (see
_BearerAuthASGIApp in unified_server.py): requests are rejected with 401
when WEATHER_MCP_TOKEN is set and the Authorization header is missing or
wrong, on both routing entries into the MCP app (the bare "/mcp" Route and
the "/mcp/..." Mount), and allowed through - including mid-session, not
just on initialize - once the correct header is supplied. When the token
env var is unset, /mcp stays open, matching today's default behavior.

StreamableHTTPSessionManager.run() can only be entered once per process
(weather_mcp is a module-level singleton), so this file deliberately uses a
single TestClient `with` block across one test function rather than
per-test fixtures. The auth assertions below toggle WEATHER_MCP_TOKEN with
monkeypatch mid-block instead, since the auth check re-reads the
environment on every request rather than caching it at import time.
"""
from starlette.testclient import TestClient

from unified_server import app


def test_mcp_endpoint_auth_and_tools_list(monkeypatch):
    monkeypatch.setenv("WEATHER_MCP_TOKEN", "test-secret-token")

    init_payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2025-06-18",
            "capabilities": {},
            "clientInfo": {"name": "test-client", "version": "0"},
        },
    }
    base_headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
    }

    with TestClient(app) as client:
        # No Authorization header at all -> 401 on the bare "/mcp" Route.
        no_auth_response = client.post("/mcp", json=init_payload, headers=base_headers)
        assert no_auth_response.status_code == 401
        assert no_auth_response.json()["error"] == "unauthorized"
        assert no_auth_response.headers.get("www-authenticate") == "Bearer"

        # Same, but against the trailing-slash Mount entry - proves the
        # single in-place wrap in unified_server.py covers both routing
        # paths into the MCP app, not just the bare-path Route.
        no_auth_slash_response = client.post("/mcp/", json=init_payload, headers=base_headers)
        assert no_auth_slash_response.status_code == 401

        # Wrong token -> 401.
        wrong_token_response = client.post(
            "/mcp",
            json=init_payload,
            headers={**base_headers, "Authorization": "Bearer wrong-token"},
        )
        assert wrong_token_response.status_code == 401

        # Correct token -> the existing initialize/notify/tools-list flow.
        auth_headers = {**base_headers, "Authorization": "Bearer test-secret-token"}

        init_response = client.post("/mcp", json=init_payload, headers=auth_headers)
        assert init_response.status_code == 200

        session_id = init_response.headers.get("mcp-session-id")
        assert session_id

        # The MCP spec requires this notification before any further request
        # on the session, or the server rejects it as "before initialization
        # was complete".
        notify_response = client.post(
            "/mcp",
            json={"jsonrpc": "2.0", "method": "notifications/initialized"},
            headers={**auth_headers, "mcp-session-id": session_id},
        )
        assert notify_response.status_code == 202

        tools_list_payload = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {},
        }

        tools_response = client.post(
            "/mcp",
            json=tools_list_payload,
            headers={**auth_headers, "mcp-session-id": session_id},
        )
        assert tools_response.status_code == 200

        # Same authenticated session, but drop the header -> still 401.
        # Proves enforcement isn't only checked on initialize.
        mid_session_no_auth = client.post(
            "/mcp",
            json=tools_list_payload,
            headers={**base_headers, "mcp-session-id": session_id},
        )
        assert mid_session_no_auth.status_code == 401

        # Unset the token entirely -> default-open behavior is restored.
        monkeypatch.delenv("WEATHER_MCP_TOKEN", raising=False)
        open_response = client.post(
            "/mcp",
            json=tools_list_payload,
            headers={**base_headers, "mcp-session-id": session_id},
        )
        assert open_response.status_code == 200
