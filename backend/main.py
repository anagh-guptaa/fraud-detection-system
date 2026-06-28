from datetime import datetime
from zoneinfo import ZoneInfo
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from backend.database.db import SessionLocal
from backend.database.models import Transaction, Prediction
from backend.database.crud import create_transaction
from backend.predict import predict_transaction

app = FastAPI(title="Fraud Detection System — L3 Ensemble")

# CORS allows the Streamlit dashboard (port 8501) to call this API (port 8000)
# without the browser blocking the request as a cross-origin call.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db():
    """Yields a fresh DB session per request and guarantees closure."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ── Request model ─────────────────────────────────────────────────────────────
# transaction_id is removed — the DB now auto-generates it.
# This is the correct real-world design: the system assigns an ID when it
# receives the transaction, not the sender.
class TransactionRequest(BaseModel):
    user_id:   int
    amount:    float = Field(..., gt=0, description="Transaction amount — must be positive")
    merchant:  str
    location:  str
    device_id: str


# ── POST /predict ─────────────────────────────────────────────────────────────
@app.post("/predict")
def predict(request: TransactionRequest, db: Session = Depends(get_db)):
    """
    Full pipeline:
    1. Save raw transaction to DB  →  get auto-generated transaction_id
    2. Build 30 features from that user's history
    3. Run 3-model ensemble (IsolationForest + LOF + LightGBM)
    4. Compute SHAP explanation
    5. Save Prediction record
    6. Return full result
    """
    timestamp = datetime.now(ZoneInfo("Asia/Kolkata"))

    # Step 1: Persist the incoming transaction.
    # is_fraud=False here because the ML model hasn't decided yet.
    # The ground truth is stored in the Prediction table separately.
    # db.refresh(tx) after commit gives us the auto-generated primary key.
    tx = create_transaction(db, {
        "user_id":   request.user_id,
        "amount":    request.amount,
        "merchant":  request.merchant,
        "location":  request.location,
        "device_id": request.device_id,
        "timestamp": timestamp,
        "is_fraud":  False,
    })

    # Steps 2-5: run inside predict_transaction
    transaction_data = {
        "transaction_id": tx.transaction_id,   # auto-generated ID from DB
        "user_id":        request.user_id,
        "amount":         request.amount,
        "merchant":       request.merchant,
        "location":       request.location,
        "device_id":      request.device_id,
        "timestamp":      timestamp,
    }

    result = predict_transaction(db, transaction_data)

    # Attach the DB-assigned ID so the caller knows which record was created
    result["transaction_id"] = tx.transaction_id
    return result


# ── GET /stats ────────────────────────────────────────────────────────────────
@app.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    """
    Aggregate metrics across all predictions.
    Counts are based on the Prediction table (not Transaction) so only
    transactions that went through the ML pipeline are counted.
    """
    total = db.query(func.count(Prediction.prediction_id)).scalar() or 0
    fraud = db.query(func.count(Prediction.prediction_id)).filter(
        Prediction.fraud_status == "FRAUD"
    ).scalar() or 0

    # Risk tiers based on ensemble fraud probability stored in risk_score
    high = db.query(func.count(Prediction.prediction_id)).filter(
        Prediction.risk_score >= 0.75
    ).scalar() or 0
    med  = db.query(func.count(Prediction.prediction_id)).filter(
        Prediction.risk_score.between(0.45, 0.749)
    ).scalar() or 0
    low  = db.query(func.count(Prediction.prediction_id)).filter(
        Prediction.risk_score < 0.45
    ).scalar() or 0

    avg_risk   = db.query(func.avg(Prediction.risk_score)).scalar() or 0.0
    avg_amount = db.query(func.avg(Transaction.amount)).scalar() or 0.0
    max_amount = db.query(func.max(Transaction.amount)).scalar() or 0.0

    return {
        "total_transactions":       total,
        "fraud_count":              fraud,
        "normal_count":             total - fraud,
        "fraud_rate_percent":       round((fraud / total * 100) if total > 0 else 0.0, 2),
        "high_risk_count":          high,
        "medium_risk_count":        med,
        "low_risk_count":           low,
        "avg_fraud_probability":    round(float(avg_risk),   4),
        "avg_transaction_amount":   round(float(avg_amount), 2),
        "max_transaction_amount":   round(float(max_amount), 2),
    }


# ── GET /history ──────────────────────────────────────────────────────────────
@app.get("/history")
def get_history(limit: int = 50, db: Session = Depends(get_db)):
    """
    Returns the most recent predictions joined with transaction details.
    Joins Prediction ↔ Transaction on transaction_id so the dashboard
    can show both the raw data and the model's verdict in one row.
    """
    rows = (
        db.query(Prediction, Transaction)
        .join(Transaction, Prediction.transaction_id == Transaction.transaction_id)
        .order_by(desc(Prediction.prediction_id))
        .limit(limit)
        .all()
    )
    return [
        {
            "transaction_id": tx.transaction_id,
            "user_id":        tx.user_id,
            "amount":         tx.amount,
            "merchant":       tx.merchant,
            "location":       tx.location,
            "device_id":      tx.device_id,
            "timestamp":      tx.timestamp.isoformat() if tx.timestamp else None,
            "fraud_status":   pred.fraud_status,
            "risk_score":     pred.risk_score,
            "reason":         pred.reason,
        }
        for pred, tx in rows
    ]


# ── GET /alerts ───────────────────────────────────────────────────────────────
@app.get("/alerts")
def get_alerts(limit: int = 20, db: Session = Depends(get_db)):
    """Returns only FRAUD-flagged predictions — the alert feed."""
    rows = (
        db.query(Prediction, Transaction)
        .join(Transaction, Prediction.transaction_id == Transaction.transaction_id)
        .filter(Prediction.fraud_status == "FRAUD")
        .order_by(desc(Prediction.prediction_id))
        .limit(limit)
        .all()
    )
    return [
        {
            "transaction_id": tx.transaction_id,
            "user_id":        tx.user_id,
            "amount":         tx.amount,
            "merchant":       tx.merchant,
            "location":       tx.location,
            "device_id":      tx.device_id,
            "timestamp":      tx.timestamp.isoformat() if tx.timestamp else None,
            "risk_score":     pred.risk_score,
            "reason":         pred.reason,
        }
        for pred, tx in rows
    ]


# ── GET /fraud-trend ──────────────────────────────────────────────────────────
@app.get("/fraud-trend")
def get_fraud_trend(limit: int = 100, db: Session = Depends(get_db)):
    """
    Returns the last N predictions sorted oldest→newest.
    The dashboard uses this to plot a running fraud-probability line chart.
    reversed(rows) flips from newest-first (DB order) to oldest-first (chart order).
    """
    rows = (
        db.query(Prediction, Transaction)
        .join(Transaction, Prediction.transaction_id == Transaction.transaction_id)
        .order_by(desc(Prediction.prediction_id))
        .limit(limit)
        .all()
    )
    return [
        {
            "seq":            idx + 1,          # x-axis position (1 = oldest)
            "transaction_id": tx.transaction_id,
            "amount":         tx.amount,
            "merchant":       tx.merchant,
            "fraud_status":   pred.fraud_status,
            "risk_score":     pred.risk_score,
            "timestamp":      tx.timestamp.isoformat() if tx.timestamp else None,
        }
        for idx, (pred, tx) in enumerate(reversed(rows))
    ]


# ── GET / and /health ─────────────────────────────────────────────────────────
@app.get("/")
def root():
    return {"message": "Fraud Detection API — L3 Ensemble", "status": "running"}


@app.get("/health")
def health(db: Session = Depends(get_db)):
    total = db.query(func.count(Prediction.prediction_id)).scalar() or 0
    return {"status": "ok", "total_predictions_served": total}
