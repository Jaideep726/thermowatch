# ThermoWatch — Product Requirements Document
### SIH PS26162 | AI-Based Detection & Classification of Industrial Fires and Persistent Thermal Sources
**Organization:** NTRO (National Technical Research Organisation) | **Team:** Hexa Hustlers (5E7A7F)
**Doc status:** Consolidated from v1 (Deep Analysis) → v2 → v3 → v4. This is the final, judge-hardened version.

---

## 1. Problem Statement

Build an AI/ML system that takes NASA FIRMS satellite thermal-anomaly data and tells you **what is actually burning**, not just that something is hot.

FIRMS already *detects* heat. It does not *classify* it. Every red dot on a fire map could be:
- 🔴 **Wildfire** — vegetation burning, needs an emergency response
- 🟡 **Crop/stubble burning** — seasonal, agricultural
- 🟣 **Industrial heat source** — refinery flare, kiln, steel plant, running 24/7 on purpose
- ⚫ **False positive** — sun glint, hot rooftop, sensor noise

**ThermoWatch's job**: ingest FIRMS data, fuse it with OpenStreetMap + land-cover context, classify each detection into one of the four categories above, and present it on a decision-support dashboard that a responder can actually act on.

> The deliverable that matters is the **classification**, not the detection. Detection is a solved problem NASA already gives away for free.

---

## 2. Why This Matters — Real-World Impact

**The core failure mode is alert fatigue.** FIRMS produces millions of detections a year globally. Most aren't emergencies. When responders can't tell the difference, they either drown in noise or start ignoring alerts — and real fires slip through.

| Metric | Value | Source |
|---|---|---|
| Fire deaths in India, 2024 | ~5,888 (~16/day) | NCRB ADSI 2024 |
| Historical average, fire deaths/year | 13,000–15,000 | NCRB |
| Factory fire fatality rate | 89 deaths per 100 accidents | NCRB 2024 |
| Forest fire economic loss | ₹1.74 lakh crore/year | FSI |
| Punjab stubble-burning events (2023) | 36,663 | — |
| Delhi NCR population hit by stubble-burning smoke | ~30 million | — |
| Peak AQI during burning season | 400+ (Hazardous) | — |
| FIRMS false-positive rate | 10–30% | Literature |

**What classification actually unlocks:**
- **Faster wildfire response** — filter out the 10–30% that's industrial/noise, and responders only see real emergencies.
- **Targeted stubble-burning enforcement** — pinpoint village-level burns for machinery dispatch and NGT evidence.
- **Accurate carbon accounting** — a forest fire and a gas flare cannot be lumped together in India's Paris Agreement GHG reporting.
- **Insurance & disaster response** — classified, geo-tagged evidence for claims and pre-positioning resources.
- **For NTRO specifically** — unauthorized industrial activity near sensitive zones, cross-border fire impact assessment, and a national thermal-signature catalogue as a strategic asset.

---

## 3. Why FIRMS Can't Do This Itself

Five hard technical limits, not a software gap:

1. **Resolution is too coarse.** MODIS = 1km/pixel, VIIRS = 375m/pixel. A factory, its parking lot, and adjacent forest can share one pixel; the sensor reports one averaged number.
2. **The spectral bands measure heat, not chemistry.** A 900K cement kiln and a 900K biomass fire look identical in mid/long-wave IR.
3. **Sub-pixel mixing.** A small 1,800K gas flare and a large 600K smouldering fire can produce the same pixel-level radiance — the signal can't be decomposed.
4. **No temporal memory per detection.** Each FIRMS row is a single snapshot; it doesn't know if that spot was hot yesterday, last month, or all year.
5. **Environmental interference.** Cloud cover blocks detection; sun glint and hot surfaces cause daytime false positives.

FIRMS' own `type` field is a 4-value heuristic (vegetation / volcano / other static / offshore) — not a real classifier.

---

## 4. Prior Art & Gaps We're Filling

| Approach | What it does | Limitation |
|---|---|---|
| VIIRS Nightfire (NOAA EOG) | Planck curve fitting on multi-band radiance to estimate source temp | Needs L1B swath data, not available via FIRMS API; night-only |
| Liu et al. 2018 (our core reference) | Object-oriented temporal clustering + temperature histogram fingerprints | 77–97% accuracy, but only 4 industrial sub-types; needs the same L1B data we don't have |
| ML on tabular FIRMS features | XGBoost/RF on FRP, brightness temp, persistence | Published 92–95% accuracy — but usually leaks location into the model |
| LULC overlay | Fire-in-forest = wildfire, fire-in-cropland = stubble | Simple, effective as a first-pass filter only |
| Static thermal masks (used by FSI/NRSC today) | Known industrial coordinates excluded from alerts | Binary, can't catch new/unlisted sources |

**The gap nobody has closed operationally**: fusing FIRMS + OSM + LULC + temporal patterns into one **live, multi-class, ground-truthed** pipeline — most of the above lives in research papers or static exclusion lists, not a running system.

---

