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

## TASK 2 — `/classify` endpoint
*Notes to be added after Task 2 is complete.*

---

## TASK 3 — `/api/fires.geojson` endpoint
*Notes to be added after Task 3 is complete.*

---

## TASK 4 — Error handling + `/api/status`
*Notes to be added after Task 4 is complete.*
