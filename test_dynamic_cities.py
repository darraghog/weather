#!/usr/bin/env python3
"""Tests for dynamic city discovery and dropdown menu integration."""

import pytest
import asyncio
from cities import get_city_coordinates, get_all_cities, DYNAMIC_CITIES, MAJOR_CITIES


class TestDynamicCityAddition:
    """Test that dynamically added cities appear in search results."""

    @pytest.fixture(autouse=True)
    def clear_dynamic_cities(self):
        """Clear dynamic cities before each test."""
        DYNAMIC_CITIES.clear()
        yield
        DYNAMIC_CITIES.clear()

    def test_static_city_in_list(self):
        """Test that static cities appear in the cities list."""
        cities = get_all_cities()
        assert "London, UK" in cities
        assert "Tokyo, Japan" in cities
        assert "Summit, NJ" in cities

    @pytest.mark.asyncio
    async def test_new_city_geocoded_and_cached(self):
        """Test that a new city gets geocoded and cached."""
        # Pick a city likely not in the static list
        test_city = "Inverness, Scotland"

        # Verify city is not in static list initially
        assert test_city not in MAJOR_CITIES, "Test city should not be in static list"

        # Get initial list
        initial_cities = get_all_cities()
        assert test_city not in initial_cities, "Test city should not be in initial list"

        # Get coordinates (should geocode and cache)
        coords_result, newly_added = await get_city_coordinates(test_city)

        assert coords_result is not None, "City should be geocoded successfully"
        assert newly_added is True, "City should be marked as newly added"
        assert test_city in DYNAMIC_CITIES, "City should be in dynamic cache"

    @pytest.mark.asyncio
    async def test_dynamic_city_appears_in_list(self):
        """Test that dynamically added cities appear in get_all_cities()."""
        test_city = "Tromso, Norway"

        # Get initial list
        initial_cities = get_all_cities()
        initial_count = len(initial_cities)

        # Add new city through geocoding
        coords_result, newly_added = await get_city_coordinates(test_city)

        assert coords_result is not None, "City should be geocoded"

        # Get updated list
        updated_cities = get_all_cities()

        assert len(updated_cities) > initial_count, "City count should increase"
        assert test_city in updated_cities, "New city should appear in cities list"

    @pytest.mark.asyncio
    async def test_multiple_dynamic_cities(self):
        """Test that multiple dynamically added cities all appear in the list."""
        test_cities = [
            "Aalborg, Denmark",
            "Trondheim, Norway",
            "Oulu, Finland"
        ]

        # Add cities
        for city in test_cities:
            await get_city_coordinates(city)

        # Verify all appear in the list
        all_cities = get_all_cities()
        for city in test_cities:
            assert city in all_cities, f"{city} should be in the cities list"

    @pytest.mark.asyncio
    async def test_dynamic_city_not_marked_new_on_second_fetch(self):
        """Test that a cached city is not marked as newly_added on subsequent fetches."""
        test_city = "Kiruna, Sweden"

        # First fetch - should be new
        coords1, newly_added1 = await get_city_coordinates(test_city)
        assert newly_added1 is True, "First fetch should mark as newly added"

        # Second fetch - should not be new
        coords2, newly_added2 = await get_city_coordinates(test_city)
        assert newly_added2 is False, "Second fetch should not mark as newly added"
        assert coords1 == coords2, "Coordinates should be the same"

    @pytest.mark.asyncio
    async def test_static_city_not_marked_as_new(self):
        """Test that static cities are never marked as newly_added."""
        static_city = "Paris, France"

        coords, newly_added = await get_city_coordinates(static_city)

        assert coords is not None, "Static city should have coordinates"
        assert newly_added is False, "Static city should not be marked as new"

    def test_dynamic_cities_persist_in_memory(self):
        """Test that dynamic cities remain available during the session."""
        # Manually add a city to dynamic cache
        test_city = "Test City, TestLand"
        test_coords = (12.3456, 78.9012)
        DYNAMIC_CITIES[test_city] = test_coords

        # Verify it appears in the cities list
        all_cities = get_all_cities()
        assert test_city in all_cities, "Manually added city should appear in list"

    def test_cities_list_includes_both_static_and_dynamic(self):
        """Test that get_all_cities() returns both static and dynamic cities."""
        # Add a dynamic city
        dynamic_city = "Dynamic Test City"
        DYNAMIC_CITIES[dynamic_city] = (1.0, 2.0)

        all_cities = get_all_cities()

        # Should include static cities
        assert "London, UK" in all_cities
        assert "Tokyo, Japan" in all_cities

        # Should include dynamic city
        assert dynamic_city in all_cities


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
