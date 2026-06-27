from datetime import datetime
from zoneinfo import ZoneInfo
from fastapi import FastAPI, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from backend.database.db import SessionLocal
from backend.predict import predict_transaction

app = FastAPI(title="Fraud Detection System")


# ── Bug Fix #3: Proper DB dependency injection instead of a global session ──
def get_db():
    """
    Yields a fresh DB session per request and guarantees it is closed
    afterwards, even if an exception occurs.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class TransactionRequest(BaseModel):
    transaction_id: int
    user_id: int
    amount: float = Field(..., gt=0, description="Amount must be positive")  # Bug Fix #3a: reject negative/zero amounts
    merchant: str
    location: str
    device_id: str


@app.get("/")
def root():
    return {"message": "Fraud Detection API Running"}


@app.post("/predict")
def predict(request: TransactionRequest, db: Session = Depends(get_db)):  # injected, not global
    transaction_data = {
        "transaction_id": request.transaction_id,
        "user_id": request.user_id,
        "amount": request.amount,
        "merchant": request.merchant,
        "location": request.location,
        "device_id": request.device_id,
        "timestamp": datetime.now(ZoneInfo("Asia/Kolkata"))
    }

    result = predict_transaction(db, transaction_data)
    return result
