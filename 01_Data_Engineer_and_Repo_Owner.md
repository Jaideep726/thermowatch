# Task PRD — Person 1: Data Engineer (+ Repo Owner)

**Your job in one line:** You get all the raw fuel (FIRMS + OSM + land-cover data) and you're also the one who sets up the shared house (the Git repo) everyone else moves into.

**You are Task 0 for the whole team.** Nobody can meaningfully start until your repo exists and your data starts landing. Move fast on tasks 1–2, don't wait for perfection.

---

## Before you start
- Install Python 3.10+ and `git` on your machine.
- Create a free GitHub account if you don't have one.
- Create a free NASA FIRMS account: https://firms.modaps.eosdis.nasa.gov/api/map_key/ (takes minutes, sometimes hours to approve — do this literally first, before reading further).

---

## TASK 0 — Create the shared Git repo (do this first, today)

1. On GitHub, create a new **public or private repo** named `thermowatch`.
2. On your machine, run:
   ```bash
   git clone https://github.com/<your-org-or-username>/thermowatch.git
   cd thermowatch
   ```
3. Create this exact folder structure:
   ```
   thermowatch/
   ├── data/
   │   ├── raw/
   │   └── processed/
   ├── ml/
   │   └── models/
   ├── backend/
   ├── frontend-globe/
   ├── frontend-dashboard/
   ├── integration/
   ├── docs/
   └── README.md
   ```
   Quick way to do it:
   ```bash
   mkdir -p data/raw data/processed ml/models backend frontend-globe frontend-dashboard integration docs
   touch README.md
   ```
4. In `README.md`, paste a one-paragraph project description (copy the "Problem Statement" section from the PRD) plus this note: `See /docs for each team member's core.md notes.`
5. Add a `.gitignore` with at least:
   ```
   __pycache__/
   *.pyc
   .env
   .venv/
   node_modules/
   *.csv
   ```
   (We ignore `.csv` so we don't accidentally commit huge data files — you'll share data via a shared drive link in your `core.md` instead, or commit small sample CSVs only.)
6. Commit and push:
   ```bash
   git add .
   git commit -m "chore: initial repo structure"
   git push origin main
   ```
7. **Share the repo link with all 5 teammates immediately.** They all run `git clone` next.

✅ **Checkpoint:** Repo exists, structure is visible on GitHub, everyone has the link.

---

## TASK 1 — Download FIRMS data for all 4 demo regions

**What you're doing:** pulling raw satellite thermal-detection data for our 4 test regions, both recent (NRT) and historical (archive), so the ML person has something to train on.

1. In `data/`, create a script `download_firms.py`:
   ```python
   import requests

   MAP_KEY = "YOUR_KEY_HERE"  # from FIRMS registration email
   BASE = "https://firms.modaps.eosdis.nasa.gov/api/area/csv"

   regions = {
       "jamnagar":    "69.0,22.0,70.5,23.0",
       "punjab":      "74.0,29.5,77.0,31.5",
       "uttarakhand": "78.0,29.5,80.0,31.0",
       "angul":       "84.5,20.5,85.5,21.5",
   }

   for name, bbox in regions.items():
       for sensor in ["VIIRS_SNPP_NRT", "VIIRS_NOAA20_NRT", "MODIS_NRT"]:
           url = f"{BASE}/{MAP_KEY}/{sensor}/{bbox}/10"
           r = requests.get(url)
           fname = f"data/raw/{name}_{sensor}_10days.csv"
           open(fname, "wb").write(r.content)
           print(f"Downloaded: {fname} ({len(r.content)} bytes)")
   ```
