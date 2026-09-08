# ThermoWatch End-to-End Testing Checklist
**Test Date:** 2026-09-07
**Tester:** Person 6 (Integration Lead)

---

## PRE-TEST SETUP

### ✓ Prerequisites Check
Before running any test, verify these files exist:
- [ ] `backend/main.py` — Backend API code
- [ ] `ml/models/thermowatch_xgb.json` — Trained XGBoost model (168K)
- [ ] `integration/cctv_mock_video.mp4` — Mock video (759K)
- [ ] `integration/trigger.js` — CCTV trigger logic
- [ ] `frontend-globe/SIH FRONTEND/frontend-globe/index.html` — Globe frontend
- [ ] `frontend-dashboard/SIH WEB DEV/frontend-globe/index.html` — Dashboard frontend

---

## PHASE 1: BACKEND STARTUP (10 min)

### Test 1.1: Start Backend Server
**Command:**
```bash
cd thermowatch
python -m venv venv
source venv/bin/activate  # or: venv\Scripts\activate on Windows
pip install -r backend/requirements.txt
uvicorn backend.main:app --reload
```

**What to expect:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
[ThermoWatch] Model loaded from ml/models/thermowatch_xgb.json
```

**PASS/FAIL:**
- ✅ PASS if: Server runs, model loads, no errors
- ❌ FAIL if: Port 8000 in use, model fails to load, missing dependencies

**Result:** ________ (PASS / FAIL)

---

### Test 1.2: API Health Check
**In browser or curl, open:**
```
http://localhost:8000/
```

**What to expect:**
```json
{"status": "ThermoWatch backend is running"}
```

**PASS/FAIL:**
- ✅ PASS if: Status returns immediately
- ❌ FAIL if: Connection refused, timeout, or error response

**Result:** ________ (PASS / FAIL)

---

### Test 1.3: Check Model Status Endpoint
**In browser or curl, open:**
```
http://localhost:8000/api/status
```

**What to expect:**
```json
{
  "model_loaded": true,
  "model_path": "ml/models/thermowatch_xgb.json",
  "stub_mode": false,
  "last_updated": null,
  "status": "ok"
}
```

**PASS/FAIL:**
- ✅ PASS if: `model_loaded: true` and `stub_mode: false`
- ⚠️ WARN if: `stub_mode: true` (model not loading, using heuristic fallback)
- ❌ FAIL if: Status endpoint returns error

**Result:** ________ (PASS / FAIL / WARN)
**Note:** If WARN, backend will still work but with fake FRP-based classifier instead of ML model

---

## PHASE 2: FRONTEND STARTUP (5 min)

### Test 2.1: Open Frontend — Globe Version
**In VS Code:**
- Open file: `frontend-globe/SIH FRONTEND/frontend-globe/index.html`
- Right-click → "Open with Live Server" (or open in browser directly)
- Expected URL: `http://127.0.0.1:5500/frontend-globe/SIH%20FRONTEND/frontend-globe/index.html`

