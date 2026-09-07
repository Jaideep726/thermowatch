# Backend Engineer — Core Notes
> Append notes after each task. This is the single source of truth for the backend API contract.

---

## TASK 1 — FastAPI Skeleton ✅

**Date completed:** 2026-09-07

### Tech stack used & why
- **FastAPI** over Flask: async support, Pydantic validation, auto-generated Swagger UI at `/docs` — essential for teammates to explore the API without writing curl commands.
- **uvicorn**: ASGI server required by FastAPI; `--reload` flag for dev hot-reloading.
- **CORSMiddleware** with `allow_origins=["*"]`: Needed so the CesiumJS frontend (served from a different origin) can call the API without browser CORS errors. Fine for hackathon — lock down in production.

### How to run
```bash
# From repo root
cd thermowatch
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r backend/requirements.txt
uvicorn backend.main:app --reload
# Visit http://localhost:8000
# Visit http://localhost:8000/docs  ← Swagger UI
```

### API contract (as of Task 1)
| Endpoint | Method | Returns |
|----------|--------|---------|
| `/` | GET | `{"status": "ThermoWatch backend is running"}` |

### Important findings
- Server must be run from repo root (`uvicorn backend.main:app`) so Python can resolve `ml/` imports in future tasks.
- `.gitignore` already excludes `venv/` — do NOT commit the virtual environment.

### Problems encountered
- None in Task 1.

---

## TASK 2 — `/classify` endpoint ✅

**Date completed:** 2026-09-07

### Tech stack used & why
- **XGBoost** (`xgb.XGBClassifier`): Loaded at startup from `ml/models/thermowatch_xgb.json`. If file not present, falls back to stub mode automatically — server never crashes on startup.
- **python-multipart**: Required by FastAPI to accept `multipart/form-data` file uploads.
- **pandas**: Reads the uploaded CSV into a DataFrame; fills missing model features with 0 to avoid key errors.

### API contract
| Endpoint | Method | Input | Returns |
|----------|--------|-------|---------|
| `/classify` | POST | `multipart/form-data`, field `file` = FIRMS CSV | GeoJSON `FeatureCollection` |

**GeoJSON `properties` fields per feature:**
```json
{
  "classification": "wildfire | crop_burning | industrial | false_positive",
  "frp":        <float>,
  "bright_ti4": <float>,
  "bright_ti5": <float>,
  "confidence": "<str: h/n/l>",
  "acq_date":   "<YYYY-MM-DD>",
  "acq_time":   "<str>"
}
```
> ⚠️ **Frontend devs**: use `properties.classification` to color-code points. Use `properties.frp` to scale point size.

### Important findings
- **Stub mode**: Until `ml/models/thermowatch_xgb.json` arrives, the server runs a FRP-threshold heuristic (`frp > 200 → industrial`, `> 50 → wildfire`, `> 10 → crop_burning`, else `false_positive`). This is clearly labeled in logs and `/api/status`.
- **MODEL_FEATURES list** is defined in `main.py` as the single source of truth. When Person 2 (ML engineer) delivers `ml/features.py`, import `MODEL_FEATURES` from there instead and delete the local copy.
- **`/classify` also saves** the output to `backend/latest_fires.geojson` — so the frontend can poll `/api/fires.geojson` without re-uploading the CSV every time.
- The CSV is gitignored (`*.csv`) — share sample files via Drive link, not git.

### Problems encountered
- PowerShell aliases `curl` → `Invoke-WebRequest`, which doesn't support `-F` multipart. Use `C:\Windows\System32\curl.exe` explicitly for testing.

---

## TASK 3 — `/api/fires.geojson` endpoint ✅

**Date completed:** 2026-09-07

### Tech stack used & why
- Simple `GET` endpoint reads `backend/latest_fires.geojson` from disk and returns it.
- Returns empty FeatureCollection `{"type":"FeatureCollection","features":[]}` if no data yet — frontend handles this gracefully.

### API contract
| Endpoint | Method | Returns |
|----------|--------|---------|
| `/api/fires.geojson` | GET | GeoJSON `FeatureCollection` (latest classified data) |

### Important findings
- Frontend should poll this endpoint (e.g., every 30s or on page load). It does NOT need to upload a file — just a plain GET.
- Pre-run `/classify` on the demo CSVs before the presentation and commit `backend/latest_fires.geojson` as a fallback in case live classification fails mid-demo.

### Problems encountered
- None.

---

## TASK 4 — Error handling + `/api/status` ✅

**Date completed:** 2026-09-07

### Tech stack used & why
- `/classify` is fully wrapped in `try/except` — returns HTTP 400 with a readable JSON error message instead of a 500 crash.
- `/api/status` returns model load state, stub mode flag, and ISO 8601 timestamp of last GeoJSON update.

### API contract
| Endpoint | Method | Returns |
|----------|--------|---------|
| `/api/status` | GET | `{"model_loaded": bool, "model_path": str, "stub_mode": bool, "last_updated": str\|null, "status": "ok"}` |

### Important findings
- Integration lead / teammates can hit `/api/status` during rehearsal to confirm the system is healthy before the demo.
- `stub_mode: true` means the real XGBoost model is not loaded — remind the ML engineer to push `thermowatch_xgb.json`.

### Problems encountered
- None.
