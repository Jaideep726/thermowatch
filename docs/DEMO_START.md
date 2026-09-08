# ThermoWatch Demo Start Guide

Use the official frontend only:

`frontend-globe/SIH FRONTEND/frontend-globe/index.html`

The old copy is preserved under `frontend-dashboard-deprecated/` for reference and is not the demo frontend.

## 1. Start the backend

From the repository root. If you cloned the repository, this is the directory named `thermowatch`:

```bash
cd thermowatch
source venv/bin/activate
uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

Confirm the model is ready:

```bash
curl http://127.0.0.1:8000/api/status
```

Expected values include:

```json
{"model_loaded": true, "stub_mode": false, "status": "ok"}
```

## 2. Start the frontend server

Open a second terminal and navigate to the same repository root:

```bash
cd thermowatch
python3 -m http.server 5500 --bind 127.0.0.1
```

## 3. Open the official demo

Open:

`http://127.0.0.1:5500/frontend-globe/SIH%20FRONTEND/frontend-globe/index.html`

## 4. Demo flow

1. Click **Push next incident**.
2. The raw incident appears as **Pending classification**.
3. The frontend sends it to `POST /classify/incident`.
4. The backend XGBoost model returns the classification.
5. The workspace shows the processing stages and the model source.
6. If the incident is near the Jamnagar mock camera, CCTV verification runs.
7. The CCTV feed is temporary and clears after five seconds.
8. The incident remains in **Incident History**.
9. Push several incidents quickly to demonstrate sequential queue processing.
10. Click an incident in the history to move the map and review its result.

## 5. What to explain

- FIRMS supplies thermal detections and raw features.
- ThermoWatch uses the backend model to classify the detection.
- CCTV is checked only after classification.
- The current MP4 is a local mock feed for one Jamnagar camera.
- Other locations correctly show that no CCTV feed is available yet.

## Troubleshooting

- Port `8000` already in use: use the existing backend process if `/api/status` responds.
- Port `5500` already in use: use the existing frontend server or choose another port and update the URL.
- `stub_mode: true`: check that `ml/models/thermowatch_xgb.json` exists and dependencies are installed.
- Backend unavailable: the demo can use its prepared incident fallback, but the UI will show `prepared demo fallback` instead of `backend model`.
