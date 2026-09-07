# Task PRD — Person 5: Frontend Engineer — Dashboard

**Your job in one line:** Build the sidebar around Person 4's globe — the live stats, the color-coded priority alert cards, and the CCTV confirmation panel. This is what turns "pretty globe" into "decision-support tool."

**Wait for:** Person 4's `frontend-globe/index.html` to exist (Task 1) — you'll be adding a sidebar `<div>` next to their globe container, so coordinate on the file structure early.

---

## Before you start
- No install needed — plain HTML/CSS/JS, same file as Person 4's globe (or a `sidebar.js` they import — agree with them which).

---

## TASK 1 — Sidebar layout with live stat boxes

**What you're doing:** a panel showing total anomalies and a breakdown by category, updating from real data.

1. Talk to Person 4 first — confirm you're both editing `frontend-globe/index.html` (recommended for a hackathon, simplest) or you're building `frontend-dashboard/sidebar.html` that they `<iframe>` in. **Write this decision in your core.md.**
2. Add the sidebar HTML + CSS:
   ```html
   <div id="sidebar" style="position:absolute; top:0; right:0; width:300px; height:100vh;
        background:#1a1a2e; color:white; padding:15px; overflow-y:auto; z-index:1;">
     <h2>🔥 ThermoWatch</h2>
     <p style="color:#888;">AI Thermal Intelligence Platform</p>
     <div style="display:flex; flex-wrap:wrap; gap:8px;">
       <div class="stat-box"><h3 id="total-count">--</h3><small>Total</small></div>
       <div class="stat-box"><h3 id="wildfire-count" style="color:red">--</h3><small>Wildfires</small></div>
       <div class="stat-box"><h3 id="industrial-count" style="color:#9b59b6">--</h3><small>Industrial</small></div>
       <div class="stat-box"><h3 id="crop-count" style="color:yellow">--</h3><small>Crop Burns</small></div>
     </div>
   </div>
   <style>
     .stat-box { flex:1 1 45%; background:rgba(255,255,255,0.1); border-radius:8px;
                 padding:10px; text-align:center; }
   </style>
   ```
3. In the same `loadFireData()` function Person 4 wrote (or a copy you add after it runs), count classifications and update the DOM:
   ```javascript
   let counts = { wildfire: 0, crop_burning: 0, industrial: 0, false_positive: 0 };
   data.features.forEach(f => counts[f.properties.classification]++);
   document.getElementById('total-count').textContent = Object.values(counts).reduce((a,b)=>a+b,0);
   document.getElementById('wildfire-count').textContent = counts.wildfire;
   document.getElementById('industrial-count').textContent = counts.industrial;
   document.getElementById('crop-count').textContent = counts.crop_burning;
   ```
4. Commit & push:
   ```bash
   git add frontend-globe/index.html   # or frontend-dashboard/sidebar.html, per your decision
   git commit -m "feat(dashboard): sidebar with live classification stat boxes"
   git push
   ```

✅ **Checkpoint:** Sidebar shows real, live counts that match the dots on the globe.

---

## TASK 2 — Priority alert cards (red/amber/green)

**What you're doing:** the thing that makes a responder's job easier — instead of reading 500 dots, they see a short, ranked list of what actually needs attention right now.

1. Define a simple priority rule (documented — you can tune it):
   - **Red**: `classification == 'wildfire' AND frp > 100`
   - **Amber**: `classification == 'wildfire' AND frp <= 100` OR (`classification == 'industrial' AND is near a population center — skip this check if you don't have population data, just use wildfire+frp for now`)
   - **Green**: everything else classified as a real fire type (not false_positive)
2. Add an alerts container to the sidebar:
   ```html
   <h3>🚨 Priority Alerts</h3>
   <div id="alerts-container"></div>
   ```
3. In your JS, after loading fire data, build alert cards for the top ~10 highest-FRP wildfire/industrial points:
   ```javascript
   function renderAlerts(features) {
     const container = document.getElementById('alerts-container');
     const sorted = features.filter(f => f.properties.classification !== 'false_positive')
                             .sort((a,b) => b.properties.frp - a.properties.frp)
                             .slice(0, 10);
     container.innerHTML = sorted.map(f => {
       const level = f.properties.frp > 100 ? 'red' : (f.properties.frp > 30 ? 'amber' : 'green');
       return `<div class="alert-card alert-${level}">
                 <b>${f.properties.classification.toUpperCase()}</b><br>
                 FRP: ${f.properties.frp} MW
               </div>`;
     }).join('');
   }
   ```
   ```css
   .alert-card { padding:10px; margin:8px 0; border-radius:8px; }
   .alert-red { background:rgba(255,0,0,0.3); border-left:4px solid red; }
   .alert-amber { background:rgba(255,165,0,0.3); border-left:4px solid orange; }
   .alert-green { background:rgba(0,255,0,0.2); border-left:4px solid green; }
   ```
4. **Nice-to-have if time allows:** clicking an alert card flies the globe camera to that point (call Person 4's `flyTo` function, or `viewer.flyTo` on that specific entity).
5. Commit & push:
   ```bash
   git add frontend-globe/index.html
   git commit -m "feat(dashboard): priority alert cards, ranked by FRP"
   git push
   ```

✅ **Checkpoint:** Top 10 real alerts show as color-coded cards, ranked by intensity.

---

## TASK 3 — CCTV confirmation panel (UI shell)

**What you're doing:** building the visual panel that Person 6 (Integration Lead) will wire up with the actual mock-video trigger logic. You build the box; they make it light up.

1. Add to the sidebar:
   ```html
   <h3>📹 CCTV Verification</h3>
   <div class="cctv-panel" id="cctv-panel" style="background:#000; border:2px solid #0f0;
        border-radius:4px; text-align:center; padding:10px;">
     <p style="color:#666;">Awaiting satellite trigger...</p>
   </div>
   ```
2. Expose two simple global functions Person 6 will call from their trigger logic:
   ```javascript
   function showCctvQuerying() {
     document.getElementById('cctv-panel').innerHTML = '<p style="color:orange;">Querying nearest CCTV...</p>';
   }
   function showCctvConfirmed(videoUrl, cameraId) {
     document.getElementById('cctv-panel').innerHTML = `
       <video src="${videoUrl}" autoplay loop muted width="100%"></video>
       <p class="confirmed-badge">✅ VISUALLY CONFIRMED — Camera ${cameraId}</p>`;
   }
   ```
   ```css
   .confirmed-badge { background:#00cc44; padding:4px 12px; border-radius:12px; font-weight:bold;
                       animation: pulse 1.5s infinite; }
   @keyframes pulse { 0%,100% { opacity:1; } 50% { opacity:0.6; } }
   ```
3. **Document these two function names clearly in your `core.md`** — Person 6 needs to know exactly what to call and with what arguments.
4. Commit & push:
   ```bash
   git add frontend-globe/index.html
   git commit -m "feat(dashboard): CCTV panel UI shell + trigger functions for integration"
   git push
   ```

✅ **Checkpoint:** The CCTV panel exists and can be triggered by calling your two functions from the browser console — confirm this works before handing off to Person 6.

---

## Your `core.md` file

Create `docs/core_frontend_dashboard.md`. After each task, append:
- **Tech stack used & why**
- **Important findings** (e.g., the exact function names/contract you exposed for Person 6)
- **Problems encountered & how you solved them**
- **Features and how they work**

---

> **Note for AI coding agents assisting with this task:** Only make code changes, run commands, or take actions autonomously if you are 95%+ confident they are correct and match what's described above. If you are below that confidence threshold, stop and ask the user a clarifying question instead of guessing.
