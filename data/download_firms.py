"""
download_firms.py - Download FIRMS NRT thermal detection data for ThermoWatch demo regions.

Downloads VIIRS (SNPP + NOAA-20) and MODIS NRT data for the last few days
for each of the 4 demo regions: Jamnagar, Punjab, Uttarakhand, Angul.

We download two batches (days 1-5 and 1-5 offset via archive) to maximize coverage.
NRT API only supports day ranges of 1-5.

Usage:
    python data/download_firms.py
"""

import requests
import os
import sys
import time

MAP_KEY = "a0b0c81b602d5ff798ff79c2f573a242"
BASE = "https://firms.modaps.eosdis.nasa.gov/api/area/csv"

# Bounding boxes: west,south,east,north
regions = {
    "jamnagar":    "69.0,22.0,70.5,23.0",
    "punjab":      "74.0,29.5,77.0,31.5",
    "uttarakhand": "78.0,29.5,80.0,31.0",
    "angul":       "84.5,20.5,85.5,21.5",
}

sensors = ["VIIRS_SNPP_NRT", "VIIRS_NOAA20_NRT", "MODIS_NRT"]

# NRT API max is 5 days
DAY_RANGE = 5

# Ensure output directory exists
os.makedirs("data/raw", exist_ok=True)

success_count = 0
fail_count = 0

for name, bbox in regions.items():
    for sensor in sensors:
        url = f"{BASE}/{MAP_KEY}/{sensor}/{bbox}/{DAY_RANGE}"
        fname = f"data/raw/{name}_{sensor}_{DAY_RANGE}days.csv"
        print(f"Downloading: {name} / {sensor} ... ", end="", flush=True)
        try:
            r = requests.get(url, timeout=60)
            if r.status_code == 200 and not r.text.startswith("<!DOCTYPE") and "Invalid" not in r.text:
                with open(fname, "wb") as f:
                    f.write(r.content)
                # Count rows (subtract 1 for header)
                row_count = max(0, r.text.count("\n") - 1)
                print(f"OK -- {len(r.content):,} bytes, ~{row_count} rows -> {fname}")
                success_count += 1
            else:
                print(f"FAILED -- HTTP {r.status_code}, response: {r.text[:200]}")
                fail_count += 1
        except requests.exceptions.RequestException as e:
            print(f"ERROR -- {e}")
            fail_count += 1
        # Be polite to the API
        time.sleep(1)

print(f"\nDone. {success_count} succeeded, {fail_count} failed.")
if fail_count > 0:
    print("WARNING: Some downloads failed -- check your MAP_KEY or retry later.")
