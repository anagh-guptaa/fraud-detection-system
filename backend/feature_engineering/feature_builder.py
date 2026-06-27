from datetime import timedelta, tzinfo
import statistics
from sqlalchemy import func, cast, Integer
from backend.database.models import Transaction
from simulation.transaction_simulator import merchant_categories

HIGH_RISK_MERCHANTS={
    "CryptoX", "DarkPay", "QuickCash", "FastLoan247", "UnknownMerchant"
}

HIGH_RISK_LOCATIONS={
    "Moscow", "Hong Kong", "Dubai", "London", "New York", "Singapore"
}

MERCHANT_CATEGORIES={
    "Amazon": "ecommerce", "Filpkart": "ecommerce",  "Myntra": "ecommerce",
    "Ajio": "ecommerce",     "Meesho": "ecommerce",    "Nykaa": "ecommerce",
    "Snapdeal": "ecommerce",
    "Zomato": "food",        "Swiggy": "food",          "Dominos": "food",
    "McDonalds": "food",     "PizzaHut": "food",        "BurgerKing": "food",
    "Uber": "transport",     "Ola": "transport",        "Rapido": "transport",
    "IRCTC": "transport",
    "Netflix": "entertainment", "Spotify": "entertainment",
    "Steam": "entertainment",   "BookMyShow": "entertainment",
    "Apple": "tech",         "Samsung": "tech",         "Croma": "tech",
    "RelianceDigital": "tech",
    "BigBasket": "daily",    "Blinkit": "daily",        "JioMart": "daily",
    "DMart": "daily",
    "CryptoX": "fraud",      "DarkPay": "fraud",        "QuickCash": "fraud",
    "UnknownMerchant": "fraud", "FastLoan247": "fraud",
}

CATEGORY_RISK={
    "ecommerce": 0.1, "food":0.1, "transport": 0.1, "entertainment": 0.1, "daily": 0.1, "tech": 0.3, "fraud": 1.0, "unknown": 0.5,
}


