# Task PRD — Person 4: Frontend Engineer — 3D Globe

**Your job in one line:** Build the CesiumJS 3D globe that shows every classified fire as a color-coded dot, and the wind-based "where's the fire NOW" cone. This is the single visual judges will remember most.

**Wait for:** Person 3 to have `/api/fires.geojson` live before Task 2 — but you can build Task 1 today using a hand-written sample GeoJSON file.

---

## Before you start
- No install needed — CesiumJS loads from a CDN.
- Register a free Cesium Ion account: https://cesium.com/ion/ — get your access token (needed for the globe/terrain to render).

---

## TASK 1 — CesiumJS boilerplate + globe

**What you're doing:** getting a spinning 3D Earth on screen. This proves your setup works before you add real data.

1. Create `frontend-globe/index.html`:
   ```html
   <!DOCTYPE html>
   <html>
   <head>
     <meta charset="UTF-8">
     <title>ThermoWatch — 3D Globe</title>
     <script src="https://cesium.com/downloads/cesiumjs/releases/1.119/Build/Cesium/Cesium.js"></script>
     <link href="https://cesium.com/downloads/cesiumjs/releases/1.119/Build/Cesium/Widgets/widgets.css" rel="stylesheet">
     <style> html, body, #cesiumContainer { width:100%; height:100%; margin:0; padding:0; } </style>
   </head>
   <body>
     <div id="cesiumContainer"></div>
     <script>
       Cesium.Ion.defaultAccessToken = 'YOUR_CESIUM_TOKEN_HERE';
       const viewer = new Cesium.Viewer('cesiumContainer');
       viewer.camera.flyTo({ destination: Cesium.Cartesian3.fromDegrees(70.0, 22.4, 150000) }); // Jamnagar
     </script>
   </body>
   </html>
   ```
2. Open this file directly in a browser (or run `python -m http.server` inside `frontend-globe/` and visit `localhost:8000`). Confirm the globe loads and flies to Jamnagar.
3. Commit & push:
   ```bash
   git add frontend-globe/index.html
   git commit -m "feat(frontend-globe): CesiumJS boilerplate, flies to Jamnagar"
   git push
   ```

✅ **Checkpoint:** A 3D globe renders in the browser and zooms to Gujarat on load.

---

## TASK 2 — Load classified points from the backend

**What you're doing:** pulling Person 3's GeoJSON and drawing a colored dot for every fire, sized by how intense it is.

1. Add to your `<script>` tag:
   ```javascript
   const colorMap = {
     'wildfire': Cesium.Color.RED,
     'crop_burning': Cesium.Color.YELLOW,
     'industrial': Cesium.Color.fromCssColorString('#9b59b6'),
     'false_positive': Cesium.Color.GRAY.withAlpha(0.4)
   };

   async function loadFireData() {
     const resp = await fetch('http://localhost:8000/api/fires.geojson');
     const data = await resp.json();
     data.features.forEach(f => {
       const { classification, frp } = f.properties;
       const [lon, lat] = f.geometry.coordinates;
       viewer.entities.add({
         position: Cesium.Cartesian3.fromDegrees(lon, lat),
         point: {
           pixelSize: Math.max(6, Math.min(frp / 5, 30)),
           color: colorMap[classification] || Cesium.Color.WHITE,
           outlineColor: Cesium.Color.BLACK,
           outlineWidth: 1
         },
         description: `<b>Type:</b> ${classification}<br><b>FRP:</b> ${frp} MW`
       });
     });
   }
   loadFireData();
   ```
2. **If the backend isn't ready yet**, hardcode a small fake `data` object with 5–10 sample points so you can keep working — swap the fetch URL back in once Person 3 confirms the endpoint is live.
3. Test: confirm red/yellow/purple/gray dots appear on the globe.
4. Commit & push:
   ```bash
   git add frontend-globe/index.html
   git commit -m "feat(frontend-globe): load and color-code classified fire points"
   git push
   ```

