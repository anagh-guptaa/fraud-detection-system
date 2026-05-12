from pathlib import Path
import joblib
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.metrics import classification_report

BASE_DIR=Path(__file__).resolve().parent.parent
dataset_path=(BASE_DIR/"data"/"processed"/"processed_fraud_dataset.csv")
df=pd.read_csv(dataset_path)
print(df.head())

feature_columns=["amount","avg_amount","max_amount","amount_ratio","is_new_location","is_new_device","transactions_last_10min","is_high_risk_merchant","is_high_risk_location"]
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