def build_transaction_features(db, transaction_data: dict) -> dict:
    """Given a transaction dict and a DB session, compute all 30 features. Returns a dict"""

    user_id= transaction_data["user_id"]
    current_amount= transaction_data["amount"]
    current_location= transaction_data["location"]
    current_device= transaction_data["device_id"]
    current_time= transaction_data["timestamp"]
    current_merchant= transaction_data["merchant"]
    current_time_naive= current_time.replace(tzinfo=None)

    hour_of_day=current_time_naive.hour
    is_night= int(0 <= hour_of_day < 6)
    is_weekend= int(current_time_naive.weekday() >=5)
    day_of_week=current_time_naive.weekday()

    is_high_risk_merchant= int(current_merchant in HIGH_RISK_MERCHANTS)
    is_high_risk_location= int(current_location in HIGH_RISK_LOCATIONS)
    merchant_category = MERCHANT_CATEGORIES.get(current_merchant, "unknown")
    merchant_category_risk= CATEGORY_RISK.get(merchant_category, 0.5)

    is_unknown_device_type= int("unknown" in current_device.lower())
    is_round_amount= int(current_amount % 100 == 0 and current_amount >=1000)


    merchant_agg=(
        db.query(
            func.avg(Transaction.amount),
            func.count(Transaction.transaction_id),
            func.sum(cast(Transaction.is_fraud, Integer)),
        ).filter(Transaction.merchant==current_merchant).one()
    )

    merchant_avg_amount= float(merchant_agg[0]) if merchant_agg[0] else current_amount
    merchant_total_txns= int(merchant_agg[1]) if merchant_agg[1] else 1
    merchant_fraud_count= int(merchant_agg[2]) if merchant_agg[2] else 0
    merchant_fraud_rate= merchant_fraud_count/merchant_total_txns

    amount_vs_merchant_avg=(
        current_amount/merchant_avg_amount if merchant_avg_amount else 1.0
    )


    user_transactions=(
        db.query(Transaction).filter(
            Transaction.user_id==user_id,
            Transaction.transaction_id<transaction_data["transaction_id"],
        )
        .order_by(Transaction.timestamp.desc()).all()
    )

    #USER FALLBACK
    if not user_transactions:
        agg=db.query(
            func.avg(Transaction.amount),
            func.max(Transaction.amount),
        ).one()

        global_avg= float(agg[0]) if agg[0] is not None else current_amount
        global_max= float(agg[1]) if agg[1] is not None else current_amount
        amount_ratio= current_amount/global_avg if global_avg else 1.0

        return {
            "amount": current_amount,
            "avg_amount": round(global_avg,2),
            "max_amount": round(global_max,2),
            "amount_ratio": round(amount_ratio,2),
            "amount_std": 0.0,
            "amount_zscore": 0.0,

            "is_new_location": 1,
            "is_new_device": 1,
            "impossible_travel": 0,

            "transactions_last_10min": 1,
            "transactions_last_1hr": 1,
            "transactions_last_24hr": 1,
            "transactions_last_7d": 1,
            "amount_last_1hr": current_amount,
            "amount_last_24hr": current_amount,
            "unique_merchants_last_24hr": 1,

            "num_unique_devices_30d": 1,
            "device_first_seen_days": 0,
            "is_unknown_device_type": is_unknown_device_type,

            "is_high_risk_merchant": is_high_risk_merchant,
            "merchant_fraud_rate": round(merchant_fraud_rate,4),
            "amount_vs_merchant_avg": round(amount_vs_merchant_avg,2),
            "merchant_category_risk": merchant_category_risk,

            "is_high_risk_location": is_high_risk_location,

            "hour_of_day": hour_of_day,
            "is_night": is_night,
            "is_weekend": is_weekend,
            "day_of_week": day_of_week,

            "time_since_last_txn_hours": 24.0,
            "is_round_amount": is_round_amount,
        }

    amounts= [tx.amount for tx in user_transactions]
    avg_amount= sum(amounts)/len(amounts)
    max_amount=max(amounts)

    amount_ratio= current_amount/avg_amount if avg_amount else 1.0
    amount_std= statistics.stdev(amounts) if len(amounts) > 1 else 0.0
    amount_zscore= (
        (current_amount - avg_amount)/ amount_std if amount_std > 0 else 0.0
    )

    previous_locations= {tx.location for tx in user_transactions}
    is_new_location= int(current_location not in previous_locations)

    previous_devices= {tx.device_id for tx in user_transactions}
    is_new_device= int(current_device not in previous_devices)

    last_tx= user_transactions[0]
    time_since_last_txn_hours=(
            (current_time_naive - last_tx.timestamp).total_seconds()/3600
    )

    impossible_travel= int(current_location != last_tx.location and time_since_last_txn_hours <2.0)

    ten_min_ago= current_time_naive - timedelta(minutes=10)
    one_hr_ago= current_time_naive - timedelta(hours=1)
    twenty_four_hr_ago= current_time_naive - timedelta(hours=24)
    seven_days_ago= current_time_naive - timedelta(days=7)
    thirty_days_ago= current_time_naive - timedelta(days=30)

    txns_10min= [tx for tx in user_transactions if tx.timestamp >= ten_min_ago]
    txns_1hr= [tx for tx in user_transactions if tx.timestamp >= one_hr_ago]
    txns_24hr= [tx for tx in user_transactions if tx.timestamp >= twenty_four_hr_ago]
    txns_7d= [tx for tx in user_transactions if tx.timestamp >= seven_days_ago]
    txns_30d= [tx for tx in user_transactions if tx.timestamp >= thirty_days_ago]

    amount_last_1hr= sum(tx.amount for tx in txns_1hr)
    amount_last_24hr= sum(tx.amount for tx in txns_24hr)

    unique_merchants_last_24hr= len({tx.merchant for tx in txns_24hr})

    num_unique_devices_30d= len({tx.device_id for tx in txns_30d})

    device_first_seen= None
    for tx in reversed(user_transactions):
        if tx.device_id== current_device:
            device_first_seen= tx.timestamp
            break

    device_first_seen_days= (
        (current_time_naive - device_first_seen).days
        if device_first_seen else 0
    )

    features = {
        "amount": current_amount,
        "avg_amount": round(avg_amount, 2),
        "max_amount": round(max_amount, 2),
        "amount_ratio": round(amount_ratio, 2),
        "amount_std": round(amount_std, 2),
        "amount_zscore": round(amount_zscore, 2),

        "is_new_location": is_new_location,
        "is_new_device": is_new_device,
        "impossible_travel": impossible_travel,

        "transactions_last_10min": len(txns_10min),
        "transactions_last_1hr": len(txns_1hr),
        "transactions_last_24hr": len(txns_24hr),
        "transactions_last_7d": len(txns_7d),
        "amount_last_1hr": round(amount_last_1hr, 2),
        "amount_last_24hr": round(amount_last_24hr, 2),
        "unique_merchants_last_24hr": unique_merchants_last_24hr,

        "num_unique_devices_30d": num_unique_devices_30d,
        "device_first_seen_days": device_first_seen_days,
        "is_unknown_device_type": is_unknown_device_type,

        "is_high_risk_merchant": is_high_risk_merchant,
        "merchant_fraud_rate": round(merchant_fraud_rate, 4),
        "amount_vs_merchant_avg": round(amount_vs_merchant_avg, 2),
        "merchant_category_risk": merchant_category_risk,

        "is_high_risk_location": is_high_risk_location,

        "hour_of_day": hour_of_day,
        "is_night": is_night,
        "is_weekend": is_weekend,
        "day_of_week": day_of_week,

        "time_since_last_txn_hours": round(time_since_last_txn_hours, 2),
        "is_round_amount": is_round_amount,
    }
    return features