"""
label_data.py - Weak-supervision labeling function for ThermoWatch.

Merges raw FIRMS CSVs, computes distance to OSM industrial sites,
looks up land cover, and assigns a weak label based on domain heuristics.
"""

import pandas as pd
import glob
import json
import numpy as np
import math

def haversine(lat1, lon1, lat2, lon2):
    # Calculate distance in km
    R = 6371.0
    lat1_rad, lon1_rad = math.radians(lat1), math.radians(lon1)
    lat2_rad, lon2_rad = math.radians(lat2), math.radians(lon2)
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def load_osm_sites():
    sites = []
    for f in glob.glob("data/processed/*_osm_industrial.json"):
        with open(f, "r", encoding="utf-8") as file:
            data = json.load(file)
            sites.extend(data)
    return sites

def auto_label(row):
    dist = row.get("dist_to_industrial", 999)
    land_cover = row.get("land_cover_class", "unknown")
    month = int(row["acq_date"].split("-")[1])
    
    if dist < 2.0:
        return "industrial"
    elif land_cover == "cropland" and month in [10, 11, 4, 5]:
        return "crop_burning"
    elif land_cover == "forest":
        return "wildfire"
    elif dist > 10 and land_cover == "unknown" and row.get("frp", 0) < 1.0:
        return "false_positive"
    return "uncertain"

def main():
    print("Loading raw CSVs...")
    # Recursively find all CSV files
    csv_files = glob.glob("data/raw/**/*.csv", recursive=True)
    # Also include the files we downloaded originally
    csv_files.extend(glob.glob("data/raw/*.csv"))
    # Remove duplicates if any
    csv_files = list(set(csv_files))
    
    if not csv_files:
        print("No CSV files found in data/raw/. Please ensure FIRMS data is downloaded.")
        return
    
    df_list = []
    for f in csv_files:
        try:
            df = pd.read_csv(f)
            # Infer region from filename or filepath
            f_lower = f.lower().replace("\\", "/")
            region = "unknown"
            for r in ["jamnagar", "punjab", "uttarakhand", "angul"]:
                if f"/{r}/" in f_lower or f"{r}_" in f_lower:
                    region = r
                    break
            df["region"] = region
            df_list.append(df)
        except Exception as e:
            print(f"Failed to read {f}: {e}")
            
    if not df_list:
        return
        
    df = pd.concat(df_list, ignore_index=True)
    print(f"Loaded {len(df)} records.")
    
    print("Computing distances to industrial sites...")
    osm_sites = load_osm_sites()
    
    # Fast vectorized Haversine in chunks to save memory and run in ~1 second on CPU
    osm_lats = np.array([s["lat"] for s in osm_sites])
    osm_lons = np.array([s["lon"] for s in osm_sites])
    df_lats = df["latitude"].values
    df_lons = df["longitude"].values

    R = 6371.0
    osm_lat_rad = np.radians(osm_lats)
    osm_lon_rad = np.radians(osm_lons)
    
    dist_to_ind = np.zeros(len(df))
    chunk_size = 10000
    for i in range(0, len(df), chunk_size):
        chunk_lat = np.radians(df_lats[i:i+chunk_size])[:, np.newaxis]
        chunk_lon = np.radians(df_lons[i:i+chunk_size])[:, np.newaxis]
        
        dlat = osm_lat_rad - chunk_lat
        dlon = osm_lon_rad - chunk_lon
        
        a = np.sin(dlat / 2)**2 + np.cos(chunk_lat) * np.cos(osm_lat_rad) * np.sin(dlon / 2)**2
        c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
        distances = R * c
        
        dist_to_ind[i:i+chunk_size] = np.min(distances, axis=1)
        
    df["dist_to_industrial"] = dist_to_ind
    
    print("Applying LULC lookup...")
    lulc = pd.read_csv("data/processed/lulc_lookup.csv")
    
    # Simple mapping by region since we built a simplified LULC table
    def get_lulc(row):
        region = row["region"]
        region_lulc = lulc[lulc["region"] == region]
        if not region_lulc.empty:
            # If there's multiple, pick the first or based on region defaults
            if region == "punjab": return "cropland"
            if region == "uttarakhand": return "forest"
            if region == "jamnagar": return "industrial" if row["dist_to_industrial"] < 5 else "cropland"
            if region == "angul": return "industrial" if row["dist_to_industrial"] < 5 else "forest"
        return "unknown"
        
    df["land_cover_class"] = df.apply(get_lulc, axis=1)
    
    print("Applying weak-supervision labels...")
    df["label"] = df.apply(auto_label, axis=1)
    
    labeled_count = len(df[df["label"] != "uncertain"])
    pct = (labeled_count / len(df)) * 100
    print(f"Labeled {labeled_count} / {len(df)} records ({pct:.1f}%)")
    
    out_path = "data/processed/firms_labeled.csv"
    df.to_csv(out_path, index=False)
    print(f"Saved labeled dataset to {out_path}")

if __name__ == "__main__":
    main()
