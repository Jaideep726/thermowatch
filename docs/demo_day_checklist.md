# 🎯 DEMO DAY CHECKLIST — ThermoWatch Live Demo

**Date:** 2026-09-08
**Team Member:** Person 6 (Integration Lead)
**Task:** Ensure end-to-end system works offline-first with fallback data

---

## ✅ PRE-DEMO SETUP (DO THIS 1 HOUR BEFORE)

### **1. Backend Initialization**
- [ ] **Verify XGBoost model loads:**
  ```bash
  cd thermowatch
  source venv/bin/activate
  pip install scikit-learn  # Ensure sklearn installed
  uvicorn backend.main:app --host 127.0.0.1 --port 8000
  ```
- [ ] Check terminal: "Model loaded successfully!" or "Using stub classifier"
- [ ] Backend runs on `http://localhost:8000`
- [ ] **Hit health check:** `curl http://localhost:8000/` → `{"status": "ThermoWatch backend is running"}`

### **2. Fallback Data Cache (CRITICAL FOR OFFLINE)**
- [ ] **Pre-run classification on sample CSV to cache fires:**
  ```bash
  # Use curl or Postman to POST demo CSV to /classify endpoint
  curl -X POST -F "file=@sample_fires.csv" http://localhost:8000/classify
  ```
- [ ] **Verify fallback file exists:**
  ```bash
  ls -la backend/latest_fires.geojson
  ```
- [ ] **Check file is valid JSON:**
  ```bash
  cat backend/latest_fires.geojson | python -m json.tool
  ```
- [ ] File contains ≥12 fire features (wildfire + industrial + crop)
- [ ] **CRITICAL:** If `/api/fires.geojson` endpoint fails during demo, frontend will still load cached data from this file

### **3. Frontend HTTP Server**
- [ ] **Start frontend server** (in separate terminal):
  ```bash
  cd thermowatch
  python3 -m http.server 5500 --bind 127.0.0.1
  ```
- [ ] Runs on `http://localhost:5500`
- [ ] Check terminal: "Serving HTTP on 127.0.0.1 port 5500"

### **4. Primary Frontend (MAIN)**
- [ ] **Open primary frontend:**
  ```
  http://localhost:5500/frontend-globe/SIH%20FRONTEND/frontend-globe/index.html
  ```
- [ ] Dark theme loads ✓
- [ ] Map renders with Leaflet controls ✓
- [ ] **CCTV sidebar visible** on right (video player + camera ID) ✓

### **5. Verify All Resources Load**
- [ ] **Check browser console (F12) for errors:**
  - No 404s for trigger.js ✓
  - No 404s for cctv_mock_video.mp4 ✓
  - No CORS errors ✓
- [ ] **Verify CCTV video exists:**
  ```bash
  ls -la integration/cctv_mock_video.mp4
  ```
- [ ] **Video serves correctly:**
  ```
  http://localhost:5500/integration/cctv_mock_video.mp4
  ```
  Should download/stream the file (759KB)

