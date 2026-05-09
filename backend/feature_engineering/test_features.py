from datetime import datetime
from zoneinfo import ZoneInfo
from backend.database.db import SessionLocal
from backend.feature_engineering.feature_builder import (build_transaction_features)

db=SessionLocal()

test_transaction={"user_id": 1,"amount": 5000,"merchant": "CryptoX","location": "Dubai","device_id": "unknown_551","timestamp": datetime.now(ZoneInfo("Asia/Kolkata"))}

features=build_transaction_features(db,test_transaction)

print("\nGenerated Features:\n")

for key, value in features.items():
    print(f"{key}: {value}")