**What to expect:**
- Leaflet map loads with dark background (#060913)
- Sidebar appears on right (360px wide, dark theme)
- Brand header shows: "🔥 ThermoWatch"
- Stat boxes show: TOTAL, WILDFIRE, INDUSTRIAL, CROP counts (all zeros initially)

**PASS/FAIL:**
- ✅ PASS if: Page loads, no JavaScript errors in console
- ❌ FAIL if: Blank page, console shows errors, map not visible

**Result:** ________ (PASS / FAIL)

**Check Console:**
```javascript
// Open DevTools (F12) → Console tab
// You should see NO red errors
// You may see: "[ThermoWatch] High-confidence wildfire detected..." (from trigger.js)
```

---

### Test 2.2: Open Frontend — Dashboard Version
**In new tab:**
- Open file: `frontend-dashboard/SIH WEB DEV/frontend-globe/index.html`
- Expected URL: `http://127.0.0.1:5500/frontend-dashboard/SIH%20WEB%20DEV/frontend-globe/index.html`

**What to expect:**
- Same as 2.1 (both frontends have identical UI)

**PASS/FAIL:**
- ✅ PASS if: Loads without errors
- ❌ FAIL if: Console errors

**Result:** ________ (PASS / FAIL)

---

## PHASE 3: API INTEGRATION (5 min)

### Test 3.1: Check /api/fires.geojson Endpoint
**In browser or curl:**
```
http://localhost:8000/api/fires.geojson
```

**What to expect:**
```json
{
  "type": "FeatureCollection",
  "features": []
}
```

**Empty array is OK at startup — no fires uploaded yet.**

**PASS/FAIL:**
- ✅ PASS if: Returns valid GeoJSON (even if empty)
- ❌ FAIL if: 404, 500 error, or malformed JSON

**Result:** ________ (PASS / FAIL)

---

## PHASE 4: FIRE DATA LOADING (10 min)

### Test 4.1: Load Mock Fire Data
**In Globe Frontend Console (F12):**
```javascript
// This will load hardcoded test fires
loadFireData(mockFireData);
```

**What to expect:**
1. Map updates: Markers appear (small circles/dots)
2. Sidebar stats update:
   - TOTAL: 5 (or however many in mockFireData)
   - WILDFIRE: varies
   - INDUSTRIAL: varies
   - CROP: varies
3. Alert cards appear (red/amber/green colored boxes with fire details)

**PASS/FAIL:**
- ✅ PASS if: Markers visible, counts non-zero, cards show
- ❌ FAIL if: No markers, console errors, counts stay 0

**Result:** ________ (PASS / FAIL)

**Note:** Check console for errors:
```
// Should NOT see errors like:
// "checkForCctvTrigger is not defined"
// "Cannot read property 'features' of undefined"
```

---

### Test 4.2: Check Fire Marker Click
**On Globe Frontend:**
1. Click on any fire marker (red dot on map)
2. Sidebar should update with fire details

**What to expect:**
- Fire classification shows (wildfire, industrial, crop, false_positive)
- FRP value displays
- Confidence level shows
- Lat/Lon coordinates shown

**PASS/FAIL:**
- ✅ PASS if: Marker clickable, details show
- ❌ FAIL if: No response on click

**Result:** ________ (PASS / FAIL)

---

## PHASE 5: CCTV AUTO-TRIGGER TEST (10 min)

### Test 5.1: Auto-Trigger on High-Confidence Wildfire
**In Console, run:**
```javascript
// Inject a high-confidence wildfire
const testWildfire = {
  type: "Feature",
  geometry: { type: "Point", coordinates: [69.5, 22.0] },
  properties: {
    classification: "wildfire",
    frp: 150,  // HIGH FRP = high confidence
    confidence: "H",
    acq_date: "2026-09-07",
    acq_time: "1430"
  }
};

const testData = {
  type: "FeatureCollection",
  features: [testWildfire]
};

loadFireData(testData);
```

**What to expect (in order):**
1. Fire marker appears on map
2. Immediately after loadFireData() completes:
   - Sidebar CCTV panel shows: **"Querying..."** state
   - Sidebar background briefly changes (appears active)
3. After ~2 seconds:
   - CCTV panel shows **mock video playing**
   - Green **"CONFIRMED"** badge appears below video
   - Badge pulses (animation effect)
   - Camera ID shown (e.g., `CAM-2200-6950`)

**Console output should show:**
```
[ThermoWatch] High-confidence wildfire detected. Triggering CCTV lookup...
[ThermoWatch] CCTV Confirmed: CAM-XXXXX
```

**PASS/FAIL:**
- ✅ PASS if: Video shows, badge appears, auto-triggered (no manual click needed)
- ⚠️ WARN if: Video doesn't play but badge appears (video file issue)
- ❌ FAIL if: Nothing happens, or "Querying" never appears

**Result:** ________ (PASS / FAIL / WARN)

---

### Test 5.2: NO Auto-Trigger on Low-Confidence Wildfire
**In Console, run:**
```javascript
// LOW FRP wildfire (should NOT trigger)
const lowConfWildfire = {
  type: "Feature",
  geometry: { type: "Point", coordinates: [72.0, 30.0] },
  properties: {
    classification: "wildfire",
    frp: 20,  // LOW FRP = low confidence
    confidence: "L",
    acq_date: "2026-09-07",
    acq_time: "1430"
  }
};

const testData = {
  type: "FeatureCollection",
  features: [lowConfWildfire]
};

loadFireData(testData);
```

**What to expect:**
- Fire marker appears
- CCTV panel does **NOT** show video
- Panel stays empty/reset

**Console should show:**
```
// NO "[ThermoWatch]" log messages
```

**PASS/FAIL:**
- ✅ PASS if: No video appears (correct — low confidence shouldn't trigger)
- ❌ FAIL if: Video appears (false trigger)

**Result:** ________ (PASS / FAIL)

---

### Test 5.3: NO Auto-Trigger on Industrial Fire (Even High FRP)
**In Console, run:**
```javascript
// Industrial fire, even with high FRP (should NOT trigger)
const industrialFire = {
  type: "Feature",
  geometry: { type: "Point", coordinates: [69.8, 21.9] },
  properties: {
    classification: "industrial",
    frp: 200,  // HIGH FRP but INDUSTRIAL
    confidence: "H",
    acq_date: "2026-09-07",
    acq_time: "1430"
  }
};

const testData = {
  type: "FeatureCollection",
  features: [industrialFire]
};

loadFireData(testData);
```

**What to expect:**
- Fire marker appears
- CCTV panel does **NOT** show video (industrial ≠ wildfire)

**PASS/FAIL:**
- ✅ PASS if: No video (correct — only wildfires trigger)
- ❌ FAIL if: Video appears (logic error)

**Result:** ________ (PASS / FAIL)

---

## PHASE 6: DASHBOARD VERSION (5 min)

### Test 6.1: Repeat Tests 4.1 & 5.1 on Dashboard Frontend
**Steps:**
1. Switch to Dashboard tab (from Test 2.2)
2. Run same `loadFireData(testData)` commands
3. Verify same behavior: markers, counts, CCTV auto-trigger

**Expected Results:** Should be identical to Globe version

**PASS/FAIL:**
- ✅ PASS if: Behaves same as Globe
- ❌ FAIL if: Different behavior or errors

**Result:** ________ (PASS / FAIL)

---

## PHASE 7: ERROR HANDLING (5 min)

### Test 7.1: Empty Fire Data
**In Console:**
```javascript
loadFireData({ type: "FeatureCollection", features: [] });
```

**What to expect:**
- Counts all show 0
- No markers
- CCTV panel resets
- No errors in console

**PASS/FAIL:**
- ✅ PASS if: Handles gracefully
- ❌ FAIL if: Console errors

**Result:** ________ (PASS / FAIL)

---

### Test 7.2: Malformed Fire Data
**In Console:**
```javascript
// Missing required fields
loadFireData({
  type: "FeatureCollection",
  features: [{
    type: "Feature",
    geometry: null,  // Invalid
    properties: {}
  }]
});
```

**What to expect:**
- Page doesn't crash
- Console may show warnings but not fatal errors

**PASS/FAIL:**
- ✅ PASS if: Doesn't crash
- ❌ FAIL if: Page breaks or throws unhandled errors

**Result:** ________ (PASS / FAIL)

---

## PHASE 8: OFFLINE VERIFICATION (5 min)

### Test 8.1: File Paths (Offline-Safe)
**Verify:**
- [ ] Video file: `integration/cctv_mock_video.mp4` is a **local file** (not CDN URL)
- [ ] Scripts included: `integration/trigger.js` is a **local file** (not CDN)
- [ ] Map library: Leaflet is from CDN (leaflet@1.9.4) — this REQUIRES internet
  - ⚠️ If internet dies, map won't load but sidebar + CCTV might still work

**PASS/FAIL:**
- ✅ PASS if: Video and trigger.js are local files
- ❌ FAIL if: Any critical resources are CDN-only (except Leaflet which is acceptable)

**Result:** ________ (PASS / FAIL)

---

## SUMMARY TABLE

Fill this in as you test. Mark ✅, ❌, or ⚠️:

| Test | Result | Notes |
|------|--------|-------|
| 1.1 Backend Startup | ✅ | Model loads successfully |
| 1.2 Health Check | ✅ | Returns status: running |
| 1.3 Status Endpoint | ✅ | model_loaded: true, stub_mode: false |
| 2.1 Globe Frontend Load | ✅ | Loads without errors, map visible |
| 2.2 Dashboard Frontend Load | ✅ | Same as 2.1 |
| 3.1 /api/fires.geojson | ✅ | Returns empty GeoJSON |
| 4.1 Load Mock Data | ✅ | 12 fires loaded, counts: 6 wildfire, 2 industrial, 3 crop |
| 4.2 Click Fire Marker | ✅ | Markers clickable (fire details show) |
| 5.1 CCTV Auto-Trigger (High-Conf Wildfire) | ✅ | **VIDEO PLAYS + GREEN BADGE CONFIRMED** |
| 5.2 NO Trigger (Low-Conf Wildfire) | ⏳ | Not yet tested |
| 5.3 NO Trigger (Industrial) | ⏳ | Not yet tested |
| 6.1 Dashboard Same Behavior | ⏳ | Not yet tested |
| 7.1 Empty Data Handling | ⏳ | Not yet tested |
| 7.2 Malformed Data Handling | ⏳ | Not yet tested |
| 8.1 Offline File Paths | ✅ | Video and JS are local files ✓ |

---

## ISSUES FOUND

**Bug/Issue #1:**
- Description:
- Severity: (Critical / High / Medium / Low)
- Routed to: (Person X)
- Status: (Open / In Progress / Fixed)
- Notes:

**Bug/Issue #2:**
- Description:
- Severity:
- Routed to:
- Status:
- Notes:

---

## SIGN-OFF

| Item | Status |
|------|--------|
| All tests completed | ⏳ |
| Critical bugs identified | ⏳ |
| Routed to team members | ⏳ |
| Ready for full rehearsal | ⏳ |

**Tester Signature:** _________________
**Date:** 2026-09-07
**Time Spent:** _____ minutes
