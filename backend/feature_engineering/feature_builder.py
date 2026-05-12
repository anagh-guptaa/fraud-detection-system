from datetime import timedelta
from backend.database.models import Transaction

HIGH_RISK_MERCHANTS={"CryptoX","DarkPay","QuickCash","FastLoan247","UnknownMerchant"}
HIGH_RISK_LOCATIONS={"Moscow","Hong Kong","Dubai"}

def build_transaction_features(db, transaction_data):

    user_id=transaction_data["user_id"]
    current_amount=transaction_data["amount"]
    current_location=transaction_data["location"]
    current_device=transaction_data["device_id"]
    current_time=transaction_data["timestamp"]

    user_transactions=(db.query(Transaction).filter(Transaction.user_id == user_id,Transaction.transaction_id <transaction_data["transaction_id"]).all())

    if not user_transactions:

        all_transactions=(db.query(Transaction).all())
        all_amounts=[
            tx.amount
            for tx in all_transactions
        ]
        global_avg_amount=(sum(all_amounts) / len(all_amounts))
        global_max_amount=max(all_amounts)
        amount_ratio=(current_amount / global_avg_amount)

        is_high_risk_merchant=int(transaction_data["merchant"] in HIGH_RISK_MERCHANTS)

        is_high_risk_location=int(
            current_location
            in HIGH_RISK_LOCATIONS
        )

        return {
            "amount": current_amount,
            "avg_amount": round(
                global_avg_amount,
                2
            ),
            "max_amount": round(
                global_max_amount,
                2
            ),
            "amount_ratio": round(
                amount_ratio,
                2
            ),
            "is_new_location": 1,
            "is_new_device": 1,
            "transactions_last_10min": 1,
            "is_high_risk_merchant":
                is_high_risk_merchant,
            "is_high_risk_location":
                is_high_risk_location
        }

    amounts=[
        tx.amount
        for tx in user_transactions
    ]

    avg_amount=(sum(amounts) / len(amounts))
    max_amount=max(amounts)
    amount_ratio=(current_amount / avg_amount)

    previous_locations={
        tx.location
        for tx in user_transactions
    }

    is_new_location=int(
        current_location
        not in previous_locations
    )

    previous_devices={
        tx.device_id
        for tx in user_transactions
    }

    is_new_device=int(current_device not in previous_devices)

    current_time_naive=(current_time.replace(tzinfo=None))


    ten_minutes_ago = (
        current_time_naive -
        timedelta(minutes=10)
    )


    recent_transactions = [
        tx for tx in user_transactions
        if tx.timestamp >= ten_minutes_ago
    ]


    transactions_last_10min = (
        len(recent_transactions)
    )

    is_high_risk_merchant = int(
        transaction_data["merchant"]
        in HIGH_RISK_MERCHANTS
    )


    is_high_risk_location = int(
        current_location
        in HIGH_RISK_LOCATIONS
    )

    features = {

        "amount": current_amount,

        "avg_amount": round(
            avg_amount,
            2
        ),

        "max_amount": round(
            max_amount,
            2
        ),

        "amount_ratio": round(
            amount_ratio,
            2
        ),

        "is_new_location":
            is_new_location,

        "is_new_device":
            is_new_device,

        "transactions_last_10min":
            transactions_last_10min,

        "is_high_risk_merchant":
            is_high_risk_merchant,

        "is_high_risk_location":
            is_high_risk_location
    }


    return features