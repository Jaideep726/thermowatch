# ThermoWatch

### AI-Based Detection & Classification of Industrial Fires and Persistent Thermal Sources
**SIH PS26162 | Team: Hexa Hustlers (5E7A7F) | Organization: NTRO**

---

## Problem Statement

Build an AI/ML system that takes NASA FIRMS satellite thermal-anomaly data and tells you **what is actually burning**, not just that something is hot.

FIRMS already *detects* heat. It does not *classify* it. Every red dot on a fire map could be:
- 🔴 **Wildfire** — vegetation burning, needs an emergency response
- 🟡 **Crop/stubble burning** — seasonal, agricultural
- 🟣 **Industrial heat source** — refinery flare, kiln, steel plant, running 24/7 on purpose
- ⚫ **False positive** — sun glint, hot rooftop, sensor noise

**ThermoWatch's job**: ingest FIRMS data, fuse it with OpenStreetMap + land-cover context, classify each detection into one of the four categories above, and present it on a decision-support dashboard that a responder can actually act on.

> The deliverable that matters is the **classification**, not the detection. Detection is a solved problem NASA already gives away for free.

---

## Repository Structure

```
thermowatch/
├── data/
│   ├── raw/              # Raw FIRMS CSVs, archive downloads
│   └── processed/        # Labeled data, OSM industrial JSONs, LULC lookup
├── ml/
│   └── models/           # Trained XGBoost model, charts
├── backend/              # FastAPI backend (classify, serve GeoJSON)
├── frontend-globe/       # CesiumJS 3D globe visualization
├── frontend-dashboard-deprecated/ # Preserved older dashboard copy (not for demo)
├── integration/          # CCTV mock trigger logic, glue scripts
├── docs/                 # Team core.md files, pitch deck, checklists
└── README.md
```

---

## Team Roles

| Person | Role | Primary Directory |
|--------|------|-------------------|
| P1 | Data Engineer + Repo Owner | `data/` |
| P2 | ML Engineer | `ml/` |
| P3 | Backend Engineer | `backend/` |
| P4 | Frontend Engineer — Globe | `frontend-globe/` |
| P5 | Frontend Engineer — Dashboard | `frontend-dashboard/` |
| P6 | Integration & Pitch Lead | `integration/`, `docs/` |

---

## Quick Start

```bash
# Clone
git clone https://github.com/<your-org-or-username>/thermowatch.git
cd thermowatch

# Backend
cd backend
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload

# Demo frontend — see docs/DEMO_START.md
```

---

## Demo Regions

| Region | Purpose |
|--------|---------|
| Jamnagar, Gujarat | Persistent refinery flares (Reliance + Nayara) |
| Punjab/Haryana | Stubble burning (Oct–Nov archive) |
| Uttarakhand | Wildfire season (Mar–Jun archive) |
| Angul, Odisha | Mixed industrial + forest edge ("complexity zone") |

---

See `/docs` for each team member's `core.md` notes.
