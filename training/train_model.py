from pathlib import Path
import joblib
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, roc_auc_score
import lightgbm as lgb

BASE_DIR= Path(__file__).resolve().parent.parent
dataset_path= BASE_DIR/"data"/"processed"/"processed_fraud_dataset.csv"
df=pd.read_csv(dataset_path)
print(f"\nDataset loaded: {len(df)} rows | {df['is_fraud'].sum()} fraud cases")
print(df.head())

FEATURE_COLUMNS = [
    "amount", "avg_amount", "max_amount", "amount_ratio",
    "amount_std", "amount_zscore",
    "is_new_location", "is_new_device", "impossible_travel",
    "transactions_last_10min", "transactions_last_1hr", "transactions_last_24hr",
    "transactions_last_7d", "amount_last_1hr", "amount_last_24hr",
    "unique_merchants_last_24hr",
    "num_unique_devices_30d", "device_first_seen_days", "is_unknown_device_type",
    "is_high_risk_merchant", "merchant_fraud_rate", "amount_vs_merchant_avg",
    "merchant_category_risk",
    "is_high_risk_location",
    "hour_of_day", "is_night", "is_weekend", "day_of_week",
    "time_since_last_txn_hours", "is_round_amount",
]

X= df[FEATURE_COLUMNS]
y_true=df["is_fraud"]


#MODEL 1: ISOLATION FOREST

print("\n Training Isolation Forest")
iso_model= IsolationForest(
    n_estimators=200,
    contamination=0.05,
    random_state=42,
    n_jobs=-1
)
iso_model.fit(X)
iso_preds= iso_model.predict(X)
iso_y_pred= [1 if p==-1 else 0 for p in iso_preds]
print("Isolation Forest Report:")
print(classification_report(y_true, iso_y_pred))


#MODEL 2: LOCAL OUTLIER FACTOR

print("\n Training Local Outlier Factor")
lof_model= LocalOutlierFactor(
    n_neighbors=20,
    contamination=0.05,
    novelty=True,
    n_jobs=-1
)
lof_model.fit(X)
lof_preds= lof_model.predict(X)
lof_y_pred= [1 if p == -1 else 0 for p in lof_preds]
print("Local Outlier Factor Report:")
print(classification_report(y_true, lof_y_pred))


#MODEL 3: LIGHTGBM (supervised)

print("\n Training LightGBM")
X_train, X_val, y_train, y_val= train_test_split(
    X,y_true,
    test_size=0.2,
    random_state=42,
    stratify=y_true
)
fraud_count= y_train.sum()
normal_count= len(y_train)-fraud_count
scale_pos_weight= normal_count/fraud_count
print(f"Fraud count: {fraud_count} | Normal count: {normal_count}")
print(f"scale_pos_weight: {scale_pos_weight:.1f}")
lgbm_model= lgb.LGBMClassifier(
    n_estimators=500,
    learning_rate=0.05,
    max_depth=6,
    num_leaves=31,
    scale_pos_weight=scale_pos_weight,
    random_state=42,
    n_jobs=-1,
    verbose=-1
)

lgbm_model.fit(
    X_train,y_train,
    eval_set=[(X_val,y_val)],
)

lgbm_probs= lgbm_model.predict_proba(X_val)[:,1]
lgbm_preds= (lgbm_probs> 0.5).astype(int)

print("LightGBM Validation Report:")
print(classification_report(y_val,lgbm_preds))
print(f"LightGBM AUC-ROC: {roc_auc_score(y_val,lgbm_probs):.4f}")

iso_path= BASE_DIR/"training"/"isolation_forest.pkl"
lof_path= BASE_DIR/"training"/"local_outlier_factor.pkl"
lgbm_path= BASE_DIR/"training"/"lightgbm_model.pkl"

joblib.dump(iso_model, iso_path)
joblib.dump(lof_model, lof_path)
joblib.dump(lgbm_model, lgbm_path)

print(f"Isolation Forest saved at {iso_path}")
print(f"Local Outlier Factor saved at {lof_path}")
print(f"LightGBM saved at {lgbm_path}")
print("\n All 3 models saved")

