from datetime import datetime
from zoneinfo import ZoneInfo
from fastapi import FastAPI
from pydantic import BaseModel
from backend.database.db import SessionLocal
from backend.predict import predict_transaction

app=FastAPI(title="Fraud Detection System")

db=SessionLocal()
class TransactionRequest(BaseModel):
    transaction_id: int
    user_id: int
    amount: float
    merchant: str
    location: str
    device_id: str

@app.get("/")
def root():
    return {"message": "Fraud Detection API Running"}

@app.post("/predict")
def predict(request: TransactionRequest):
    transaction_data={
        "transaction_id": request.transaction_id,
        "user_id":request.user_id,
        "amount": request.amount,
        "merchant": request.merchant,
        "location": request.location,
        "device_id": request.device_id,
        "timestamp": datetime.now(ZoneInfo("Asia/Kolkata"))
    }

    result=predict_transaction(db,transaction_data)

    return result