✅ **Checkpoint:** Real classified points from the backend render as colored, sized dots on the globe.

---

## TASK 3 — Click-to-inspect + fly-to for demo regions

**What you're doing:** making the demo interactive — clicking a dot shows its details, and buttons let you jump straight to Jamnagar/Punjab/Uttarakhand for the pitch.

1. The `description` field you added in Task 2 already makes clicking a dot show a popup — verify this works by clicking a point.
2. Add simple fly-to buttons above the globe (plain HTML buttons calling `viewer.camera.flyTo(...)` with each region's coordinates):
   ```html
   <div style="position:absolute; top:10px; left:10px; z-index:1;">
     <button onclick="flyTo(70.0,22.4)">Jamnagar</button>
     <button onclick="flyTo(75.5,30.5)">Punjab</button>
     <button onclick="flyTo(79.0,30.3)">Uttarakhand</button>
   </div>
   <script>
     function flyTo(lon, lat) {
       viewer.camera.flyTo({ destination: Cesium.Cartesian3.fromDegrees(lon, lat, 150000) });
     }
   </script>
   ```
3. Commit & push:
   ```bash
   git add frontend-globe/index.html
   git commit -m "feat(frontend-globe): click-to-inspect popups + region fly-to buttons"
   git push
   ```

✅ **Checkpoint:** Clicking a dot shows details; clicking a region button flies the camera there — this is your rehearsed demo flow.

---

## TASK 4 — Wind-based nowcasting cone (label it "illustrative")

**What you're doing:** for wildfires only, draw a translucent cone in the wind's direction showing roughly where the fire might be spreading right now. **This must be labeled as illustrative, not a scientific prediction** — that's a rule from the PRD, not a suggestion.

1. Add:
   ```javascript
   function addWindCone(lon, lat, windSpeed, windDir) {
     const spreadKm = windSpeed * 0.5;
     const dirRad = (windDir * Math.PI) / 180;
     const endLat = lat + (spreadKm / 111) * Math.cos(dirRad);
     const endLon = lon + (spreadKm / (111 * Math.cos(lat * Math.PI/180))) * Math.sin(dirRad);
     viewer.entities.add({
       polygon: {
         hierarchy: Cesium.Cartesian3.fromDegreesArray([lon, lat, endLon - 0.01, endLat, endLon + 0.01, endLat]),
         material: Cesium.Color.RED.withAlpha(0.2),
         outline: true,
         outlineColor: Cesium.Color.RED.withAlpha(0.6)
       },
       description: 'Illustrative nowcast — directional wind-based estimate, not a validated fire-spread model.'
     });
   }
   ```
2. Call `addWindCone(...)` only for points where `classification === 'wildfire'` and `frp > 50`, using wind speed/direction (get this from Person 3's API if they add it, or hardcode a placeholder wind value for now and flag it in your `core.md`).
3. Add a small on-screen legend/label near the cone reading "Illustrative nowcast (wind-based)".
4. Commit & push:
   ```bash
   git add frontend-globe/index.html
   git commit -m "feat(frontend-globe): wind-based nowcasting cone for wildfires, labeled illustrative"
   git push
   ```

✅ **Checkpoint:** Wildfire points show a translucent directional cone, clearly labeled as illustrative.

---

## Your `core.md` file

Create `docs/core_frontend_globe.md`. After each task, append:
- **Tech stack used & why** (e.g., "CesiumJS over deck.gl — better default terrain and lighting, no build step needed for a hackathon")
- **Important findings** (e.g., "Ion token has a rate limit — cache terrain tiles if demo has poor wifi")
- **Problems encountered & how you solved them**
- **Features and how they work**

---

> **Note for AI coding agents assisting with this task:** Only make code changes, run commands, or take actions autonomously if you are 95%+ confident they are correct and match what's described above. If you are below that confidence threshold, stop and ask the user a clarifying question instead of guessing.
