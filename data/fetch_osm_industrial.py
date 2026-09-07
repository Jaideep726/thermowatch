"""
fetch_osm_industrial.py - Download industrial site locations from OpenStreetMap Overpass API.

Fetches refineries, factories, kilns, flares, and industrial land-use polygons
for the 4 ThermoWatch demo regions. Saves as JSON files in data/processed/.

Usage:
    python data/fetch_osm_industrial.py
"""

import requests
import json
import os
import time

os.makedirs("data/processed", exist_ok=True)

# Bounding boxes: (south, west, north, east) — Overpass format
regions = {
    "jamnagar":    (22.0, 69.0, 23.0, 70.5),
    "punjab":      (29.5, 74.0, 31.5, 77.0),
    "uttarakhand": (29.5, 78.0, 31.0, 80.0),
    "angul":       (20.5, 84.5, 21.5, 85.5),
}

OVERPASS_URL = "https://overpass-api.de/api/interpreter"

for name, (s, w, n, e) in regions.items():
    query = f"""
    [out:json][timeout:90];
    (
      way["landuse"="industrial"]({s},{w},{n},{e});
      relation["landuse"="industrial"]({s},{w},{n},{e});
      node["man_made"="works"]({s},{w},{n},{e});
      node["man_made"="flare"]({s},{w},{n},{e});
      node["industrial"="refinery"]({s},{w},{n},{e});
      node["industrial"="factory"]({s},{w},{n},{e});
      node["man_made"="petroleum_well"]({s},{w},{n},{e});
      way["industrial"="refinery"]({s},{w},{n},{e});
      way["industrial"="factory"]({s},{w},{n},{e});
    );
    out center;
    """

    print(f"Querying OSM for {name} ... ", end="", flush=True)
    try:
        headers = {"User-Agent": "ThermoWatch-Script/1.0", "Accept": "*/*"}
        r = requests.post(OVERPASS_URL, data={"data": query}, headers=headers, timeout=120)
        r.raise_for_status()
        data = r.json()

        sites = []
        for el in data["elements"]:
            lat, lon = None, None
            if "center" in el:
                lat, lon = el["center"]["lat"], el["center"]["lon"]
            elif "lat" in el:
                lat, lon = el["lat"], el["lon"]

            if lat is not None:
                tags = el.get("tags", {})
                sites.append({
                    "lat": lat,
                    "lon": lon,
                    "type": el.get("type"),
                    "osm_id": el.get("id"),
                    "name": tags.get("name", ""),
                    "landuse": tags.get("landuse", ""),
                    "man_made": tags.get("man_made", ""),
                    "industrial": tags.get("industrial", ""),
                })

        out_path = f"data/processed/{name}_osm_industrial.json"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(sites, f, indent=2, ensure_ascii=False)

        print(f"OK -- {len(sites)} industrial sites -> {out_path}")

    except Exception as e:
        print(f"ERROR -- {e}")

    # Be polite to Overpass
    time.sleep(5)

print("\nOSM download complete.")
