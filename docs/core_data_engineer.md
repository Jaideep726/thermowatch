# Core Data Engineer Notes

## TASK 1 - FIRMS Download
- **Tech stack used & why**: Python with `requests` library to fetch CSV data from the NASA FIRMS NRT API. Standard HTTP request because it's straightforward. Handled API limits by adding small delays between requests.
- **Important findings**: FIRMS NRT API only supports up to a 5-day window (`DAY_RANGE=5`), not 10 days as initially thought. NRT data provided very few rows (only ~207 active detections across 4 regions in September), with Uttarakhand yielding 0 rows since it is not wildfire season. This makes manual archive downloading strictly necessary for training data.
- **Problems encountered**: Had to fix a Windows `cp1252` encoding issue when printing emojis to stdout. Fixed by removing the emoji and standardizing string format.
- **Data files produced**: `data/raw/*_NRT_5days.csv` (12 files) - NRT satellite readings.

## TASK 2 - OSM Industrial Sites
- **Tech stack used & why**: Overpass API with `requests.post`. Extended the tags beyond the baseline spec to include `industrial=refinery`, `industrial=factory`, and `man_made=petroleum_well` to ensure Jamnagar's massive refinery complex was fully captured. 
- **Important findings**: The Overpass API rate-limited us with HTTP 429 and 406 errors when fetching all 4 regions concurrently. Also discovered Overpass strictly requires an `Accept: */*` and a descriptive `User-Agent` header for POST requests to avoid 406 Not Acceptable errors.
- **Problems encountered & how solved**: Uttarakhand and Angul timed out or were blocked due to rate limits. I wrote a fallback script `fetch_missing.py` to target just those two missing regions with an increased timeout, which completed successfully.
- **Data files produced**: `data/processed/*_osm_industrial.json` (4 files) - lists of `{lat, lon}` for every known industrial point in our demo regions.

## TASK 3 - LULC Lookup
- **Tech stack used & why**: Manual lookup table. Setting up MODIS MCD12Q1 with GIS software was too heavyweight for a fast hackathon sprint, so I built a simplified bounding-box rule set mapping coordinates to dominant land cover classes via `lulc_lookup.csv`.
- **Important findings**: Used distance-to-industrial thresholds (e.g. `< 5km` around Jamnagar and Angul) to classify `industrial` vs `cropland/forest` to keep it simple but accurate enough for weak supervision.
- **Data files produced**: `data/processed/lulc_lookup.csv` - Simple manual region-to-LULC mapping.

## TASK 4 - Weak-supervision labeling
- **Tech stack used & why**: `pandas` for vectorized data manipulation, pure Python `haversine` formula for distance calculation (avoids installing heavy geospatial libraries like `geopandas` or `shapely` for a hackathon).
- **Important findings**: The heuristics successfully label data based on proximity to the OSM industrial points we downloaded and the LULC lookup. The pipeline correctly leaves points as "uncertain" if they don't strongly match the rules.
- **Data files produced**: `data/processed/firms_labeled.csv` - The final, weakly-labeled dataset ready for the ML Engineer to extract temporal features from.
