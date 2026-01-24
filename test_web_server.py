#!/usr/bin/env python3
"""Test script for the updated web server with city lookup."""

import asyncio
from cities import get_all_cities, get_city_coordinates

async def test_city_lookup():
    """Test the city lookup functionality."""
    print("Testing city lookup functionality...\n")
    
    # Test getting all cities
    cities = get_all_cities()
    print(f"Total cities loaded: {len(cities)}")
    print("First 10 cities:")
    for city in cities[:10]:
        print(f"  - {city}")
    
    print("\n" + "="*50 + "\n")
    
    # Test specific city lookups
    test_cities = [
        "San Francisco, CA",
        "London, UK", 
        "Tokyo, Japan",
        "Sydney, Australia",
        "New York City, NY"
    ]
    
    print("Testing specific city coordinates:")
    for city in test_cities:
        coords = get_city_coordinates(city)
        if coords:
            lat, lng = coords
            print(f"  {city}: {lat}, {lng}")
        else:
            print(f"  {city}: NOT FOUND")
    
    print("\n" + "="*50 + "\n")
    
    # Test forecast with city lookup
    from weather import get_forecast
    
    print("Testing forecast with San Francisco coordinates:")
    sf_coords = get_city_coordinates("San Francisco, CA")
    if sf_coords:
        lat, lng = sf_coords
        forecast = await get_forecast(lat, lng)
        print(f"Forecast for San Francisco ({lat}, {lng}):")
        print(forecast[:500] + "..." if len(forecast) > 500 else forecast)

if __name__ == "__main__":
    asyncio.run(test_city_lookup())