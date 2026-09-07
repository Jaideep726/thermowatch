from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from io import StringIO
import pandas as pd
import json
import os

# ── XGBoost model (loaded at startup if available) ──────────────────────────
MODEL_PATH = "ml/models/thermowatch_xgb.json"
model = None
model_loaded = False

try:
    import xgboost as xgb
    if os.path.exists(MODEL_PATH):
        model = xgb.XGBClassifier()
        model.load_model(MODEL_PATH)
        model_loaded = True
        print(f"[ThermoWatch] Model loaded from {MODEL_PATH}")
    else:
        print(f"[ThermoWatch] WARNING: Model file not found at {MODEL_PATH}. "
              "Running in STUB mode — predictions will be placeholder labels.")
except Exception as e:
    print(f"[ThermoWatch] ERROR loading model: {e}. Running in STUB mode.")

# ── Feature list (must match ml/features.py when model arrives) ─────────────
MODEL_FEATURES = [
    "bright_ti4", "bright_ti5", "bright_diff",
    "frp", "confidence_num", "daynight_num",
    "hour_of_day", "temporal_persistence",
    "site_temp_std", "detections_per_month",
    "thermal_excess", "frp_brightness_ratio",
]

LABEL_MAP = {0: "wildfire", 1: "crop_burning", 2: "industrial", 3: "false_positive"}

# ── App setup ────────────────────────────────────────────────────────────────
app = FastAPI(title="ThermoWatch API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # fine for hackathon demo
    allow_methods=["*"],
    allow_headers=["*"],
)

LATEST_GEOJSON_PATH = "backend/latest_fires.geojson"


# ── Helpers ──────────────────────────────────────────────────────────────────
def _df_to_geojson(df: pd.DataFrame) -> dict:
    """Convert a classified DataFrame into a GeoJSON FeatureCollection."""
    features = []
    for _, row in df.iterrows():
        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [float(row.get("longitude", 0)),
                                float(row.get("latitude", 0))]
            },
            "properties": {
                "classification": row.get("classification", "unknown"),
                "frp":            float(row.get("frp", 0)),
                "bright_ti4":     float(row.get("bright_ti4", 0)),
                "bright_ti5":     float(row.get("bright_ti5", 0)),
                "confidence":     str(row.get("confidence", "")),
                "acq_date":       str(row.get("acq_date", "")),
                "acq_time":       str(row.get("acq_time", "")),
            }
        })
    return {"type": "FeatureCollection", "features": features}


def _stub_classify(df: pd.DataFrame) -> pd.Series:
    """
    Placeholder classifier used when the real model is not yet available.
    Applies a simple rule-based heuristic on raw FIRMS columns so the
    pipeline is testable end-to-end without the trained model.
    NOTE: This is NOT the real ML model — replace once thermowatch_xgb.json arrives.
    """
    import numpy as np

    def rule(row):
        frp = row.get("frp", 0)
        try:
            frp = float(frp)
        except (ValueError, TypeError):
            frp = 0.0
        if frp > 200:
            return "industrial"
        elif frp > 50:
            return "wildfire"
        elif frp > 10:
            return "crop_burning"
        else:
            return "false_positive"

    return df.apply(rule, axis=1)


# ── Endpoints ────────────────────────────────────────────────────────────────
@app.get("/")
def health():
    return {"status": "ThermoWatch backend is running"}


@app.post("/classify")
async def classify(file: UploadFile = File(...)):
    """
    Accept a FIRMS-style CSV, classify each detection, return GeoJSON.
    Also saves output to backend/latest_fires.geojson for the GET endpoint.
    """
    try:
        content = await file.read()
        df = pd.read_csv(StringIO(content.decode()))

        # ── Run model or stub ────────────────────────────────────────────────
        if model_loaded:
            # Ensure all 12 features exist; fill missing with 0
            for feat in MODEL_FEATURES:
                if feat not in df.columns:
                    df[feat] = 0
            X = df[MODEL_FEATURES]
            preds = model.predict(X)
            df["classification"] = [LABEL_MAP[int(p)] for p in preds]
        else:
            # STUB: heuristic until real model arrives
            df["classification"] = _stub_classify(df)

        geojson = _df_to_geojson(df)

        # ── Persist for /api/fires.geojson ───────────────────────────────────
        with open(LATEST_GEOJSON_PATH, "w") as f:
            json.dump(geojson, f)

        return geojson

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Classification failed: {str(e)}")


@app.get("/api/fires.geojson")
def get_latest_fires():
    """
    Always serves the latest classified dataset.
    Frontend polls this endpoint — no file upload needed.
    """
    if not os.path.exists(LATEST_GEOJSON_PATH):
        return {"type": "FeatureCollection", "features": []}
    with open(LATEST_GEOJSON_PATH) as f:
        return json.load(f)


@app.get("/api/status")
def status():
    """
    Health / readiness check for the team to verify the system is up.
    Returns model load status and the last time the GeoJSON was updated.
    """
    import datetime
    last_updated = None
    if os.path.exists(LATEST_GEOJSON_PATH):
        mtime = os.path.getmtime(LATEST_GEOJSON_PATH)
        last_updated = datetime.datetime.utcfromtimestamp(mtime).isoformat() + "Z"

    return {
        "model_loaded":  model_loaded,
        "model_path":    MODEL_PATH,
        "stub_mode":     not model_loaded,
        "last_updated":  last_updated,
        "status":        "ok",
    }
