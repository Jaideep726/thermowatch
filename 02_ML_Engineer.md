# Task PRD — Person 2: ML Engineer

**Your job in one line:** Turn the labeled data from Person 1 into a working classifier that guesses "wildfire / crop burning / industrial / false positive" from sensor readings alone — never from location.

**Wait for:** Person 1 to push `data/processed/firms_labeled.csv` (their Task 4) before you can fully finish Task 2 below. You can start Task 1 (env setup) immediately in parallel.

---

## Before you start
```bash
git clone https://github.com/<org>/thermowatch.git
cd thermowatch
python -m venv venv
source venv/bin/activate   # on Windows: venv\Scripts\activate
pip install xgboost pandas scikit-learn numpy matplotlib seaborn
```

---

## TASK 1 — Environment + feature engineering script

**What you're doing:** computing the 12 "model features" — the numbers the AI is actually allowed to learn from. This is the single most important list in the whole project: it must NOT include distance-to-industrial, land-cover, or anything location-based. Those are for labeling only (Person 1's job).

1. Create `ml/features.py`. Your final feature list (copy exactly):
   ```python
   MODEL_FEATURES = [
       'bright_ti4', 'bright_ti5', 'bright_diff', 'frp',
       'confidence_num', 'daynight_num', 'hour_of_day',
       'temporal_persistence', 'site_temp_std', 'detections_per_month',
       'thermal_excess', 'frp_brightness_ratio',
   ]
   ```
2. Write functions to compute the derived ones from `data/processed/firms_labeled.csv`:
   - `bright_diff = bright_ti4 - bright_ti5`
   - `temporal_persistence` = count of detections within 1km & 30 days of this point
   - `site_temp_std` = std deviation of `bright_ti4` at this same location over time
   - `detections_per_month` = detections at this site / month-span of data at that site
   - `thermal_excess = bright_ti4 - ambient_temp` (use a simple monthly climatology table — **use a different table per region**, don't apply Jamnagar's numbers to Uttarakhand, that silently breaks the wildfire class)
   - `frp_brightness_ratio = frp / bright_ti4`
3. Save output as `data/processed/firms_features.csv`.
4. Commit & push:
   ```bash
   git add ml/features.py data/processed/firms_features.csv
   git commit -m "feat(ml): feature engineering pipeline, 12 model features"
   git push
   ```

✅ **Checkpoint:** A CSV exists with all 12 model features computed correctly, per-region ambient temp used.

---

## TASK 2 — Train XGBoost with spatial cross-validation

**What you're doing:** training the classifier the RIGHT way — splitting train/test by geographic region, not randomly, so the model can't cheat by memorizing coordinates.

1. Create `ml/train.py`:
   ```python
   import xgboost as xgb
   import pandas as pd
   import numpy as np
   from sklearn.model_selection import StratifiedGroupKFold
   from sklearn.metrics import classification_report

   df = pd.read_csv("data/processed/firms_features.csv")
   label_map = {'wildfire': 0, 'crop_burning': 1, 'industrial': 2, 'false_positive': 3}
   df = df[df['label'] != 'uncertain'].copy()
   df['label_num'] = df['label'].map(label_map)

   from ml.features import MODEL_FEATURES
   X = df[MODEL_FEATURES]
   y = df['label_num']

   df['geo_group'] = (df['latitude']*2).astype(int).astype(str) + '_' + (df['longitude']*2).astype(int).astype(str)

   splitter = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=42)
   best_model, best_f1 = None, 0

   for fold, (tr, te) in enumerate(splitter.split(X, y, df['geo_group'])):
       model = xgb.XGBClassifier(n_estimators=300, max_depth=6, learning_rate=0.08,
                                  objective='multi:softprob', num_class=4, eval_metric='mlogloss')
       model.fit(X.iloc[tr], y.iloc[tr])
       preds = model.predict(X.iloc[te])
       report = classification_report(y.iloc[te], preds, output_dict=True)
       f1 = report['weighted avg']['f1-score']
       print(f"Fold {fold+1}: F1 = {f1:.3f}")
       if f1 > best_f1:
           best_f1, best_model = f1, model

   best_model.save_model("ml/models/thermowatch_xgb.json")
   print(f"Best pipeline-consistency F1: {best_f1:.3f}")
   ```
2. Run it: `python ml/train.py`
3. Commit & push:
   ```bash
   git add ml/train.py ml/models/thermowatch_xgb.json
   git commit -m "feat(ml): trained XGBoost model with spatial CV"
   git push
   ```

✅ **Checkpoint:** `thermowatch_xgb.json` model file exists. You have a "pipeline consistency F1" number (expect ~0.82–0.88).

---

## TASK 3 — Build the independent validation set (the honesty check)

**What you're doing:** manually curating 30–50 real, independently-verified events (NOT from the heuristic labeling) so we can report a second, more trustworthy accuracy number.

1. Create `ml/independent_validation_set.csv` with columns: `latitude, longitude, confirmed_label, source_url, verification_method` — fill with real events, e.g.:
   - Uttarakhand forest fire, June 2024 (from news/FSI bulletin) → `wildfire`
   - Jamnagar Reliance refinery flare (visually confirmed on Google Earth) → `industrial`
   - Punjab stubble burning Oct 2023 (IARI CREAMS confirmed) → `crop_burning`
   - **Important:** include at least one site NEVER used anywhere in training/labeling — e.g. Bhilai Steel Plant, Chhattisgarh — this is what makes "independent" actually true.
2. Aim for 30–50 rows total across all 4 categories.
3. Compute the same 12 model features for each row (reuse `ml/features.py` logic).
4. Run the trained model on this set, print `classification_report`.
5. Note both numbers (pipeline F1 + this ground-truth accuracy) clearly in your `core.md`.
6. Commit & push:
   ```bash
   git add ml/independent_validation_set.csv
   git commit -m "feat(ml): independent validation set + ground-truth accuracy"
   git push
   ```

✅ **Checkpoint:** You can state, out loud, two numbers: pipeline consistency F1 and ground-truth accuracy.

---

## TASK 4 — Export explainability charts for the demo

**What you're doing:** making the "why did it classify this as X" chart and the confusion matrix — judges love this, and it's cheap to build.

1. Add to `ml/train.py` (or a new `ml/explain.py`):
   - Feature importance bar chart (`xgb.plot_importance(best_model)`), save as `ml/models/feature_importance.png`
   - Confusion matrix heatmap (use `seaborn.heatmap` + `sklearn.metrics.confusion_matrix`), save as `ml/models/confusion_matrix.png`
2. Commit & push:
   ```bash
   git add ml/models/feature_importance.png ml/models/confusion_matrix.png
   git commit -m "feat(ml): explainability charts for demo"
   git push
   ```

✅ **Checkpoint:** Two PNG charts exist, ready to drop into the pitch deck.

---

## Your `core.md` file

Create `docs/core_ml_engineer.md`. After each task, append:
- **Tech stack used & why** (e.g., "XGBoost over a neural net because our input is tabular, not images — trains in minutes")
- **Important findings** (e.g., "Wildfire recall dropped to ~80% once we removed dist_to_forest from model features — expected, and more honest")
- **Problems encountered & how you solved them**
- **Features and how they work** (what each script/file does)

---

> **Note for AI coding agents assisting with this task:** Only make code changes, run commands, or take actions autonomously if you are 95%+ confident they are correct and match what's described above. If you are below that confidence threshold, stop and ask the user a clarifying question instead of guessing.
