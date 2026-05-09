from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from backend.database.models import Transaction

def build_transaction_features(db,transaction_data):
    user_id=transaction_data["user_id"]
    current_amount=transaction_data["amount"]
    current_location=transaction_data["location"]
    current_device=transaction_data["device_id"]
    current_time=transaction_data["timestamp"]

    user_transactions=(db.query(Transaction).filter(Transaction.user_id==user_id).all())

    if not user_transactions:
        return {"amount":current_amount,"avg_amount":current_amount,"max_amount":current_amount,"amount_ratio": 1,"is_new_location": 0, "is_new_device": 0, "transaction_last_10min": 1}

    amounts=[tx.amount for tx in user_transactions]
    avg_amount=sum(amounts)/len(amounts)
    max_amount=max(amounts)
    amount_ratio=current_amount/avg_amount

    previous_locations={tx.location for tx in user_transactions}

    is_new_location=int(current_location not in previous_locations)

    previous_devices={tx.device_id for tx in user_transactions}

    is_new_device=int(current_device not in previous_devices)

    ten_minutes_ago=current_time-timedelta(minutes=10)

    recent_transactions=[
        tx for tx in user_transactions
        if tx.timestamp.replace(
            tzinfo=ZoneInfo("Asia/Kolkata")
        )>=ten_minutes_ago
    ]

    transactions_last_10min=len(recent_transactions)

    features = {"amount": current_amount,"avg_amount": round(avg_amount, 2),"max_amount": round(max_amount, 2),"amount_ratio": round(amount_ratio, 2),"is_new_location": is_new_location,"is_new_device": is_new_device,"transactions_last_10min": transactions_last_10min}

    return features

