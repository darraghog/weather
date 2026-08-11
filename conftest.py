"""Shared pytest fixtures for the weather app test suite.

All HTTP calls are blocked by default via respx (`respx_mock` is autouse
below) - any test that needs network data must mock it explicitly with
one of the fixtures here, or a real request will raise
`respx.models.AllMockedAssertionError` instead of hitting the network.
"""
import httpx
import pytest
import respx

import cities as cities_module

NWS_API_BASE = "https://api.weather.gov"
OPEN_METEO_API_BASE = "https://api.open-meteo.com/v1"
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"


@pytest.fixture(autouse=True)
def respx_mock():
    """Active respx router for every test; blocks any unmocked real request."""
    with respx.mock(assert_all_called=False) as mock:
        yield mock


@pytest.fixture(autouse=True)
def clear_dynamic_cities():
    """Ensure cities.DYNAMIC_CITIES doesn't leak state between tests."""
    cities_module.DYNAMIC_CITIES.clear()
    yield
    cities_module.DYNAMIC_CITIES.clear()


@pytest.fixture
def web_server_client():
    """Flask test client for web_server.app."""
    from web_server import app

    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def unified_flask_client():
    """Flask test client for unified_server.flask_app."""
    from unified_server import flask_app

    flask_app.config["TESTING"] = True
    with flask_app.test_client() as client:
        yield client


@pytest.fixture
def mock_geocode(respx_mock):
    """Factory: mock_geocode(lat, lon) makes any Nominatim lookup return those coordinates."""

    def _mock(lat: float = 51.5074, lon: float = -0.1278):
        respx_mock.get(NOMINATIM_URL).mock(
            return_value=httpx.Response(200, json=[{"lat": str(lat), "lon": str(lon)}])
        )

    return _mock


@pytest.fixture
def mock_geocode_not_found(respx_mock):
    """Make any Nominatim lookup return no results (city not found)."""
    respx_mock.get(NOMINATIM_URL).mock(return_value=httpx.Response(200, json=[]))


@pytest.fixture
def mock_nws_alerts(respx_mock):
    """Factory: mock_nws_alerts(state, features) mocks the NWS active-alerts endpoint."""

    def _mock(state: str = "CA", features: list | None = None):
        respx_mock.get(f"{NWS_API_BASE}/alerts/active/area/{state}").mock(
            return_value=httpx.Response(200, json={"features": features if features is not None else []})
        )

    return _mock


@pytest.fixture
def mock_nws_forecast(respx_mock):
    """Factory: mock_nws_forecast(lat, lon, periods) mocks the NWS points+forecast chain."""

    def _mock(lat: float, lon: float, periods: list | None = None):
        forecast_url = f"{NWS_API_BASE}/gridpoints/MOCK/1,1/forecast"
        respx_mock.get(f"{NWS_API_BASE}/points/{lat},{lon}").mock(
            return_value=httpx.Response(200, json={"properties": {"forecast": forecast_url}})
        )
        default_periods = [
            {
                "name": "Today",
                "temperature": 70,
                "temperatureUnit": "F",
                "windSpeed": "5 mph",
                "windDirection": "NW",
                "detailedForecast": "Sunny.",
            }
        ]
        respx_mock.get(forecast_url).mock(
            return_value=httpx.Response(200, json={"properties": {"periods": periods or default_periods}})
        )

    return _mock


@pytest.fixture
def mock_open_meteo_forecast(respx_mock):
    """Factory: mock_open_meteo_forecast(overrides) mocks the Open-Meteo forecast endpoint."""

    def _mock(overrides: dict | None = None):
        payload = {
            "current_weather": {"temperature": 15.0, "windspeed": 10.0, "weathercode": 1},
            "daily": {
                "time": ["2026-08-11", "2026-08-12"],
                "temperature_2m_max": [20.0, 21.0],
                "temperature_2m_min": [10.0, 11.0],
                "precipitation_sum": [0.0, 0.1],
                "windspeed_10m_max": [12.0, 14.0],
                "weathercode": [1, 2],
            },
        }
        if overrides:
            payload.update(overrides)
        respx_mock.get(f"{OPEN_METEO_API_BASE}/forecast").mock(
            return_value=httpx.Response(200, json=payload)
        )

    return _mock
