#!/usr/bin/env python3
"""Test that verifies dropdown refreshes after adding new cities."""

import pytest
import json
from web_server import app
from cities import DYNAMIC_CITIES


@pytest.fixture
def client():
    """Create a test client for the Flask app."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture(autouse=True)
def clear_dynamic_cities():
    """Clear dynamic cities before each test."""
    DYNAMIC_CITIES.clear()
    yield
    DYNAMIC_CITIES.clear()


class TestDropdownRefresh:
    """Test that the dropdown menu updates after adding new cities."""

    def test_galway_workflow(self, client):
        """Test the exact user workflow: Add Galway, then verify it's searchable."""
        test_city = "Galway, Ireland"

        # Step 1: User types "Galway, Ireland" and submits forecast
        print("\n=== Step 1: User submits forecast for Galway ===")
        response1 = client.post(
            '/api/forecast',
            data=json.dumps({'city': test_city}),
            content_type='application/json'
        )
        assert response1.status_code == 200
        data1 = json.loads(response1.data)

        print(f"Response: {data1['location']}")
        assert data1['location']['city'] == test_city
        assert data1['location']['newly_added'] is True
        print("✓ Galway was added successfully (newly_added: True)")

        # Step 2: Frontend refreshes cities list (simulating the loadCities() call)
        print("\n=== Step 2: Frontend refreshes cities list ===")
        response2 = client.get('/api/cities')
        assert response2.status_code == 200
        cities_list = json.loads(response2.data)['cities']

        print(f"Total cities in list: {len(cities_list)}")
        assert test_city in cities_list
        print(f"✓ Galway found in cities list")

        # Step 3: User types "galway" - simulate dropdown filter
        print("\n=== Step 3: User types 'galway' in search ===")
        search_term = "galway"
        matching_cities = [c for c in cities_list if search_term.lower() in c.lower()]

        print(f"Cities matching '{search_term}': {matching_cities}")
        assert len(matching_cities) > 0
        assert test_city in matching_cities
        print(f"✓ Galway appears in filtered dropdown results")

    def test_multiple_searches_after_adding_city(self, client):
        """Test that newly added city appears in multiple search variations."""
        test_city = "Cork, Ireland"

        # Add the city
        response1 = client.post(
            '/api/forecast',
            data=json.dumps({'city': test_city}),
            content_type='application/json'
        )
        assert response1.status_code == 200

        # Get cities list
        response2 = client.get('/api/cities')
        cities = json.loads(response2.data)['cities']

        # Test various search terms
        search_tests = [
            "cork",
            "Cork",
            "CORK",
            "ireland",
            "Cork, Ireland",
            "ork, Ir"  # partial match
        ]

        for search_term in search_tests:
            matches = [c for c in cities if search_term.lower() in c.lower()]
            assert test_city in matches, f"Search '{search_term}' should find {test_city}"
            print(f"✓ Search '{search_term}' found Cork")

    def test_city_persists_across_multiple_api_calls(self, client):
        """Test that dynamically added city remains available in subsequent API calls."""
        test_city = "Limerick, Ireland"

        # Add city via forecast
        client.post(
            '/api/forecast',
            data=json.dumps({'city': test_city}),
            content_type='application/json'
        )

        # Make multiple cities list requests
        for i in range(5):
            response = client.get('/api/cities')
            cities = json.loads(response.data)['cities']
            assert test_city in cities, f"City should be in list on request {i+1}"
            print(f"✓ Request {i+1}: City still in list")

    def test_second_forecast_request_shows_city_in_dropdown(self, client):
        """Test the complete workflow: add city, then search for it again."""
        test_city = "Waterford, Ireland"

        # First request - adds the city
        print("\n=== First request ===")
        response1 = client.post(
            '/api/forecast',
            data=json.dumps({'city': test_city}),
            content_type='application/json'
        )
        data1 = json.loads(response1.data)
        assert data1['location']['newly_added'] is True
        print(f"Added {test_city}, newly_added=True")

        # Simulate user clicking back on city field (loads dropdown)
        print("\n=== User clicks on city field ===")
        response2 = client.get('/api/cities')
        cities = json.loads(response2.data)['cities']
        assert test_city in cities
        print(f"✓ {test_city} available in dropdown")

        # User searches for the city again
        print("\n=== User types 'water' ===")
        matching = [c for c in cities if 'water' in c.lower()]
        print(f"Matching cities: {matching}")
        assert test_city in matching
        print(f"✓ {test_city} appears in search results")

        # User makes another forecast request
        print("\n=== User selects city from dropdown and submits ===")
        response3 = client.post(
            '/api/forecast',
            data=json.dumps({'city': test_city}),
            content_type='application/json'
        )
        data3 = json.loads(response3.data)
        assert data3['location']['newly_added'] is False  # Should not be "new" anymore
        print(f"Second request: newly_added=False (as expected)")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
