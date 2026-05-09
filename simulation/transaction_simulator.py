import random
import time
from datetime import datetime
from zoneinfo import ZoneInfo
from backend.database.db import SessionLocal
from backend.database.crud import create_transaction

ecommerce_merchants=["Amazon","Flipkart","Myntra","Ajio","Meesho","Nykaa","Snapdeal"]
food_merchants=["Zomato","Swiggy","Dominos","McDonalds","PizzaHut","BurgerKing"]
transport_merchants=["Uber","Ola","Rapido","IRCTC"]
entertainment_merchants=["Netflix","Spotify","Steam","BookMyShow"]
tech_merchants=["Apple","Samsung","Croma","RelianceDigital"]
daily_merchants=["BigBasket","Blinkit","JioMart","DMart"]
fraud_merchants=["CryptoX","DarkPay","QuickCash","UnknownMerchant","FastLoan247"]

users=[
    {"user_id": 1,"avg_spend": 100,"home_location": "Delhi","usual_device": "android_001","preferred_categories":[ecommerce_merchants,food_merchants,daily_merchants]},
    {"user_id": 2,"avg_spend": 500,"home_location": "Mumbai","usual_device": "iphone_002","preferred_categories": [food_merchants,transport_merchants,entertainment_merchants]},
    {"user_id": 3,"avg_spend": 1000,"home_location": "Bangalore","usual_device": "laptop_003","preferred_categories": [tech_merchants,ecommerce_merchants,entertainment_merchants]},
    {"user_id": 4,"avg_spend": 250,"home_location": "Kolkata","usual_device": "android_004","preferred_categories": [daily_merchants,food_merchants,transport_merchants]},
    {"user_id": 5,"avg_spend": 2000,"home_location": "Hyderabad","usual_device": "iphone_005","preferred_categories": [tech_merchants,ecommerce_merchants,entertainment_merchants]}
]

def generate_normal_transaction(user):
    merchant_category=random.choice(user["preferred_categories"])
    merchant=random.choice(merchant_category)
    amount=round(random.normalvariate(user["avg_spend"],user["avg_spend"]*0.2),2)

    transaction={"user_id": user["user_id"],"amount":max(amount,10),"merchant": merchant,"location": user["home_location"],"device_id": user["usual_device"],"timestamp": datetime.now(ZoneInfo("Asia/Kolkata")),"is_fraud": False}

    return transaction

def generate_fraud_transaction(user):

    fraud_locations = ["London","Dubai","New York","Singapore","Moscow","Hong Kong"]
    transaction = {"user_id": user["user_id"],"amount": round(user["avg_spend"] * random.randint(20, 50),2),"merchant": random.choice(fraud_merchants),"location": random.choice(fraud_locations),"device_id": f"unknown_device_{random.randint(100, 999)}","timestamp": datetime.now(ZoneInfo("Asia/Kolkata")),"is_fraud": True}

    return transaction

def generate_transaction():
    user=random.choice(users)
    fraud_probability=0.10
    if random.random()<fraud_probability:
        transaction=generate_fraud_transaction(user)
    else:
        transaction=generate_normal_transaction(user)
    return transaction

if __name__=="__main__":
    db=SessionLocal()
    print("\nStarting Transaction Simulator...\n")
    while True:
        transaction=generate_transaction()
        create_transaction(db,transaction)
        print(
            f"[+] Transaction Stored | "
            f"User: {transaction['user_id']} | "
            f"Amount: ₹{transaction['amount']} | "
            f"Fraud: {transaction['is_fraud']}"
        )
        time.sleep(2)

