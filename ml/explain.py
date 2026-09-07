"""
explain.py - Generate explainability charts for the ThermoWatch classifier.

Creates feature importance and confusion matrix visualizations for the demo.
"""

import xgboost as xgb
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import confusion_matrix
from sklearn.model_selection import StratifiedGroupKFold
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ml.features import MODEL_FEATURES

def plot_feature_importance(model, save_path="ml/models/feature_importance.png"):
    """Generate and save feature importance bar chart."""
    print("Generating feature importance chart...")
    
    importance_df = pd.DataFrame({
        'feature': MODEL_FEATURES,
        'importance': model.feature_importances_
    }).sort_values('importance', ascending=True)
    
    plt.figure(figsize=(10, 8))
    plt.barh(importance_df['feature'], importance_df['importance'], color='steelblue')
    plt.xlabel('Importance Score', fontsize=12)
    plt.ylabel('Feature', fontsize=12)
    plt.title('ThermoWatch Model — Feature Importance\n(What the AI uses to classify thermal detections)', 
              fontsize=14, fontweight='bold')
    plt.grid(axis='x', alpha=0.3)
    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"✓ Saved to {save_path}")
    plt.close()

def plot_confusion_matrix(y_true, y_pred, labels, save_path="ml/models/confusion_matrix.png"):
    """Generate and save confusion matrix heatmap."""
    print("Generating confusion matrix...")
    
    cm = confusion_matrix(y_true, y_pred)
    
    plt.figure(figsize=(8, 6))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
                xticklabels=labels, yticklabels=labels,
                cbar_kws={'label': 'Count'})
    plt.xlabel('Predicted Label', fontsize=12)
    plt.ylabel('True Label', fontsize=12)
    plt.title('ThermoWatch Model — Confusion Matrix\n(Spatial Cross-Validation)', 
              fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"✓ Saved to {save_path}")
    plt.close()

def plot_class_distribution(df, save_path="ml/models/class_distribution.png"):
    """Plot class distribution in training data."""
    print("Generating class distribution chart...")
    
    plt.figure(figsize=(10, 6))
    counts = df['label'].value_counts()
    colors = {'industrial': '#e74c3c', 'wildfire': '#f39c12', 
              'crop_burning': '#27ae60', 'false_positive': '#95a5a6'}
    bar_colors = [colors.get(label, 'gray') for label in counts.index]
    
    plt.bar(counts.index, counts.values, color=bar_colors, alpha=0.8, edgecolor='black')
    plt.xlabel('Class', fontsize=12)
    plt.ylabel('Number of Samples', fontsize=12)
    plt.title('Training Data Distribution\n(After weak-supervision labeling)', 
              fontsize=14, fontweight='bold')
    plt.xticks(rotation=45, ha='right')
    plt.grid(axis='y', alpha=0.3)
    
    # Add count labels on bars
    for i, (label, count) in enumerate(counts.items()):
        plt.text(i, count + 1, str(count), ha='center', va='bottom', fontweight='bold')
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"✓ Saved to {save_path}")
    plt.close()

def main():
    print("=" * 70)
    print("ThermoWatch — Generating Explainability Charts")
    print("=" * 70)
    
    # Load data
    df = pd.read_csv("data/processed/firms_features.csv")
    df = df[df['label'] != 'uncertain'].copy()
    
    print(f"\nLoaded {len(df)} training samples")
    print(f"Classes: {df['label'].unique()}")
    
    # Map labels
    unique_labels = sorted(df['label'].unique())
    label_map = {label: idx for idx, label in enumerate(unique_labels)}
    df['label_num'] = df['label'].map(label_map)
    
    X = df[MODEL_FEATURES]
    y = df['label_num']
    
    # Load model
    model_path = "ml/models/thermowatch_xgb.json"
    if not os.path.exists(model_path):
        print(f"ERROR: Model not found at {model_path}. Run ml/train.py first.")
        return
    
    model = xgb.XGBClassifier()
    model.load_model(model_path)
    print(f"\nLoaded model from {model_path}")
    
    # Create output directory
    os.makedirs("ml/models", exist_ok=True)
    
    # 1. Feature Importance
    plot_feature_importance(model)
    
    # 2. Class Distribution
    plot_class_distribution(df)
    
    # 3. Confusion Matrix (from cross-validation)
    print("\nGenerating confusion matrix from spatial CV predictions...")
    
    df['geo_group'] = (
        (df['latitude'] * 2).astype(int).astype(str) + '_' + 
        (df['longitude'] * 2).astype(int).astype(str)
    )
    
    # Get predictions from one CV fold for visualization
    splitter = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=42)
    for train_idx, test_idx in splitter.split(X, y, df['geo_group']):
        X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
        y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
        
        fold_model = xgb.XGBClassifier(
            n_estimators=300, max_depth=6, learning_rate=0.08,
            objective='binary:logistic' if len(unique_labels) == 2 else 'multi:softprob',
            random_state=42, use_label_encoder=False
        )
        fold_model.fit(X_train, y_train, verbose=False)
        y_pred = fold_model.predict(X_test)
        
        plot_confusion_matrix(y_test, y_pred, unique_labels)
        break  # Just use first fold for visualization
    
    print("\n" + "=" * 70)
    print("✅ All charts generated successfully!")
    print("=" * 70)
    print("\nGenerated files:")
    print("  - ml/models/feature_importance.png")
    print("  - ml/models/confusion_matrix.png")
    print("  - ml/models/class_distribution.png")
    print("\nThese charts are ready for the pitch deck and demo.")
    print("=" * 70)

if __name__ == "__main__":
    main()
