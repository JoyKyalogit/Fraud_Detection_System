from sqlalchemy import create_engine
import pandas as pd
import numpy as np
import joblib
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import (
    classification_report, confusion_matrix, roc_auc_score,
    precision_recall_curve, average_precision_score, f1_score
)
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import warnings
warnings.filterwarnings("ignore")


try:
    from xgboost import XGBClassifier
    USE_XGBOOST = True
    print("XGBoost available — using XGBClassifier")
except ImportError:
    USE_XGBOOST = False
    print("XGBoost not found — falling back to RandomForest. Run: pip install xgboost")

# 1. DATABASE CONNECTION
DB_URL = "postgresql://postgres:jloh@localhost:5432/paysim_fraud_project"

print("\n Connecting to PostgreSQL...")
engine = create_engine(DB_URL)
df = pd.read_sql("SELECT * FROM transactions_clean;", engine)
print(f"   Loaded {len(df):,} rows × {df.shape[1]} columns")


# 2. PREPROCESSING

print("\n Preprocessing...")

# One-hot encode transaction type
df = pd.get_dummies(df, columns=["type"], prefix="type")
df.columns = df.columns.str.lower()

# Log-scale amount (handles extreme values like 500B transactions)
df["amount_log"] = np.log1p(df["amount"])

# Check class balance
fraud_count = df["isfraud"].sum()
total = len(df)
fraud_pct = fraud_count / total * 100
print(f"   Class balance → Legitimate: {total - fraud_count:,} ({100 - fraud_pct:.2f}%) | Fraud: {fraud_count:,} ({fraud_pct:.2f}%)")


# 3. FEATURE SELECTION

FEATURES = [
    "amount_log", "isflaggedfraud", "large_txn_flag",
    "high_risk_type_flag", "odd_hour_flag", "frequent_txn_flag",
    "new_sender_flag", "type_cash_out", "type_transfer",
    "type_debit", "type_payment", "type_cash_in"
]

# Add missing columns as 0 (safety for missing transaction types in data)
for col in FEATURES:
    if col not in df.columns:
        df[col] = 0
        print(f"   Column '{col}' not found in data — added as zeros")

X = df[FEATURES]
y = df["isfraud"]

print(f"   Features: {len(FEATURES)} | Target: 'isfraud'")


# 4. TRAIN / TEST SPLIT (stratified to preserve fraud ratio)

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)
print(f"\n Split → Train: {len(X_train):,} | Test: {len(X_test):,}")


# 5. MODEL DEFINITION

scale_pos_weight = (y_train == 0).sum() / (y_train == 1).sum()

if USE_XGBOOST:
    model = XGBClassifier(
        n_estimators=300,
        max_depth=6,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        scale_pos_weight=scale_pos_weight,  # handles class imbalance
        random_state=42,
        n_jobs=-1,
        eval_metric="aucpr",
        verbosity=0,
    )
else:
    model = RandomForestClassifier(
        n_estimators=150,
        max_depth=25,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1,
    )


# 6. CROSS-VALIDATION (before final fit)

print("\n Running 5-fold cross-validation (ROC-AUC)...")
cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
cv_scores = cross_val_score(model, X_train, y_train, cv=cv, scoring="roc_auc", n_jobs=-1)
print(f"   CV ROC-AUC: {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")
print(f"   Per fold:   {[f'{s:.4f}' for s in cv_scores]}")


# 7. FINAL TRAINING

print("\n Training final model on full training set...")
model.fit(X_train, y_train)
print("   Training complete!")


# 8. EVALUATION

print("\n Evaluating on held-out test set...")

y_pred_proba = model.predict_proba(X_test)[:, 1]

# Use threshold 0.3 
THRESHOLD = 0.3
y_pred = (y_pred_proba >= THRESHOLD).astype(int)

# Core metrics
roc_auc = roc_auc_score(y_test, y_pred_proba)
avg_precision = average_precision_score(y_test, y_pred_proba)
f1 = f1_score(y_test, y_pred)

print(f"\n   {'Metric':<25} {'Value':>10}")
print(f"   {'─'*36}")
print(f"   {'ROC-AUC Score':<25} {roc_auc:>10.4f}")
print(f"   {'Avg Precision (PR-AUC)':<25} {avg_precision:>10.4f}")
print(f"   {'F1 Score (t=0.30)':<25} {f1:>10.4f}")

print(f"\n Classification Report (threshold = {THRESHOLD}):")
print(classification_report(y_test, y_pred, target_names=["Legitimate", "Fraud"]))

# Confusion matrix values
tn, fp, fn, tp = confusion_matrix(y_test, y_pred).ravel()
print(f"   Confusion Matrix:")
print(f"   True Positives  (caught fraud):    {tp:>8,}")
print(f"   False Positives (false alarms):    {fp:>8,}")
print(f"   True Negatives  (correct approve): {tn:>8,}")
print(f"   False Negatives (missed fraud):    {fn:>8,}")
print(f"\n   Fraud catch rate (Recall): {tp / (tp + fn) * 100:.1f}%")
print(f"   False alarm rate:          {fp / (fp + tn) * 100:.1f}%")


# 9. FEATURE IMPORTANCE

print("\n Feature Importance:")
if USE_XGBOOST:
    importances = model.feature_importances_
else:
    importances = model.feature_importances_

feat_df = pd.DataFrame({
    "Feature": FEATURES,
    "Importance": importances
}).sort_values("Importance", ascending=False)

for _, row in feat_df.iterrows():
    bar = "█" * int(row["Importance"] * 50)
    print(f"   {row['Feature']:<25} {bar:<30} {row['Importance']:.4f}")


# 10. THRESHOLD ANALYSIS (helps you decide if 0.3 is the right threshold)

print("\n Threshold Sensitivity Analysis:")
print(f"   {'Threshold':<12} {'Precision':>10} {'Recall':>10} {'F1':>10} {'Flagged%':>10}")
print(f"   {'─'*54}")
for thresh in [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7]:
    preds = (y_pred_proba >= thresh).astype(int)
    from sklearn.metrics import precision_score, recall_score
    if preds.sum() > 0:
        p = precision_score(y_test, preds, zero_division=0)
        r = recall_score(y_test, preds, zero_division=0)
        f = f1_score(y_test, preds, zero_division=0)
        flagged = preds.mean() * 100
        marker = " ← current" if thresh == THRESHOLD else ""
        print(f"   {thresh:<12.1f} {p:>10.3f} {r:>10.3f} {f:>10.3f} {flagged:>9.2f}%{marker}")

# 11. SAVE MODEL

MODEL_PATH = "fraud_model.pkl"
joblib.dump(model, MODEL_PATH)
print(f"\n Model saved → {MODEL_PATH}")
print(f"   Algorithm:  {'XGBoost' if USE_XGBOOST else 'RandomForest'}")
print(f"   Features:   {len(FEATURES)}")
print(f"   ROC-AUC:    {roc_auc:.4f}")
print(f"   Threshold:  {THRESHOLD}")
print(f"\n Done! Run: uvicorn deploy:app --reload")