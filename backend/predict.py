from pathlib import Path
import joblib
import numpy as np
from backend.feature_engineering.feature_builder import build_transaction_features

BASE_DIR=Path(__file__).resolve().parent.parent
model_path=(BASE_DIR/"training"/"fraud_detection_model.pkl")
model=joblib.load(model_path)
print("\nFraud Detection Model Loaded\n")

FEATURE_COLUMNS = ["amount","avg_amount","max_amount","amount_ratio","is_new_location","is_new_device","transactions_last_10min","is_high_risk_merchant","is_high_risk_location"]
def predict_transaction(db,transaction_data):
    features=build_transaction_features(db,transaction_data)
    feature_vector=np.array([features[col] for col in FEATURE_COLUMNS]).reshape(1,-1)
    prediction=model.predict(feature_vector)[0]

    anomaly_score=model.decision_function(feature_vector)[0]
    is_fraud=prediction==-1

    if anomaly_score<-0.10:
        risk_level="HIGH"
    elif anomaly_score<0:
        risk_level="MEDIUM"
    else:
        risk_level="HIGH"

    result={"is_fraud": bool(is_fraud),"risk_level": risk_level,"anomaly_score": round(anomaly_score,4),"features": features}

    return result

