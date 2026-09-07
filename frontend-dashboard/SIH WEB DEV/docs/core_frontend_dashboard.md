# Core Frontend Dashboard Documentation (`docs/core_frontend_dashboard.md`)

This document records the architectural decisions, technical implementation details, exposed API contracts, and features of the **ThermoWatch Dashboard Sidebar** (Person 5 - Frontend Engineer).

---

## Architectural Decision

- **File Structure & Integration Approach:** Integrated directly into `frontend-globe/index.html`.
- **Why:** Integrating the sidebar directly adjacent to the globe container in `frontend-globe/index.html` eliminates cross-origin iframe messaging complexities, guarantees instantaneous camera movement triggers (`flyTo`), and ensures seamless hackathon deployment.

---

## Tech Stack Used & Why

1. **HTML5 & Semantic Markup**: Clean structural elements (`#sidebar`, `.stat-box`, `#alerts-container`, `#cctv-panel`) for maximum performance and accessibility.
2. **Vanilla CSS3 (Glassmorphism & Micro-animations)**:
   - High-contrast dark theme background (`rgba(15, 23, 42, 0.92)` with `backdrop-filter: blur(16px)`).
   - Dynamic hover states and pulsing CSS `@keyframes` badge animations for visual excitement and urgency.
3. **Vanilla ES6 Javascript**:
   - Zero framework overhead, hyper-fast DOM manipulation.
   - Global function exposure (`window.showCctvQuerying`, `window.showCctvConfirmed`) for Person 6 (Integration Lead).
4. **Leaflet.js / GIS Visualizer**:
   - Lightweight, robust dark tile mapping rendering thermal anomaly markers with real-time fly-to camera controls on alert card clicks.

---

## Exposed API Contract (For Person 6 - Integration Lead)

To trigger the CCTV verification panel programmatically from external integration scripts or satellite telemetry events, call the following window functions:

### 1. `showCctvQuerying()`
- **Signature:** `window.showCctvQuerying()`
- **Parameters:** None
- **Behavior:** Updates `#cctv-panel` border color to amber/orange (`#f59e0b`) and displays `"🔍 Querying nearest CCTV camera..."`.

### 2. `showCctvConfirmed(videoUrl, cameraId)`
- **Signature:** `window.showCctvConfirmed(videoUrl, cameraId)`
- **Parameters:**
  - `videoUrl` *(String)*: Direct video URL or stream path (e.g. MP4 / WebM / HLS).
  - `cameraId` *(String)*: Unique Camera ID (e.g. `'CAM-802'`).
- **Behavior:** Renders an autoplaying, looping muted video feed inside `#cctv-panel` with a glowing green border and a pulsing `✅ VISUALLY CONFIRMED — Camera <cameraId>` badge.

### 3. `resetCctvPanel()`
- **Signature:** `window.resetCctvPanel()`
- **Parameters:** None
- **Behavior:** Resets `#cctv-panel` back to its initial idle state (`"Awaiting satellite trigger..."`).

---

## Task Breakdown & Implementation Details

### Task 1 — Sidebar Layout & Live Stat Boxes
- **Stat Counters:** `#total-count`, `#wildfire-count`, `#industrial-count`, `#crop-count`.
- **Data Engine:** Function `loadFireData(geojson)` iterates through all features, aggregates counts per `classification`, and updates DOM elements dynamically.

### Task 2 — Priority Alert Cards (Red / Amber / Green)
- **Priority Rules:**
  - 🔴 **Red Alert**: `classification === 'wildfire'` AND `frp > 100 MW`
  - 🟠 **Amber Alert**: (`classification === 'wildfire'` AND `frp <= 100 MW`) OR `classification === 'industrial'`
  - 🟢 **Green Alert**: All other non-false-positive thermal detections (e.g. `crop_burning`)
- **Ranking:** Detections are filtered to exclude `false_positive`, sorted by Fire Radiative Power (FRP) descending, and top 10 items are displayed.
- **Interactive Feature:** Clicking any alert card triggers `flyToAnomaly(lat, lng)`, animating the globe camera directly to the target anomaly.

### Task 3 — CCTV Confirmation Panel UI Shell
- Built `#cctv-panel` box with dark background `#000` and glowing border `#00ff66`.
- Includes `.confirmed-badge` styled with CSS pulse animation (`@keyframes pulse`).
- Includes dev control buttons for quick integration testing in the browser console.

---

## Problems Encountered & Solutions

1. **Problem:** Ensuring map markers and alert cards stay synced when new telemetry data arrives.
   - **Solution:** Encapsulated stat calculation, card rendering, and marker plotting inside a single declarative `loadFireData(data)` function.
2. **Problem:** Smooth globe navigation when clicking alert cards without breaking map state.
   - **Solution:** Standardized coordinates as `[lng, lat]` matching GeoJSON standard and converted to `[lat, lng]` for `map.flyTo([lat, lng], 8)`.

---

## How to Verify

1. Open `frontend-globe/index.html` in any web browser.
2. Verify live count stats match the breakdown of total thermal anomalies.
3. Scroll through Priority Alert cards, click any card, and confirm map/globe animates to that point.
4. Open DevTools Console (`F12`) and test:
   ```javascript
   showCctvQuerying();
   showCctvConfirmed('https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4', 'CAM-802');
   ```
   Confirm the video loads and badge pulses.
