from datetime import datetime
from zoneinfo import ZoneInfo
from backend.database.db import SessionLocal
from backend.predict import predict_transaction

db=SessionLocal()

transaction_data={"transaction_id":999999,"user_id": 1000, "amount": 120000, "merchant": "Amazon", "location": "Mumbai", "device_id": "android_3","timestamp": datetime.now(ZoneInfo("Asia/Kolkata"))}

result= predict_transaction(db,transaction_data)

print("\nPrediction Result\n")
print(result)