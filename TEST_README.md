# Weather MCP Server - Test Suite

This directory contains automated tests for the Weather MCP Server, focusing on dynamic city discovery and dropdown menu integration.

## Test Files

### `test_dynamic_cities.py`
Unit tests for the dynamic city addition functionality:
- ✅ Static cities appear in the cities list
- ✅ New cities are geocoded and cached correctly
- ✅ Dynamically added cities appear in `get_all_cities()`
- ✅ Multiple dynamic cities can be added
- ✅ Cities are not marked as "new" on subsequent fetches
- ✅ Static cities are never marked as "new"
- ✅ Dynamic cities persist in memory during the session
- ✅ Cities list includes both static and dynamic entries

### `test_web_integration.py`
Integration tests for the web API and dropdown functionality:
- ✅ `/api/cities` endpoint returns static cities
- ✅ Forecast requests add cities to the dynamic list
- ✅ `/api/city-coordinates` endpoint adds cities to the list
- ✅ Multiple dynamically added cities all appear
- ✅ Second request is not marked as "newly added"
- ✅ Cities list is returned in sorted order
- ✅ **Dropdown receives dynamically added cities** (key feature test)

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
uv run pytest --cov=cities --cov=web_server --cov-report=html
```

### Test Output

All tests should pass with output similar to:
```
============================= test session starts ==============================
test_dynamic_cities.py::TestDynamicCityAddition::test_static_city_in_list PASSED
test_dynamic_cities.py::TestDynamicCityAddition::test_new_city_geocoded_and_cached PASSED
...
test_web_integration.py::TestDropdownIntegration::test_dynamic_city_available_for_dropdown PASSED
============================== 15 passed in 13.49s =============================
```

## Key Test Scenarios

### Dropdown Integration Test
The most important test for the user requirement:

```python
def test_dynamic_city_available_for_dropdown(self, client):
    """Test end-to-end: Add city, verify it's in /api/cities for dropdown."""
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

## Dependencies

- `pytest>=8.0.0` - Test framework
- `pytest-asyncio>=0.23.0` - Async test support

## Continuous Testing

To watch for changes and re-run tests automatically:

```bash
uv run pytest-watch
```

## Notes

- Tests use fixtures to clear `DYNAMIC_CITIES` before each test to ensure isolation
- Integration tests use Flask's test client to simulate HTTP requests
- All async functions are tested with `@pytest.mark.asyncio`
- Tests verify both the caching mechanism and the API integration