2. Run it: `python download_firms.py`
3. Also manually download **archive data** (6–12 months) for the same 4 regions from https://firms.modaps.eosdis.nasa.gov/download/ — save into `data/raw/` as `<region>_archive.csv`.
4. Commit (small files only — if archive files are huge, DON'T push the CSVs; instead note the download link/steps in your `core.md` so teammates can re-download):
   ```bash
   git add download_firms.py data/raw/*.csv
   git commit -m "feat(data): FIRMS NRT + archive data for 4 regions"
   git push
   ```

✅ **Checkpoint:** 4 regions × NRT data downloaded, archive data downloaded, script committed.

---

## TASK 2 — Get OSM industrial site locations (Overpass API)

**What you're doing:** getting the lat/lon of every refinery, kiln, and factory in our regions, so we can later say "this hot spot is 300m from a known factory."

1. Create `data/fetch_osm_industrial.py`:
   ```python
   import requests, json

   regions = {
       "jamnagar":    (22.0, 69.0, 23.0, 70.5),
       "punjab":      (29.5, 74.0, 31.5, 77.0),
       "uttarakhand": (29.5, 78.0, 31.0, 80.0),
       "angul":       (20.5, 84.5, 21.5, 85.5),
   }

   for name, (s, w, n, e) in regions.items():
       query = f"""
       [out:json][timeout:60];
       (
         way["landuse"="industrial"]({s},{w},{n},{e});
         relation["landuse"="industrial"]({s},{w},{n},{e});
         node["man_made"="works"]({s},{w},{n},{e});
         node["man_made"="flare"]({s},{w},{n},{e});
       );
       out center;
       """
       r = requests.post("https://overpass-api.de/api/interpreter", data={"data": query})
       data = r.json()
       sites = []
       for el in data["elements"]:
           if "center" in el:
               sites.append({"lat": el["center"]["lat"], "lon": el["center"]["lon"]})
           elif "lat" in el:
               sites.append({"lat": el["lat"], "lon": el["lon"]})
       with open(f"data/processed/{name}_osm_industrial.json", "w") as f:
           json.dump(sites, f)
       print(f"{name}: {len(sites)} industrial sites found")
   ```
2. Run it: `python fetch_osm_industrial.py`
3. Commit & push:
   ```bash
   git add data/fetch_osm_industrial.py data/processed/*_osm_industrial.json
   git commit -m "feat(data): OSM industrial site locations for 4 regions"
   git push
   ```

✅ **Checkpoint:** 4 JSON files with industrial site coordinates exist and are pushed.

---

## TASK 3 — Land cover (LULC) lookup for each region

**What you're doing:** for each region, get a simple "is this forest, cropland, urban, or barren" answer per rough grid cell — this lets us later say "this hot spot is in a forest" vs "in a field."

1. If you have GIS tools available, download MODIS MCD12Q1 for India from NASA Earthdata and extract land-cover class per 0.01° grid cell for the 4 bounding boxes.
2. **If that's too slow to set up (it's fine — this is the most technical task):** build a simplified manual lookup table instead. Create `data/processed/lulc_lookup.csv` with columns `region, lat_min, lat_max, lon_min, lon_max, land_cover_class`, and hand-fill rows using Google Maps satellite view for each region (e.g., Jamnagar refinery zone = `industrial`, surrounding area = `cropland`; Uttarakhand region = `forest`; Punjab = `cropland`).
3. Document in your `core.md` which method you used and why (this matters — the PRD explicitly says be honest about shortcuts taken).
4. Commit & push:
   ```bash
   git add data/processed/lulc_lookup.csv
   git commit -m "feat(data): land cover lookup for 4 demo regions"
   git push
   ```

✅ **Checkpoint:** A land-cover lookup file exists, method is documented.

---

## TASK 4 — Weak-supervision labeling function

**What you're doing:** since we have no manually labeled fires, we write rules that guess the label using ONLY location/context features (never sensor features — that's the ML engineer's job to keep separate).

1. Create `data/label_data.py`. Use the rules from PRD Section 5.1 (Design Decision A table). Copy the `auto_label()` function logic:
   - Uses `dist_to_industrial`, `land_cover_class`, `month`, `latitude` — labeling-only features.
   - Outputs one of: `industrial`, `crop_burning`, `wildfire`, `false_positive`, `uncertain`.
2. Merge your FIRMS CSVs + OSM distances + LULC lookup into one dataframe, apply `auto_label()`, save as `data/processed/firms_labeled.csv`.
3. Print and note in `core.md`: what % of rows got a real label vs `uncertain`.
4. Commit & push:
   ```bash
   git add data/label_data.py data/processed/firms_labeled.csv
   git commit -m "feat(data): weak-supervision labeling pipeline"
   git push
   ```

✅ **Checkpoint:** Labeled dataset exists — this is what the ML Engineer (Person 2) needs to start training.

---

## Your `core.md` file

Create `docs/core_data_engineer.md`. Every time you finish a task or hit something notable, append (don't overwrite) a short entry with:
- **Tech stack used & why** (e.g., "Used `requests` + Overpass API instead of a paid GIS tool because it's free and needs no API key")
- **Important findings** (e.g., "Angul has very few OSM industrial tags — had to add NALCO/JSPL manually")
- **Problems encountered & how you solved them** (e.g., "FIRMS archive download times out for >6 months — split into 2 requests")
- **Features/data files and how they work** (a one-line description of each file you produced)

Keep entries short and factual — this file's whole purpose is so teammates can read it later and understand your part without asking you.

---

> **Note for AI coding agents assisting with this task:** Only make code changes, run commands, or take actions autonomously if you are 95%+ confident they are correct and match what's described above. If you are below that confidence threshold, stop and ask the user a clarifying question instead of guessing.
