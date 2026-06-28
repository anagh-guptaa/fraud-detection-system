from pathlib import Path
import joblib
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.metrics import classification_report

BASE_DIR=Path(__file__).resolve().parent.parent
dataset_path=(BASE_DIR/"data"/"processed"/"processed_fraud_dataset.csv")
df=pd.read_csv(dataset_path)
print(df.head())

feature_columns = [
    "amount",
    "avg_amount",
    "max_amount",
    "amount_ratio",
    "amount_std",
    "amount_zscore",
    "is_new_location",
    "is_new_device",
    "impossible_travel",
    "transactions_last_10min",
    "transactions_last_1hr",
    "transactions_last_24hr",
    "transactions_last_7d",
    "amount_last_1hr",
    "amount_last_24hr",
    "unique_merchants_last_24hr",
    "num_unique_devices_30d",
    "device_first_seen_days",
    "is_unknown_device_type",
    "is_high_risk_merchant",
    "merchant_fraud_rate",
    "amount_vs_merchant_avg",
    "merchant_category_risk",
    "is_high_risk_location",
    "hour_of_day",
    "is_night",
    "is_weekend",
    "day_of_week",
    "time_since_last_txn_hours",
    "is_round_amount",
]
X=df[feature_columns]
y_true=df["is_fraud"]

model=IsolationForest(n_estimators=100,contamination=0.05,random_state=42)
model.fit(X)
print("\nModel Training Complete")
predictions=model.predict(X)

y_pred=[
    1 if pred == -1 else 0
    for pred in predictions
]

print("\nClassification Report:\n")
print(classification_report(y_true,y_pred))

model_path=(BASE_DIR/"training"/"fraud_detection_model.pkl")
joblib.dump(model,model_path)
print("\nModel saved successfully")