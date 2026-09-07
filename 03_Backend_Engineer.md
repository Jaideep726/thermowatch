# Task PRD — Person 3: Backend Engineer

**Your job in one line:** Build the API that takes a FIRMS CSV, runs it through the ML model, and hands back classified, map-ready data (GeoJSON) that the frontend can draw.

**Wait for:** Person 2 to push `ml/models/thermowatch_xgb.json` before Task 2. You can build Task 1 (skeleton) immediately using fake/dummy data.

---

## Before you start
```bash
git clone https://github.com/<org>/thermowatch.git
cd thermowatch/backend
python -m venv venv
source venv/bin/activate
pip install fastapi uvicorn pandas xgboost python-multipart
```

---

## TASK 1 — FastAPI project skeleton

**What you're doing:** setting up a basic working API server, before it does anything smart, just to prove the wiring works.

1. Create `backend/main.py`:
   ```python
   from fastapi import FastAPI
   from fastapi.middleware.cors import CORSMiddleware

   app = FastAPI(title="ThermoWatch API")

   app.add_middleware(
       CORSMiddleware,
       allow_origins=["*"],  # fine for hackathon demo
       allow_methods=["*"],
       allow_headers=["*"],
   )

   @app.get("/")
   def health():
       return {"status": "ThermoWatch backend is running"}
   ```
2. Create `backend/requirements.txt`:
   ```
   fastapi
   uvicorn
   pandas
   xgboost
   python-multipart
   ```
3. Run it: `uvicorn backend.main:app --reload` (from repo root) — visit `http://localhost:8000` and confirm you see the health message.
4. Commit & push:
   ```bash
   git add backend/main.py backend/requirements.txt
   git commit -m "feat(backend): FastAPI skeleton with health check"
   git push
   ```

✅ **Checkpoint:** Server runs locally, `/` returns a status message.

---

## TASK 2 — `/classify` endpoint

**What you're doing:** the core of your job — accept a FIRMS-style CSV, run it through Person 2's model, return classified GeoJSON that CesiumJS can draw directly.

1. Add to `backend/main.py`:
   ```python
   import pandas as pd
   import xgboost as xgb
   from fastapi import UploadFile, File
   from io import StringIO
   import json

   model = xgb.XGBClassifier()
   model.load_model("ml/models/thermowatch_xgb.json")

   from ml.features import MODEL_FEATURES  # reuse Person 2's feature list
   LABEL_MAP = {0: 'wildfire', 1: 'crop_burning', 2: 'industrial', 3: 'false_positive'}

   @app.post("/classify")
   async def classify(file: UploadFile = File(...)):
       content = await file.read()
       df = pd.read_csv(StringIO(content.decode()))

       # NOTE: assumes df already has the 12 model features computed
       # (reuse Person 2's feature-engineering functions here if raw FIRMS CSV is passed in)
       X = df[MODEL_FEATURES]
       preds = model.predict(X)
       df['classification'] = [LABEL_MAP[p] for p in preds]

       features = []
       for _, row in df.iterrows():
           features.append({
               "type": "Feature",
               "geometry": {"type": "Point", "coordinates": [row['longitude'], row['latitude']]},
               "properties": {
                   "classification": row['classification'],
                   "frp": row.get('frp', 0),
                   "bright_ti4": row.get('bright_ti4', 0),
               }
           })
       return {"type": "FeatureCollection", "features": features}
   ```
2. **Important:** Coordinate with Person 2 on whether the CSV you receive already has the 12 features computed, or if you need to call their `features.py` functions yourself inside this endpoint. Write down whichever you agree on in your `core.md`.
3. Test with a small sample CSV using `curl` or Postman:
   ```bash
   curl -X POST -F "file=@data/raw/jamnagar_VIIRS_SNPP_NRT_10days.csv" http://localhost:8000/classify
   ```
4. Commit & push:
   ```bash
   git add backend/main.py
   git commit -m "feat(backend): /classify endpoint returning GeoJSON"
   git push
   ```

✅ **Checkpoint:** POSTing a CSV returns valid GeoJSON with a `classification` field per point.

---

## TASK 3 — `/fires.geojson` endpoint (what the frontend actually polls)

**What you're doing:** a simple GET endpoint that always serves the latest classified dataset, so the frontend doesn't need to upload a file every time — it just polls this.

1. Add to `backend/main.py`:
   ```python
   import os

   LATEST_GEOJSON_PATH = "backend/latest_fires.geojson"

   @app.get("/api/fires.geojson")
   def get_latest_fires():
       if not os.path.exists(LATEST_GEOJSON_PATH):
           return {"type": "FeatureCollection", "features": []}
       with open(LATEST_GEOJSON_PATH) as f:
           return json.load(f)
   ```
2. Modify `/classify` to also save its output to `backend/latest_fires.geojson` after generating it.
3. Pre-run `/classify` once on your Jamnagar+Punjab+Uttarakhand data so `latest_fires.geojson` exists and is committed as a fallback (in case live classification fails during demo).
4. Commit & push:
   ```bash
   git add backend/main.py backend/latest_fires.geojson
   git commit -m "feat(backend): /api/fires.geojson live-serving endpoint"
   git push
   ```

✅ **Checkpoint:** `GET http://localhost:8000/api/fires.geojson` returns real classified data without needing a file upload.

---

## TASK 4 — Error handling + demo safety net

**What you're doing:** making sure the API doesn't crash mid-demo if something's slightly off.

1. Wrap the `/classify` logic in a try/except; on failure, return a clear JSON error message instead of a 500 crash.
2. Add a `/api/status` endpoint returning `{"model_loaded": true, "last_updated": <timestamp>}` so the frontend/integration lead can show a "system healthy" indicator.
3. Commit & push:
   ```bash
   git add backend/main.py
   git commit -m "feat(backend): error handling + status endpoint"
   git push
   ```

✅ **Checkpoint:** Bad input doesn't crash the server; there's a status check the team can rely on during rehearsal.

---

## Your `core.md` file

Create `docs/core_backend_engineer.md`. After each task, append:
- **Tech stack used & why** (e.g., "FastAPI over Flask — async support, auto-generated docs at /docs")
- **Important findings** (e.g., API contract details — exact field names in the GeoJSON — so frontend devs don't have to guess)
- **Problems encountered & how you solved them**
- **Features and how they work**

---

> **Note for AI coding agents assisting with this task:** Only make code changes, run commands, or take actions autonomously if you are 95%+ confident they are correct and match what's described above. If you are below that confidence threshold, stop and ask the user a clarifying question instead of guessing.
