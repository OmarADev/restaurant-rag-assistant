# fetch_restaurant.py
# Fetches real restaurant data from OpenStreetMap using Nominatim (geocoding)
# and the Overpass API (restaurant data). No API key required.
# Usage: python fetch_restaurant.py
# Output: saves restaurant data to data/<city_slug>/<restaurant_slug>/info.json

import requests
import json
import os
import re
import time

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
OVERPASS_URL = "https://overpass-api.de/api/interpreter"
HEADERS = {"User-Agent": "RestaurantRAG-Portfolio/1.0"}


def slugify(text):
    """Convert a string to a filesystem-safe slug."""
    return re.sub(r'[^a-z0-9]+', '_', text.lower()).strip('_')


def geocode_city(city):
    """Get lat/lon for a city name using Nominatim."""
    resp = requests.get(
        NOMINATIM_URL,
        params={"q": city, "format": "json", "limit": 1},
        headers=HEADERS,
        timeout=10
    )
    results = resp.json()
    if not results:
        raise ValueError(f"City not found: {city}")
    lat = float(results[0]["lat"])
    lon = float(results[0]["lon"])
    print(f"Found {city}: lat={lat:.4f}, lon={lon:.4f}")
    return lat, lon


def fetch_restaurants(lat, lon, radius_m=1000, limit=20):
    """Fetch restaurants near a lat/lon using Overpass API."""
    query = f"""
    [out:json][timeout:30];
    node[amenity=restaurant](around:{radius_m},{lat},{lon});
    out {limit};
    """
    resp = requests.post(OVERPASS_URL, data=query, headers=HEADERS, timeout=30)
    data = resp.json()
    elements = data.get("elements", [])

    restaurants = []
    for el in elements:
        tags = el.get("tags", {})
        name = tags.get("name")
        if not name:
            continue  # skip unnamed nodes
        restaurants.append({
            "name": name,
            "cuisine": tags.get("cuisine", "Not specified"),
            "opening_hours": tags.get("opening_hours", "Not available"),
            "phone": tags.get("phone", tags.get("contact:phone", "Not available")),
            "website": tags.get("website", tags.get("contact:website", "Not available")),
            "address": (
                f"{tags.get('addr:street', '')} {tags.get('addr:housenumber', '')}".strip()
                or "Not available"
            ),
            "lat": el.get("lat"),
            "lon": el.get("lon"),
        })

    return restaurants


def save_restaurant(city_slug, restaurant):
    """Save a single restaurant's data as info.json in its own folder."""
    r_slug = slugify(restaurant["name"])
    folder = os.path.join("data", city_slug, r_slug)
    os.makedirs(folder, exist_ok=True)

    out_path = os.path.join(folder, "info.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(restaurant, f, indent=2, ensure_ascii=False)

    return folder


def main():
    city = input("Enter a city name (e.g. Berlin, Munich, Hamburg): ").strip()
    if not city:
        print("No city entered. Exiting.")
        return

    print(f"\nGeocoding {city}...")
    lat, lon = geocode_city(city)

    print(f"Fetching restaurants near {city}...")
    time.sleep(1)  # be polite to Nominatim rate limits
    restaurants = fetch_restaurants(lat, lon)

    if not restaurants:
        print("No restaurants found. Try a larger city or check your connection.")
        return

    print(f"\nFound {len(restaurants)} restaurants:\n")
    for i, r in enumerate(restaurants):
        print(f"  [{i+1}] {r['name']} — {r['cuisine']}")

    city_slug = slugify(city)
    saved = 0
    for r in restaurants:
        folder = save_restaurant(city_slug, r)
        saved += 1

    print(f"\nSaved {saved} restaurants to data/{city_slug}/")
    print("You can now select one in the Streamlit app.")


if __name__ == "__main__":
    main()
