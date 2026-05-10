import pandas as pd
from backend.database.db import SessionLocal
from backend.database.models import Transaction
from backend.feature_engineering.feature_builder import build_transaction_features

db=SessionLocal()

transactions=(db.query(Transaction).order_by(Transaction.transaction_id).all())
print(f"\nTotal Transactions Loaded: {len(transactions)}")

dataset=[]

for tx in transactions:
    transaction_data={"user_id": tx.user_id,"amount": tx.amount,"merchant": tx.merchant,"location": tx.location,"device_id": tx.device_id,"timestamp": tx.timestamp}
    features=build_transaction_features(db,transaction_data)
    features["is_fraud"]=tx.is_fraud
    dataset.append(features)

df=pd.DataFrame(dataset)
print("\nDataset Preview:\n")
print(df.head())
print("\nDataset Shape:")
print(df.shape)

df.to_csv("data/processed/processed_fraud_dataset.csv",index=False)
print("\nProcessed dataset saved successfully")
