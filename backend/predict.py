from pathlib import Path
import joblib
import numpy as np
import shap
from backend.feature_engineering.feature_builder import build_transaction_features
from backend.database.models import Prediction

BASE_DIR = Path(__file__).resolve().parent.parent
iso_model= joblib.load(BASE_DIR/"training"/"isolation_forest.pkl")
lof_model= joblib.load(BASE_DIR/"training"/"local_outlier_factor.pkl")
lgbm_model= joblib.load(BASE_DIR/"training"/"lightgbm_model.pkl")
explainer= shap.TreeExplainer(lgbm_model)

print("Isolation Forest loaded")
print("Local Outlier Factor loaded")
print("LightGBM loaded")
print("SHAP explainer ready\n")


FEATURE_COLUMNS = [
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

def _sigmoid(x: float) -> float:
    """Converts any real number to 0.0-1.0 range"""
    return 1.0/(1.0 + np.exp(-float(x)))


def predict_transaction(db, transaction_data: dict) -> dict:
    features = build_transaction_features(db, transaction_data)
    X= np.array([features[col] for col in FEATURE_COLUMNS]).reshape(1,-1)
    iso_raw= iso_model.decision_function(X)[0]
    lof_raw= lof_model.decision_function(X)[0]
    lgbm_p= lgbm_model.predict_proba(X)[0][1]
    iso_prob= _sigmoid(-iso_raw * 5)
    lof_prob= _sigmoid(-lof_raw * 5)

    final_prob= (0.35 * iso_prob) + (0.20* lof_prob) + (0.45 * lgbm_p)
    is_fraud= final_prob>0.5

    if final_prob> 0.75:
        risk_level= "HIGH"
    elif final_prob>0.45:
        risk_level= "MEDIUM"
    else:
        risk_level= "LOW"

    shap_values= explainer.shap_values(X)
    if isinstance(shap_values, list):
        shap_row= shap_values[1][0]
    else:
        shap_row= shap_values[0]

    shap_dict= dict(zip(FEATURE_COLUMNS,shap_row))
    top_reasons= sorted(shap_dict.items(), key=lambda i: abs(i[1]), reverse= True)[:3]

    reason_str= "; ".join(f"{f}={v:.3f}" for f, v in top_reasons)
    db.add(Prediction(
        transaction_id=transaction_data["transaction_id"],
        risk_score=round(float(final_prob), 4),
        fraud_status="FRAUD" if is_fraud else "NORMAL",
        reason=reason_str,
    ))
    db.commit()

    return {
        "is_fraud": bool(is_fraud),
        "risk_level": risk_level,
        "fraud_probability": round(float(final_prob),4),
        "model_scores": {
            "isolation_forest": round(float(iso_prob),4),
            "local_outlier_factor": round(float(lof_prob),4),
            "lightgbm": round(float(lgbm_p),4),
        },
        "top_reasons": [
            {
                "feature": feat,
                "impact": round(float(val),4),
                "direction": "toward_fraud" if val > 0 else "toward_normal",
            }
            for feat, val in top_reasons
        ],
        "features": features,
    }


