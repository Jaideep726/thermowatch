# Task PRD — Person 6: Integration & Pitch Lead

**Your job in one line:** Wire the CCTV mock into the live system, glue every teammate's piece together, keep the risk list honest, and own the final pitch. You're the one who makes sure everyone else's work actually adds up to a working demo.

**Wait for:** Person 5's CCTV panel functions (Task 3) to exist before Task 1 below.

---

## Before you start
- No special install — you'll mostly be writing glue JS and editing/testing the combined app.
- Download a Creative Commons fire/smoke video clip in advance — search "FireNet dataset Kaggle" or any royalty-free fire/smoke stock clip. Save it into `integration/cctv_mock_video.mp4`.

---

## TASK 1 — CCTV mock trigger logic

**What you're doing:** the moment a wildfire is classified with high confidence, this logic pretends to "query the nearest CCTV camera" and shows the confirmation — this is the differentiator feature that separates us from every other satellite-only dashboard.

1. Confirm with Person 5 the exact function names they exposed (`showCctvQuerying()`, `showCctvConfirmed(videoUrl, cameraId)`).
2. Add trigger logic (in `frontend-globe/index.html`, after `loadFireData()` runs, or a new `integration/trigger.js` included via `<script>`):
   ```javascript
   function checkForCctvTrigger(features) {
     const highConfidenceWildfire = features.find(
       f => f.properties.classification === 'wildfire' && f.properties.frp > 80
     );
     if (highConfidenceWildfire) {
       showCctvQuerying();
       setTimeout(() => {
         showCctvConfirmed('integration/cctv_mock_video.mp4', 'JMG-CAM-2847');
       }, 2000); // simulate ~2 second "checking" delay
     }
   }
   ```
3. Call `checkForCctvTrigger(data.features)` inside the existing `loadFireData()` function (coordinate with Person 4/5 on exactly where).
4. Test end-to-end: load the page, confirm the panel goes "Querying..." then shows the confirmed video + badge automatically when a wildfire is present in the data.
5. Commit & push:
   ```bash
   git add integration/trigger.js integration/cctv_mock_video.mp4
   git commit -m "feat(integration): CCTV mock trigger logic wired to live classification"
   git push
   ```

✅ **Checkpoint:** Loading the dashboard with real data auto-triggers the CCTV confirmation flow — no manual clicking needed.

---

## TASK 2 — End-to-end integration test

**What you're doing:** running the whole system together, start to finish, and writing down everything that breaks.

1. Start all 3 services locally:
   - Backend: `uvicorn backend.main:app --reload`
   - Frontend: open `frontend-globe/index.html` (or serve it with `python -m http.server`)
2. Walk through the full flow yourself: globe loads → points appear → sidebar counts match → alert cards show → clicking a wildfire region triggers the CCTV panel → wind cone appears on wildfires.
3. Create `docs/integration_test_log.md` and log every bug found, who it was routed to, and whether it's fixed. Format:
   ```
   | Bug | Found by | Routed to | Status |
   |---|---|---|---|
   | Sidebar counts don't match globe dots | P6 | P5 | Fixed |
   ```
4. Commit & push:
   ```bash
   git add docs/integration_test_log.md
   git commit -m "test(integration): end-to-end test pass, bug log"
   git push
   ```

✅ **Checkpoint:** You've personally run the full demo flow at least twice without a crash.

---

## TASK 3 — Offline/no-internet safety net

**What you're doing:** making sure the demo survives bad wifi at the venue (a very real risk called out in the PRD).

1. Confirm with Person 3 that `backend/latest_fires.geojson` (a pre-computed fallback) exists and loads even without live FIRMS API access.
2. Confirm the CCTV video file is a local file, not a URL that requires internet.
3. Confirm Cesium Ion terrain isn't a hard dependency — if the venue wifi fails, check whether `new Cesium.Viewer('cesiumContainer')` (default, no custom terrain) still works offline-ish, or agree with Person 4 on a lightweight terrain fallback.
4. Write a one-page "Demo Day Checklist" in `docs/demo_day_checklist.md`: what to start, in what order, and what to do if X breaks.
5. Commit & push:
   ```bash
   git add docs/demo_day_checklist.md
   git commit -m "docs(integration): demo day checklist + offline safety net"
   git push
   ```

✅ **Checkpoint:** The team has a written plan for "wifi dies 5 minutes before our slot."

---

## TASK 4 — Pitch deck + demo script

**What you're doing:** turning the PRD into a spoken performance. Judges remember confidence and honesty, not jargon.

1. Build a short slide deck (Google Slides/PPT) covering: Problem → Impact stats → Why FIRMS can't classify → Our architecture → Live demo → Both accuracy numbers → Roadmap (Tier 3 items, clearly labeled) → Team.
2. Use the "One-Line Demo Script" from the main PRD (Section 11) as your base — rehearse it out loud with the actual live dashboard, not slides.
3. Review the "Anticipated Judge Questions" section (Section 10 of the PRD) as a team — assign who answers what if asked live.
4. Save the deck into `docs/pitch_deck.pptx` (or a link to it, if using Google Slides, pasted into `docs/pitch_deck_link.md`).
5. Commit & push:
   ```bash
   git add docs/pitch_deck_link.md
   git commit -m "docs(integration): pitch deck + rehearsed demo script"
   git push
   ```

✅ **Checkpoint:** Full team has rehearsed the demo at least once, live, end-to-end, out loud.

---

## Your `core.md` file

Create `docs/core_integration_lead.md`. After each task, append:
- **Tech stack used & why** (e.g., "Plain JS trigger logic, no framework — simplest way to glue two files quickly")
- **Important findings** (bugs found, timing issues, what broke during rehearsal)
- **Problems encountered & how you solved them**
- **Features and how they work**

---

> **Note for AI coding agents assisting with this task:** Only make code changes, run commands, or take actions autonomously if you are 95%+ confident they are correct and match what's described above. If you are below that confidence threshold, stop and ask the user a clarifying question instead of guessing.
