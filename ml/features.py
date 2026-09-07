"""
features.py - Feature engineering pipeline for ThermoWatch.

Computes the 12 model-only features from the weakly-labeled FIRMS data.
Strictly excludes any location-based features (distance to industrial, land cover, lat/lon)
to prevent the model from memorizing coordinates instead of learning thermal signatures.
"""

import pandas as pd
import numpy as np
from sklearn.neighbors import BallTree
import os

MODEL_FEATURES = [
    'bright_ti4', 'bright_ti5', 'bright_diff', 'frp',
    'confidence_num', 'daynight_num', 'hour_of_day',
    'temporal_persistence', 'site_temp_std', 'detections_per_month',
    'thermal_excess', 'frp_brightness_ratio',
]

def add_climatology(df):
    """
    Applies a simple regional monthly climatology for ambient temperature approximation (in Kelvin).
    These are rough estimates of average monthly highs.
    """
    # Rough baseline ambient temps in K (273.15 + Celsius)
    # Jamnagar: Coastal, hot. Punjab: Extreme seasonal. Uttarakhand: Mountainous/cooler. Angul: Tropical hot.
    climatology = {
        'jamnagar':    {1: 298, 2: 301, 3: 306, 4: 309, 5: 311, 6: 310, 7: 306, 8: 305, 9: 306, 10: 309, 11: 305, 12: 300},
        'punjab':      {1: 292, 2: 296, 3: 302, 4: 310, 5: 313, 6: 313, 7: 308, 8: 307, 9: 307, 10: 305, 11: 299, 12: 294},
        'uttarakhand': {1: 285, 2: 288, 3: 294, 4: 300, 5: 304, 6: 304, 7: 300, 8: 299, 9: 298, 10: 295, 11: 291, 12: 287},
        'angul':       {1: 301, 2: 305, 3: 310, 4: 313, 5: 314, 6: 309, 7: 305, 8: 304, 9: 305, 10: 305, 11: 302, 12: 299},
        'unknown':     {m: 300 for m in range(1, 13)}
    }
    
    ambient = []
    for _, row in df.iterrows():
        region = row['region']
        month = row['month']
        if region in climatology:
            ambient.append(climatology[region].get(month, 300))
        else:
            ambient.append(300)
    df['ambient_temp'] = ambient
    return df

def extract_features(df):
    print("Computing baseline numeric conversions...")
    # Map confidence to numeric (l/n/h -> 1/2/3, or numeric directly for MODIS)
    def map_conf(c):
        if pd.isna(c): return 2
        c = str(c).lower()
        if c == 'l': return 1
        if c == 'n': return 2
        if c == 'h': return 3
        try: return float(c) / 100.0 * 3  # Scale MODIS 0-100 to roughly 1-3
        except: return 2
        
    df['confidence_num'] = df['confidence'].apply(map_conf)
    df['daynight_num'] = df['daynight'].map({'D': 1, 'N': 0}).fillna(1)
    
    # Handle missing bright_ti5 (some MODIS might not map cleanly)
    # MODIS has bright_t31 instead of bright_ti5. We'll harmonize them.
    if 'bright_t31' in df.columns:
        df['bright_ti5'] = df['bright_ti5'].fillna(df['bright_t31'])
    
    df['bright_ti4'] = df['bright_ti4'].fillna(df['brightness']) if 'brightness' in df.columns else df['bright_ti4']
    
    df['bright_diff'] = df['bright_ti4'] - df['bright_ti5']
    df['frp_brightness_ratio'] = df['frp'] / (df['bright_ti4'] + 1e-5)
    
    # Time features
    df['acq_date'] = pd.to_datetime(df['acq_date'])
    df['month'] = df['acq_date'].dt.month
    
    # Extract hour from acq_time (format varies, usually HHMM)
    def extract_hour(t):
        try:
            t = int(t)
            return t // 100
        except: return 12
    df['hour_of_day'] = df['acq_time'].apply(extract_hour)
    
    df = add_climatology(df)
    df['thermal_excess'] = df['bright_ti4'] - df['ambient_temp']

    print("Computing spatial-temporal features (BallTree)...")
    # For temporal persistence, we look at detections within 1km.
    # To do this fast, we build a BallTree.
    rad_lats = np.radians(df['latitude'].values)
    rad_lons = np.radians(df['longitude'].values)
    points = np.vstack((rad_lats, rad_lons)).T
    
    tree = BallTree(points, metric='haversine')
    # 1 km in radians
    radius = 1.0 / 6371.0 
    
    # Find all points within 1km
    indices = tree.query_radius(points, r=radius)
    
    temporal_persistence = []
    site_temp_std = []
    detections_per_month = []
    
    df_dates = df['acq_date'].values
    df_temps = df['bright_ti4'].values
    
    # 30 days in numpy timedelta64
    thirty_days = np.timedelta64(30, 'D')
    
    for i, idx_list in enumerate(indices):
        current_date = df_dates[i]
        
        # temporal_persistence: count of points within 1km and within 30 days of this point
        close_dates = df_dates[idx_list]
        time_diffs = np.abs(close_dates - current_date)
        valid_time_mask = time_diffs <= thirty_days
        temporal_persistence.append(np.sum(valid_time_mask))
        
        # site_temp_std: std dev of temperature at this 1km cluster across ALL time
        site_temps = df_temps[idx_list]
        site_temp_std.append(np.std(site_temps) if len(site_temps) > 1 else 0)
        
        # detections_per_month: total detections at site / months of data span at site
        if len(close_dates) > 1:
            date_span_days = (np.max(close_dates) - np.min(close_dates)) / np.timedelta64(1, 'D')
            months_span = max(1.0, date_span_days / 30.0)
        else:
            months_span = 1.0
        detections_per_month.append(len(idx_list) / months_span)
        
    df['temporal_persistence'] = temporal_persistence
    df['site_temp_std'] = site_temp_std
    df['detections_per_month'] = detections_per_month
    
    return df

def main():
    in_path = "data/processed/firms_labeled.csv"
    out_path = "data/processed/firms_features.csv"
    
    if not os.path.exists(in_path):
        print(f"File {in_path} not found. Run label_data.py first.")
        return
        
    print(f"Loading {in_path}...")
    df = pd.read_csv(in_path)
    
    df = extract_features(df)
    
    # Keep only the columns we actually need for training/evaluation to save space
    keep_cols = MODEL_FEATURES + ['latitude', 'longitude', 'label', 'region', 'acq_date']
    df = df[[c for c in keep_cols if c in df.columns]]
    
    df.to_csv(out_path, index=False)
    print(f"Saved feature dataset with {len(df)} rows to {out_path}")

if __name__ == "__main__":
    main()
