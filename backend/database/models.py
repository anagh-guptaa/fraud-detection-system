from sqlalchemy import Column, Integer, Float, String, DateTime, Boolean
from datetime import datetime
from zoneinfo import ZoneInfo
from backend.database.db import Base

class Transaction(Base):
    __tablename__ = "transactions"

    transaction_id= Column(Integer,primary_key=True,index=True)
    user_id= Column(Integer, nullable=False)
    amount= Column(Float, nullable=False)
    merchant= Column(String, nullable=False)
    location= Column(String, nullable=False)
    device_id= Column(String,nullable= False)
    timestamp= Column(DateTime, default=lambda: datetime.now(ZoneInfo("Asia/Kolkata")))
    is_fraud = Column(Boolean, default=False)

class Prediction(Base):
    __tablename__ = "predictions"

    prediction_id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(Integer, nullable=False)
    risk_score = Column(Float)
    fraud_status = Column(String)
    reason = Column(String)