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

locations = ["Delhi","Mumbai","Bangalore","Kolkata","Hyderabad","Chennai","Pune","Ahmedabad"]
device_types = ["android","iphone","laptop","tablet"]
merchant_categories = [ecommerce_merchants,food_merchants,transport_merchants,entertainment_merchants,tech_merchants,daily_merchants]

def generate_users(num_users=100):
    users=[]
    for user_id in range(1, num_users + 1):
        avg_spend=random.randint(100, 5000)
        home_location=random.choice(locations)
        device=(f"{random.choice(device_types)}_"f"{random.randint(100,999)}")
        preferred_categories = random.sample(
            merchant_categories,
            k=3
        )
        user = {"user_id": user_id,"avg_spend": avg_spend,"home_location": home_location,"usual_device": device,"preferred_categories": preferred_categories}
        users.append(user)

    return users

users = generate_users(100)


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
    fraud_probability=0.05
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
        time.sleep(0.01)

