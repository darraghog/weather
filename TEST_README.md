# Weather MCP Server - Test Suite

Automated tests for the Weather MCP Server: the MCP tools (`weather.py`),
city lookup/geocoding (`cities.py`), and the Flask web API
(`web_server.py`/`unified_server.py`). All external HTTP calls (NWS,
Open-Meteo, Nominatim geocoding) are mocked - the suite runs fully offline
and deterministically.

## How mocking works

`conftest.py` defines an **autouse `respx_mock` fixture** active for every
test. It blocks any real HTTP request by default (respx raises
`AllMockedAssertionError` if a test forgets to mock a call it needs) - so a
test that requires network data must explicitly register a response.

Reusable fixtures for the common response shapes:

- `mock_geocode(lat, lon)` - any Nominatim geocoding lookup returns these coordinates.
- `mock_geocode_not_found` - Nominatim returns no results.
- `mock_nws_alerts(state, features)` - mocks the NWS active-alerts endpoint.
- `mock_nws_forecast(lat, lon, periods)` - mocks the NWS points -> forecast chain.
- `mock_open_meteo_forecast(overrides)` - mocks the Open-Meteo forecast endpoint.
- `web_server_client` / `unified_flask_client` - Flask test clients for the two server modules.
- `clear_dynamic_cities` (autouse) - resets `cities.DYNAMIC_CITIES` before/after every test, so dynamically-geocoded cities from one test never leak into another.

## Test Files

### `test_server.py`
Unit tests for `weather.py`'s MCP tools directly:
- `get_alerts()` - formatted output, no-alerts case, API-failure case.
- `get_forecast()` - NWS path for US coordinates, Open-Meteo fallback for non-US coordinates and when NWS has no data, and the all-sources-fail case.

### `test_web_server.py`
Tests the city-lookup -> forecast chain (`cities.py` + `weather.py` together):
- `get_all_cities()` / `get_city_coordinates()` for known static cities.
- End-to-end: a static city's coordinates feeding into `get_forecast()`.
- End-to-end: a newly geocoded (dynamic) city feeding into `get_forecast()`.

### `test_sse_endpoint.py`
Tests the MCP tool-dispatch layer in-process (no live server, no real SSE
connection needed): confirms `get_alerts`/`get_forecast` are registered on
`weather.mcp` and exercises them via `mcp.call_tool(...)`.

### `test_dynamic_cities.py`
Unit tests for dynamic city addition/caching in `cities.py`:
- Static cities appear in the cities list.
- New cities are geocoded and cached correctly.
- Dynamically added cities appear in `get_all_cities()`.
- Multiple dynamic cities can be added.
- Cities are not marked as "new" on subsequent fetches.
- Static cities are never marked as "new".
- Dynamic cities persist in memory during the session.

### `test_web_integration.py`
Integration tests for the web API and dropdown functionality:
- `/api/cities` endpoint returns static cities.
- Forecast requests add cities to the dynamic list.
- `/api/city-coordinates` endpoint adds cities to the list.
- Multiple dynamically added cities all appear.
- Second request is not marked as "newly added".
- Cities list is returned in sorted order.
- **Dropdown receives dynamically added cities** (key feature test).

### `test_dropdown_refresh.py`
End-to-end user-workflow tests: add a city via `/api/forecast`, then verify
it's immediately searchable via `/api/cities` under several search-term
variations (case-insensitive, partial match, etc.).

### `test_unified_server.py`
Smoke tests for `unified_server.py`'s Flask routes. `web_server.py` and
`unified_server.py` define the same routes as separate, copy-pasted
functions (not shared code), so exercising `web_server.py` elsewhere in the
suite does not cover `unified_server.py` - the module actually launched by
`start_server.sh`. This file gives it direct coverage of `/`, `/api/cities`,
`/api/alerts`, and `/api/forecast`.

## Running Tests

### Install Test Dependencies

```bash
cd weather
uv sync --extra dev
```

### Run All Tests

```bash
# Run all tests
uv run pytest -v

# Run specific test file
uv run pytest test_dynamic_cities.py -v

# Run specific test
uv run pytest test_dynamic_cities.py::TestDynamicCityAddition::test_new_city_geocoded_and_cached -v

# Run with coverage
uv run pytest --cov=weather --cov=cities --cov=web_server --cov=unified_server --cov-report=html
```

### Test Output

All tests pass with output similar to:
```
============================= test session starts ==============================
test_dynamic_cities.py::TestDynamicCityAddition::test_static_city_in_list PASSED
test_dynamic_cities.py::TestDynamicCityAddition::test_new_city_geocoded_and_cached PASSED
...
test_dropdown_refresh.py::TestDropdownRefresh::test_second_forecast_request_shows_city_in_dropdown PASSED
============================== 38 passed in 1.0s =============================
```

Since everything is mocked, the whole suite runs in well under a second -
there's no network latency to wait on.

## Continuous Integration

`.github/workflows/test.yml` runs the full suite (with coverage) on every
push and pull request via GitHub Actions, using `uv` for dependency
installation. No secrets or live network access are required since all
external calls are mocked.

## Key Test Scenario

The most important test for the dropdown-refresh user requirement:

```python
def test_dynamic_city_available_for_dropdown(self, client, mock_geocode, mock_open_meteo_forecast):
    """Test end-to-end: Add city, verify it's in /api/cities for dropdown."""
    mock_geocode(lat=..., lon=...)
    mock_open_meteo_forecast()

    # Step 1: User enters new city in web form
    response1 = client.post('/api/forecast', data=json.dumps({'city': test_city}))

    # Step 2: Frontend loads cities for dropdown
    response2 = client.get('/api/cities')
    cities_for_dropdown = json.loads(response2.data)['cities']

    # Step 3: Verify new city is available in dropdown
    assert test_city in cities_for_dropdown
```

This ensures that when a user:
1. Types a new city name (e.g., "Molde, Norway")
2. Gets the forecast (city is geocoded and cached)
3. Clicks back on the city field (frontend requests `/api/cities`)
4. **The new city appears in the autocomplete dropdown**

...all without touching the real Nominatim/Open-Meteo APIs.

## Dependencies

- `pytest>=8.0.0` - Test framework
- `pytest-asyncio>=0.23.0` - Async test support (config: `asyncio_mode = "auto"` in `pyproject.toml`, so `async def test_...` functions run automatically without needing an explicit marker)
- `pytest-cov>=5.0.0` - Coverage reporting
- `respx>=0.21.0` - HTTP mocking for `httpx` (used by `weather.py`/`cities.py`)

## Notes

- Tests use fixtures to clear `DYNAMIC_CITIES` before each test to ensure isolation (centralized in `conftest.py`, not duplicated per file).
- Integration tests use Flask's test client to simulate HTTP requests.
- All async test functions run under `asyncio_mode = "auto"`.
- No test hits a real external API - if you see a `respx.models.AllMockedAssertionError`, a code path is making an HTTP call that isn't mocked yet; add the appropriate `mock_*` fixture call.
