#!/usr/bin/env python3
"""Unified server combining Flask web GUI and MCP SSE endpoint."""

import asyncio
import contextlib
import logging
import os
from secrets import compare_digest
from typing import Any, Coroutine
from flask import Flask, render_template, request, jsonify
from weather import get_alerts, get_forecast, mcp as weather_mcp
from cities import get_all_cities, get_city_coordinates
from asgiref.wsgi import WsgiToAsgi
from starlette.applications import Starlette
from starlette.datastructures import Headers
from starlette.responses import JSONResponse
from starlette.routing import Mount, Route
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware

# Create Flask app
flask_app = Flask(__name__)

def run_async(coro: Coroutine) -> Any:
    """Run an async coroutine in a new event loop (for Flask sync context).

    Args:
        coro: The coroutine to run

    Returns:
        The result of the coroutine
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()

@flask_app.route('/')
def index():
    """Serve the main web interface."""
    return render_template('index.html')

@flask_app.route('/api/alerts', methods=['POST'])
def api_alerts():
    """API endpoint for weather alerts."""
    try:
        data = request.get_json()
        state = data.get('state', '').upper()

        if not state or len(state) != 2:
            return jsonify({'error': 'Please provide a valid 2-letter state code (e.g., CA, NY)'}), 400

        result = run_async(get_alerts(state))
        return jsonify({'result': result})

    except Exception as e:
        return jsonify({'error': f'Error fetching alerts: {str(e)}'}), 500

@flask_app.route('/api/cities', methods=['GET'])
def api_cities():
    """API endpoint to get all available cities."""
    try:
        cities = get_all_cities()
        return jsonify({'cities': cities})
    except Exception as e:
        return jsonify({'error': f'Error fetching cities: {str(e)}'}), 500

@flask_app.route('/api/city-coordinates', methods=['POST'])
def api_city_coordinates():
    """API endpoint to get coordinates for a specific city."""
    try:
        data = request.get_json()
        city = data.get('city', '').strip()

        if not city:
            return jsonify({'error': 'Please provide a city name'}), 400

        coords_result, newly_added = run_async(get_city_coordinates(city))
        if coords_result:
            latitude, longitude = coords_result
            return jsonify({
                'city': city,
                'latitude': latitude,
                'longitude': longitude,
                'newly_added': newly_added
            })
        else:
            return jsonify({'error': f'Could not find coordinates for "{city}"'}), 404

    except Exception as e:
        return jsonify({'error': f'Error fetching coordinates: {str(e)}'}), 500

@flask_app.route('/api/forecast', methods=['POST'])
def api_forecast():
    """API endpoint for weather forecast."""
    try:
        data = request.get_json()
        city = data.get('city')
        latitude = data.get('latitude')
        longitude = data.get('longitude')

        city_name = None
        was_newly_added = False

        # If city is provided, get coordinates from city lookup (with geocoding)
        if city:
            coords_result, newly_added = run_async(get_city_coordinates(city))
            if coords_result:
                latitude, longitude = coords_result
                city_name = city
                was_newly_added = newly_added
            else:
                return jsonify({'error': f'Could not find or geocode city "{city}"'}), 400

        if latitude is None or longitude is None:
            return jsonify({'error': 'Please provide either a city or both latitude and longitude'}), 400

        try:
            lat = float(latitude)
            lng = float(longitude)
        except ValueError:
            return jsonify({'error': 'Latitude and longitude must be valid numbers'}), 400

        if not (-90 <= lat <= 90) or not (-180 <= lng <= 180):
            return jsonify({'error': 'Invalid coordinates. Latitude: -90 to 90, Longitude: -180 to 180'}), 400

        result = run_async(get_forecast(lat, lng))

        response_data = {
            'result': result,
            'location': {
                'city': city_name,
                'latitude': lat,
                'longitude': lng,
                'newly_added': was_newly_added
            }
        }

        return jsonify(response_data)

    except Exception as e:
        return jsonify({'error': f'Error fetching forecast: {str(e)}'}), 500

# Convert Flask app to ASGI
wsgi_app = WsgiToAsgi(flask_app)

# Get MCP Streamable HTTP app - it has a route at /mcp.
# This also lazily creates weather_mcp's StreamableHTTPSessionManager.
mcp_app = weather_mcp.streamable_http_app()

# Create combined Starlette app
# Mount MCP app at root so /mcp is accessible
# Then mount Flask app to catch remaining routes
middleware = [
    Middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["mcp-session-id"],
    )
]


@contextlib.asynccontextmanager
async def lifespan(app):
    # streamable_http_app()'s own lifespan starts the session manager's task
    # group; merging only its routes (below) drops that lifespan, so we have
    # to re-enter it here or every /mcp request fails with
    # "Task group is not initialized".
    async with weather_mcp.session_manager.run():
        yield


# mcp_app.routes is just [Mount("/mcp", app=handle_streamable_http)]. A Mount's
# path-matching regex requires a literal "/" after the prefix, so it never
# matches the bare "/mcp" (no trailing slash) - only "/mcp/...". Without an
# explicit exact-path route, bare "/mcp" falls through to the Flask catch-all
# Mount below (which matches any path) and 404s there instead of reaching MCP.
mcp_mount = mcp_app.routes[0]

logger = logging.getLogger(__name__)

WEATHER_MCP_TOKEN_ENV_VAR = "WEATHER_MCP_TOKEN"

if not os.environ.get(WEATHER_MCP_TOKEN_ENV_VAR):
    logger.warning(
        "%s is not set - the /mcp endpoint has NO auth and is open to "
        "anyone with the URL. Set %s in the environment (e.g. in a local "
        ".env sourced by start_server.sh) before exposing this server "
        "remotely to require a bearer token on /mcp. Generate one with: "
        "python -c \"import secrets; print(secrets.token_urlsafe(32))\"",
        WEATHER_MCP_TOKEN_ENV_VAR, WEATHER_MCP_TOKEN_ENV_VAR,
    )


class _BearerAuthASGIApp:
    """Requires `Authorization: Bearer <token>` on every request to the
    wrapped app, scoped only to whatever it wraps.

    Applied only to mcp_mount.app below (shared by both the bare "/mcp"
    Route and the "/mcp/..." Mount) - never to the Flask-mounted routes,
    which don't hold a reference to this class at all.

    Reads WEATHER_MCP_TOKEN from the environment on every call (not cached
    at import time) so it stays open by default for local dev when unset,
    and so tests can toggle it with monkeypatch without reimporting this
    module (weather_mcp's session manager is a singleton that can only be
    started once per process - see test_mcp_http_endpoint.py).
    """

    def __init__(self, app):
        self._app = app

    async def __call__(self, scope, receive, send):
        token = os.environ.get(WEATHER_MCP_TOKEN_ENV_VAR)
        if scope["type"] != "http" or not token:
            # No token configured -> auth disabled (open), matches local-dev
            # default. Non-http scopes (lifespan) always pass through.
            await self._app(scope, receive, send)
            return

        if scope["method"] == "OPTIONS":
            # Real CORS preflights never reach here (CORSMiddleware, which
            # wraps this whole app, answers them itself - see
            # starlette.middleware.cors.CORSMiddleware.__call__). This is a
            # defensive no-op for any other OPTIONS request.
            await self._app(scope, receive, send)
            return

        headers = Headers(scope=scope)
        auth_header = headers.get("authorization", "")
        expected = f"Bearer {token}"
        # Compare as bytes: Starlette decodes headers latin-1, and
        # secrets.compare_digest raises TypeError on non-ASCII str input,
        # which would turn a malformed header into a 500 instead of a 401.
        if not compare_digest(auth_header.encode("utf-8"), expected.encode("utf-8")):
            response = JSONResponse(
                {
                    "error": "unauthorized",
                    "message": "Missing or invalid bearer token. Provide an "
                    "'Authorization: Bearer <token>' header.",
                },
                status_code=401,
                headers={"WWW-Authenticate": "Bearer"},
            )
            await response(scope, receive, send)
            return

        await self._app(scope, receive, send)


# Wrap once, in place: both the explicit Route("/mcp", ...) below and the
# Mount("/mcp/...") itself read mcp_mount.app, so this single wrap covers
# both routing entries into the MCP app. This line MUST run before the
# Route("/mcp", ...) below is constructed, since Route captures
# mcp_mount.app by value - moving this after that line would silently
# leave bare "/mcp" unauthenticated. It never touches Mount("/", wsgi_app)
# (the Flask app), which holds no reference to this wrapper.
mcp_mount.app = _BearerAuthASGIApp(mcp_mount.app)


class _ASGIEndpoint:
    """Route() treats a plain function endpoint as `func(request) -> response`;
    wrapping it in a callable class makes Route treat it as a raw ASGI app
    instead, matching handle_streamable_http's real (scope, receive, send)
    signature."""

    def __init__(self, app):
        self._app = app

    async def __call__(self, scope, receive, send):
        await self._app(scope, receive, send)


app = Starlette(
    routes=[
        Route("/mcp", endpoint=_ASGIEndpoint(mcp_mount.app), methods=["GET", "POST", "DELETE"]),
        mcp_mount,
        Mount("/", wsgi_app),
    ],
    middleware=middleware,
    lifespan=lifespan,
)

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=5000)