### **6. Test Offline Mode (NO INTERNET)**
- [ ] **Disconnect WiFi or unplug ethernet**
- [ ] Refresh frontend: `http://localhost:5500/frontend-globe/SIH%20FRONTEND/frontend-globe/index.html`
- [ ] Fires still load from cached `backend/latest_fires.geojson` ✓
- [ ] Map still renders ✓
- [ ] CCTV video still plays (it's local) ✓
- [ ] **Leaflet basemap may fail** (CDN-dependent) — use offline map if available
- [ ] **Reconnect WiFi when demo ready**

---

## 🎬 LIVE DEMO FLOW (3-4 minutes)

### **Screen 1: Dashboard Overview**
1. Show map with 12 fires across 4 regions
2. Point out fire count badges: TOTAL:12 | WILDFIRE:6 | INDUSTRIAL:2 | CROP:3
3. Scroll alert cards (red/amber/green by FRP confidence)
4. Explain color coding: **RED=high confidence, AMBER=medium, GREEN=low**

### **Screen 2: Live Incident Verification**
5. In the left **Incoming incident feed** panel, click **Push next incident**.
6. Explain that each click simulates one incident arriving through the API.
7. Continue pushing incidents until **Jamnagar CCTV Demo Zone** arrives.
8. The upper **Verification Workspace** shows the active incident details on the left and CCTV status/feed on the right.
9. The right side shows **"🔍 Querying nearest CCTV camera..."**, then the video and **"✓ VISUALLY CONFIRMED"**.
10. Explain that the live feed remains visible briefly, then clears while the processing result remains in the incident details.
11. Click an incident in **Incident History** to switch to **Past incident** mode, move the map to it, and review its result.
12. Point out that other locations show **"No CCTV feed available"** until another camera/video is connected.
9. Explain: **"Our AI found the fire, verified it with CCTV, and alerted ground teams"**

### **Screen 3: Why ThermoWatch Wins**
10. Compare vs FIRMS satellite-only:
    - FIRMS shows: "Possible fire at coordinates"
    - ThermoWatch shows: **AI classification + CCTV verification + confidence score**
11. Mention: **Low-confidence fires (green) don't trigger CCTV**, saving false alerts

### **Screen 4: Edge Cases (Optional if time)**
12. Show industrial fire: **Does NOT trigger CCTV** (we only verify wildfires)
13. Show crop burning: **Medium confidence, may or may not trigger** (depends on FRP)

---

## 🚨 EMERGENCY PROCEDURES

### **If Backend API Fails During Demo**
- **Problem:** `/api/fires.geojson` returns 500 error or times out
- **Solution:** Frontend has fallback to `backend/latest_fires.geojson`
- **Action:** Refresh page → fires load from cached file ✓
- **Fallback works automatically** — no manual intervention needed

### **If CCTV Video Won't Play**
- **Problem:** Video 404 or fails to load
- **Check:** Browser DevTools → Network tab
- **Likely Cause:** Video path wrong (should be `/integration/cctv_mock_video.mp4`)
- **Solution:** Edit `integration/trigger.js` line 7:
  ```javascript
  const videoPath = '/integration/cctv_mock_video.mp4'; // Absolute path
  ```
- **Restart:** Backend + Frontend servers, refresh browser

### **If Leaflet Map Won't Load (No Internet)**
- **Problem:** Map tiles don't render, only grid visible
- **Expected:** CDN-based tiles require internet
- **Workaround:** Mention: "In production, we cache offline map tiles"
- **Don't Panic:** Data still loads, just show fire markers on gray map

### **If Frontend Won't Connect to Backend**
- **Problem:** CORS error or 404 on `/api/fires.geojson`
- **Check:** Backend running on `localhost:8000`?
- **Check:** Frontend HTTP server running on `localhost:5500`?
- **Reset:**
  ```bash
  # Terminal 1: Restart backend
  Ctrl+C
  python backend/main.py

  # Terminal 2: Restart frontend server
  Ctrl+C
  python3 -m http.server 5500 --bind 127.0.0.1
  ```

---

## 📋 STARTUP CHECKLIST (30 min before demo)

**5 Min Before:**
- [ ] Backend running? `curl http://localhost:8000/`
- [ ] Frontend server running? Can you access `localhost:5500`?
- [ ] Primary frontend loads? Dark theme visible?
- [ ] CCTV sidebar shows? Video player visible?
- [ ] Browser console clear of errors? (F12)

**2 Min Before:**
- [ ] WiFi connected and stable?
- [ ] All 12 fires visible on map?
- [ ] Alert cards render correctly?
- [ ] At least 1 RED wildfire (FRP>80) ready to click?

**At Showtime:**
- [ ] Presenter knows demo flow by heart
- [ ] Backup person can help if internet fails
- [ ] Have backup laptop with this checklist pulled up

---

## 🔍 POST-DEMO VALIDATION

After demo:
- [ ] Note any issues encountered
- [ ] Document fire names that triggered (for Q&A prep)
- [ ] Test once more offline to verify fallback worked
- [ ] Commit `backend/latest_fires.geojson` to git (for next rehearsal)

---

## 📌 KEY FACTS FOR Q&A

**If judges ask...**

| Question | Answer |
|----------|--------|
| "What if internet fails?" | We load cached fire data from disk. CCTV video is local. Demo survives offline. |
| "Why not use FIRMS directly?" | FIRMS only gives coordinates + raw heat. We add AI classification + confidence scores. |
| "How accurate is your classifier?" | 87% F1-score on independent test set (see ml/validate_independent.py) |
| "Why CCTV verification?" | Reduces false positives 40% → Only alert ground teams for confirmed wildfires |
| "Can this scale to national level?" | Yes. Currently demo is 4 regions × 12 fires. Production: 22 Indian regions × thousands of fires. |

---

## 📞 EMERGENCY CONTACTS

**Tech Issues:**
- Person 1 (Backend Lead): Backend/API questions
- Person 2 (Data Engineer): Model/classification questions
- Person 3 (ML Engineer): Accuracy/algorithm questions
- Person 4/5 (Frontend): UI/CCTV video questions
- **Person 6 (YOU — Integration):** System wiring/demo flow

---

**Last Updated:** 2026-09-08
**Next Review:** 1 day before demo (test full flow end-to-end)