## 5. Solution Architecture (Final, Judge-Hardened)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      THERMOWATCH — HONEST ARCHITECTURE                  │
├─────────────────────────────────────────────────────────────────────────┤
│  FIRMS API (NRT, ~3hr) ──CSV──┐                                          │
│                                ▼                                         │
│  OSM Overpass (industrial) ──►  LABELING  ───labels──►┌──────────────┐  │
│  LULC (land cover)         ──►  (training only)       │  FASTAPI      │  │
│                                                        │  BACKEND      │  │
│  Weather API ──ambient_temp, region-specific─────────►│  ┌─────────┐  │  │
│                                                        │  │XGBoost  │  │  │
│  FIRMS CSV ───────────────────────────────────────────►  │(sensor +│──┼─►│ CesiumJS
│                                                        │  │temporal │  │  │ 3D Globe
│  Fire video (pre-recorded) ──triggered by high alert──►│  │ only)   │  │  │ + Alerts
│                                                        │  └─────────┘  │  │ + CCTV
│                                                        └──────────────┘  │  panel
│  WHAT'S LIVE:  ML classifier, globe, dashboard, CCTV mock, alerts       │
│  WHAT'S MOCKED: CCTV video feed, INSAT-3DR layer                        │
│  WHAT'S ROADMAP: VNF Planck physics, super-resolution, ICCC API access  │
└─────────────────────────────────────────────────────────────────────────┘
```

### 5.1 The Two Design Decisions That Make This Defensible

**A. Labeling features ≠ model features (fixes the "the model just memorized coordinates" problem)**

| Used only to CREATE labels | Fed to the ML model |
|---|---|
| `dist_to_industrial` | `bright_ti4`, `bright_ti5`, `bright_diff` |
| `dist_to_forest` | `frp`, `confidence_num`, `daynight_num` |
| `land_cover_class` | `hour_of_day`, `temporal_persistence` |
| `is_known_static_source` | `site_temp_std`, `detections_per_month` |
| `month` (for crop-season rule) | `thermal_excess`, `frp_brightness_ratio` |

The model never sees *where* a detection is. It has to learn what a heat source **looks like physically** — sensor readings and behavior over time — not look up an address. This is the single most important design decision in the whole project; it's what survives a PhD-level cross-examination.

**B. Two honest metrics, reported together, not one inflated number**

| Metric | What it measures | Expected range |
|---|---|---|
| Pipeline Consistency (spatial CV) | Can the model reproduce the heuristic labels using sensor data only? | Weighted F1 ~0.82–0.88 |
| Ground-Truth Validation | Does it get real, independently verified events right? (30–50 events from news/FSI bulletins/Google Earth, including at least one site — e.g. Bhilai Steel Plant — never used anywhere in training or labeling) | Accuracy ~75–85% |

> On stage: *"We report both numbers because they mean different things. The first is high but self-referential. The second is lower but real. We trust the second one more."*

### 5.2 Latency Strategy (Tiered Fusion)

| Tier | Source | Latency | Role |
|---|---|---|---|
| 1 — Rapid detection | INSAT-3DR (concept/pitch only) | ~30 min | New-anomaly flagging, coarse LULC classification |
| 2 — Confirmation | FIRMS VIIRS/MODIS NRT (**actually built**) | ~3 hrs | Full ML classification, priority alert |
| 3 — Predictive interpolation | Wind data + last confirmed detection | Continuous | "Illustrative nowcast" cone showing likely current spread — explicitly labeled as directional, not a validated fire-behavior model |

---

## 6. Feature Scope (What Gets Built vs. Pitched)

### Tier 1 — Must Ship (live in the demo)
| # | Feature | Why it's core |
|---|---|---|
| 1 | XGBoost classifier (no feature leakage, independent validation) | The actual product |
| 2 | FastAPI backend — ingest FIRMS CSV, run model, serve GeoJSON | Glue layer |
| 3 | CesiumJS 3D globe — color-coded points, size scaled by FRP | The "wow" the judges see first |
| 4 | Dashboard sidebar — live counts, classification breakdown, click-to-inspect | Turns data into a decision-support tool |

### Tier 2 — Should Ship (build if Tier 1 is solid early)
| # | Feature | Why it's a differentiator |
|---|---|---|
| 5 | IoT/CCTV confirmation mock — satellite alert triggers nearest Smart-City camera check, "✅ VISUALLY CONFIRMED" badge | Nobody else bridges satellite → ground-level video |
| 6 | Priority alert cards (red/amber/green) | Turns raw classification into action |
| 7 | Wind-based nowcasting cone, labeled "illustrative" | Answers "the satellite data is 3 hours old — so what?" |

### Tier 3 — Pitch Only (architecture slide, not built)
| Feature | Why it's roadmap, not real |
|---|---|
| VIIRS Nightfire multi-band Planck physics | Needs NOAA EOG L1B swath data FIRMS doesn't provide |
| Full INSAT-3DR live integration | MOSDAC access is restricted/delayed |
| Thermal super-resolution (SRGAN) | Needs paired LR-HR training data + GPU time we don't have |
| Full ICCC/Smart-City API integration | Requires a municipal MoU, not a hackathon deliverable |

**Honesty is a feature.** Every mocked or pitched item is labeled as such, on-screen, during the demo. This is deliberate — it's what survived two rounds of adversarial judge review.

---

## 7. Data Sources

| Source | What we get | Access |
|---|---|---|
| NASA FIRMS API | Active fire/thermal detections (CSV/JSON) | Free, register at firms.modaps.eosdis.nasa.gov |
| FIRMS Archive | Historical data (2000–present) for training | Free download portal |
| OSM Overpass API | Industrial facility & land-use polygons | Free, no key |
| MODIS MCD12Q1 | Global land cover, 500m | Free, NASA Earthdata |
| OpenWeatherMap | Ambient temperature, wind speed/direction | Free tier, 1000 calls/day |
| MOSDAC (ISRO) | INSAT-3DR thermal products (concept reference only) | Free registration |

**Demo regions:** Jamnagar, Gujarat (persistent refinery flares — Reliance + Nayara); Punjab/Haryana (stubble burning, Oct–Nov archive); Uttarakhand (wildfire season, Mar–Jun archive); Angul, Odisha (mixed industrial + forest edge — "complexity zone").

---

## 8. Risk Register

| Risk | Mitigation |
|---|---|
| FIRMS API key not approved in time | Register immediately; pre-download archive as fallback |
| Model accuracy below 80% | Fall back to 3-class (drop false_positive) or binary (fire/not-fire) |
| CesiumJS lags with many points | Cap at 5–10K points, use clustering / `PointPrimitives` |
| No internet at venue | Pre-cache all FIRMS/OSM/LULC/model files; run fully offline except the live weather call |
| CCTV mock looks fake | Use real Creative-Commons fire footage + realistic camera-ID/timestamp overlay |
| A team member is unavailable | Every module has one owner who documents its API contract so anyone can pick it up |
| Judge doesn't buy the physics | Prepare the one-slide "different fires have different thermal fingerprints" visual, and the two-metric honesty framing |

---

## 9. Success Criteria for the Demo

- Live classification of a real FIRMS feed into 4 categories, visualized on the 3D globe within seconds of load.
- Both accuracy numbers (pipeline consistency + independent ground truth) shown on screen, not just claimed verbally.
- At least one Tier-2 differentiator (CCTV mock or nowcasting cone) working end-to-end.
- Every mocked/roadmap component clearly labeled as such — no claim we can't defend if a judge pushes back.

---

## 10. Anticipated Judge Questions (Rehearsed Answers)

- **"Do you have real CCTV/ICCC access?"** → No — mocked integration; production would need a municipal MoU; swapping in a live feed is a config change, not a rewrite.
- **"Is the fire-spread cone a validated model?"** → No — directional wind-based indicator, labeled "illustrative nowcast," not Rothermel/FARSITE.
- **"Why XGBoost, not deep learning?"** → Input is a 12-feature tabular vector, not an image; gradient-boosted trees outperform NNs on tabular data at this scale (Grinsztajn et al. 2022).
- **"Isn't `temporal_persistence` in both labeling and model features — still circular?"** → Partially, but the labeling rule also requires a distance constraint the model never sees; the model must learn persistence-alone correlation, which is weaker — hence the honest, lower F1. The independent validation set (including a site never used in training, e.g. Bhilai) is the real check.
- **"Is your ambient-temperature data real?"** → Live OpenWeatherMap calls for the live demo; region-specific monthly climatology tables (Jamnagar/Punjab/Uttarakhand each different) for backfilling a year of archive data — flagged explicitly, not presented as live data.

---

## 11. One-Line Demo Script

> "Every year, FIRMS detects millions of thermal anomalies worldwide — and can't tell you what's burning. ThermoWatch classifies those dots using twelve sensor and temporal features, never the location itself. A refinery flare in Jamnagar, stubble burning in Punjab, a wildfire in Uttarakhand — the model tells them apart from their thermal behavior alone. When it flags a likely wildfire, it triggers a Smart-City CCTV check for visual confirmation, and a wind-based cone shows where the fire likely is *right now* — not three hours ago. We report two accuracy numbers, not one, because intellectual honesty matters more than a big number on a slide."

---

## 12. References

1. Liu et al. (2018) — *Identifying industrial heat sources using time-series of the VIIRS Nightfire product with an object-oriented approach*, Remote Sensing of Environment.
2. Ma et al. (2024) — *An industrial heat source dataset based on remotely sensed active fire/hotspot detection in China, 2012–2021*, Geoscience Data Journal.
3. Elvidge et al. (2013) — *VIIRS Nightfire: Satellite Pyrometry at Night*.
4. Schroeder et al. (2014) — *The New VIIRS 375m Active Fire Detection Data Product*.
5. Giglio et al. (2016) — *MODIS Collection 6 Active Fire Product*.
6. Grinsztajn et al. (2022) — *Why do tree-based models still outperform deep learning on tabular data?*

---

*This document consolidates: SIH PS26162 Deep Analysis (v1), Strategy v2 (IoT/CCTV + hybrid physics), Strategy v3 (post first judge-review fixes), and Strategy v4 (post second judge-review fixes — the final, ship-ready version). Where versions conflicted, v4's corrections take precedence.*
