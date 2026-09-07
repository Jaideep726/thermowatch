"""
train.py - Train XGBoost classifier with spatial cross-validation for ThermoWatch.

Uses StratifiedGroupKFold to split by geographic region, preventing the model from
memorizing coordinates. Reports pipeline consistency F1 score.
"""

import xgboost as xgb
import pandas as pd
import numpy as np
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.metrics import classification_report, f1_score
import os

def main():
    print("=" * 70)
    print("ThermoWatch XGBoost Training — Spatial Cross-Validation")
    print("=" * 70)
    
    # Load feature dataset
    df = pd.read_csv("data/processed/firms_features.csv")
    print(f"\nLoaded {len(df)} records from firms_features.csv")
    
    # Map labels to numeric
    label_map = {
        'wildfire': 0,
        'crop_burning': 1,
        'industrial': 2,
        'false_positive': 3
    }
    
    # Filter out uncertain labels
    df = df[df['label'] != 'uncertain'].copy()
    print(f"After filtering 'uncertain': {len(df)} records")
    
    # Check class distribution
    print("\nClass distribution:")
    label_counts = df['label'].value_counts()
    print(label_counts)
    
    # Check if we have enough classes
    unique_labels = df['label'].unique()
    num_classes = len(unique_labels)
    print(f"\nNumber of classes present: {num_classes}")
    
    if num_classes < 2:
        print("\nERROR: Need at least 2 classes for classification")
        return
    
    # Remap labels to be contiguous (0, 1, 2, ...) for the classes we actually have
    actual_label_map = {label: idx for idx, label in enumerate(sorted(unique_labels))}
    print(f"\nActual label mapping: {actual_label_map}")
    
    df['label_num'] = df['label'].map(actual_label_map)
    
    # Import the 12 model features
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from ml.features import MODEL_FEATURES
    
    # Verify all features are present
    missing_features = [f for f in MODEL_FEATURES if f not in df.columns]
    if missing_features:
        print(f"\nERROR: Missing features: {missing_features}")
        return
    
    X = df[MODEL_FEATURES]
    y = df['label_num']
    
    # Create geographic groups (0.5 degree grid cells ~ 55km at equator)
    # This ensures train/test split is by REGION, not random rows
    df['geo_group'] = (
        (df['latitude'] * 2).astype(int).astype(str) + '_' + 
        (df['longitude'] * 2).astype(int).astype(str)
    )
    
    print(f"\nCreated {df['geo_group'].nunique()} geographic groups for spatial CV")
    
    # Check if we have enough groups for the CV split
    n_groups = df['geo_group'].nunique()
    n_splits = min(5, n_groups, len(df) // 10)  # At least 10 samples per fold
    
    if n_splits < 2:
        print(f"\nWARNING: Not enough data for cross-validation. Training on all data.")
        n_splits = 2  # Minimum for StratifiedGroupKFold
    
    print(f"Using {n_splits} folds for cross-validation")
    
    # Spatial cross-validation
    try:
        splitter = StratifiedGroupKFold(n_splits=n_splits, shuffle=True, random_state=42)
    except ValueError as e:
        print(f"\nWARNING: StratifiedGroupKFold failed: {e}")
        print("Falling back to regular StratifiedKFold...")
        from sklearn.model_selection import StratifiedKFold
        splitter = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)
        use_groups = False
    else:
        use_groups = True
    
    best_model = None
    best_f1 = 0
    fold_f1_scores = []
    
    print(f"\nRunning {n_splits}-fold {'Spatial' if use_groups else 'Stratified'} Cross-Validation...")
    print("-" * 70)
    
    split_args = (X, y, df['geo_group']) if use_groups else (X, y)
    for fold, (train_idx, test_idx) in enumerate(splitter.split(*split_args)):
        print(f"\nFold {fold + 1}/{n_splits}")
        
        X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
        y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
        
        print(f"  Train: {len(X_train)} samples, Test: {len(X_test)} samples")
        
        # Train XGBoost
        model = xgb.XGBClassifier(
            n_estimators=300,
            max_depth=6,
            learning_rate=0.08,
            objective='multi:softprob' if num_classes > 2 else 'binary:logistic',
            num_class=num_classes if num_classes > 2 else None,
            eval_metric='mlogloss' if num_classes > 2 else 'logloss',
            random_state=42,
            use_label_encoder=False
        )
        
        model.fit(X_train, y_train, verbose=False)
        
        # Predict on test set
        y_pred = model.predict(X_test)
        
        # Calculate F1 score
        f1 = f1_score(y_test, y_pred, average='weighted')
        fold_f1_scores.append(f1)
        
        print(f"  Weighted F1: {f1:.4f}")
        
        # Keep best model
        if f1 > best_f1:
            best_f1 = f1
            best_model = model
            
            # Print detailed report for best fold
            print(f"\n  Classification Report (Fold {fold + 1}):")
            label_names = sorted(unique_labels)
            try:
                report = classification_report(
                    y_test, y_pred,
                    target_names=label_names,
                    labels=list(range(num_classes)),
                    digits=3,
                    zero_division=0
                )
                print("  " + report.replace("\n", "\n  "))
            except Exception as e:
                print(f"  Could not generate report: {e}")
    
    # Summary statistics
    print("\n" + "=" * 70)
    print("CROSS-VALIDATION SUMMARY")
    print("=" * 70)
    print(f"Mean F1 (Pipeline Consistency): {np.mean(fold_f1_scores):.4f} ± {np.std(fold_f1_scores):.4f}")
    print(f"Best F1 (saved model): {best_f1:.4f}")
    print(f"Min F1: {np.min(fold_f1_scores):.4f}")
    print(f"Max F1: {np.max(fold_f1_scores):.4f}")
    
    # Save best model
    os.makedirs("ml/models", exist_ok=True)
    model_path = "ml/models/thermowatch_xgb.json"
    best_model.save_model(model_path)
    print(f"\nSaved best model to {model_path}")
    
    # Feature importance
    print("\nTop 10 Feature Importances:")
    print("-" * 70)
    feature_importance = pd.DataFrame({
        'feature': MODEL_FEATURES,
        'importance': best_model.feature_importances_
    }).sort_values('importance', ascending=False)
    
    for idx, row in feature_importance.head(10).iterrows():
        print(f"  {row['feature']:25s} {row['importance']:.4f}")
    
    print("\n" + "=" * 70)
    print("✅ Training complete!")
    print("=" * 70)
    print("\nNOTE: This is the PIPELINE CONSISTENCY F1 (model reproducing heuristic labels).")
    print("For GROUND-TRUTH ACCURACY, run the independent validation set (TASK 3).")
    print("=" * 70)

if __name__ == "__main__":
    main()
