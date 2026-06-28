import random
import time
import requests

# ─────────────────────────────────────────────────────────────────────────────
# The simulator now POSTs to the FastAPI /predict endpoint instead of writing
# directly to the DB. This means EVERY transaction flows through:
#   Simulator → API → Feature Engineering → 3-Model Ensemble → DB
# That is the real production pipeline.
# ─────────────────────────────────────────────────────────────────────────────
API_URL = "http://127.0.0.1:8000/predict"

# ── Merchant lists (same as before) ───────────────────────────────────────────
ecommerce_merchants    = ["Amazon", "Flipkart", "Myntra", "Ajio", "Meesho", "Nykaa", "Snapdeal"]
food_merchants         = ["Zomato", "Swiggy", "Dominos", "McDonalds", "PizzaHut", "BurgerKing"]
transport_merchants    = ["Uber", "Ola", "Rapido", "IRCTC"]
entertainment_merchants= ["Netflix", "Spotify", "Steam", "BookMyShow"]
tech_merchants         = ["Apple", "Samsung", "Croma", "RelianceDigital"]
daily_merchants        = ["BigBasket", "Blinkit", "JioMart", "DMart"]
fraud_merchants        = ["CryptoX", "DarkPay", "QuickCash", "UnknownMerchant", "FastLoan247"]

locations    = ["Delhi", "Mumbai", "Bangalore", "Kolkata", "Hyderabad", "Chennai", "Pune", "Ahmedabad"]
device_types = ["android", "iphone", "laptop", "tablet"]
merchant_categories = [
    ecommerce_merchants, food_merchants, transport_merchants,
    entertainment_merchants, tech_merchants, daily_merchants,
]


def generate_users(num_users=100):
    users = []
    for user_id in range(1, num_users + 1):
        users.append({
            "user_id":              user_id,
            "avg_spend":            random.randint(100, 5000),
            "home_location":        random.choice(locations),
            "usual_device":         f"{random.choice(device_types)}_{random.randint(100, 999)}",
            "preferred_categories": random.sample(merchant_categories, k=3),
        })
    return users


def generate_normal_transaction(user) -> dict:
    category = random.choice(user["preferred_categories"])
    merchant = random.choice(category)
    amount   = random.normalvariate(user["avg_spend"], user["avg_spend"] * 0.2)
    return {
        "user_id":   user["user_id"],
        "amount":    max(round(amount, 2), 10.0),
        "merchant":  merchant,
        "location":  user["home_location"],
        "device_id": user["usual_device"],
    }


def generate_fraud_transaction(user) -> dict:
    fraud_locations = ["London", "Dubai", "New York", "Singapore", "Moscow", "Hong Kong"]
    return {
        "user_id":   user["user_id"],
        "amount":    round(user["avg_spend"] * random.randint(20, 50), 2),
        "merchant":  random.choice(fraud_merchants),
        "location":  random.choice(fraud_locations),
        "device_id": f"unknown_device_{random.randint(100, 999)}",
    }


# Pre-generate 100 synthetic users with consistent spending profiles
users = generate_users(100)


def generate_transaction():
    """Returns (payload_dict, is_fraud_simulated).
    The payload goes to the API. is_fraud_simulated lets us check model accuracy."""
    user              = random.choice(users)
    is_fraud_simulated = random.random() < 0.05   # 5% fraud rate
    if is_fraud_simulated:
        payload = generate_fraud_transaction(user)
    else:
        payload = generate_normal_transaction(user)
    return payload, is_fraud_simulated


# ── ANSI colour helpers ────────────────────────────────────────────────────────
RED    = "\033[91m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
GREY   = "\033[90m"
BOLD   = "\033[1m"
RESET  = "\033[0m"


if __name__ == "__main__":
    print(f"\n{BOLD}{'═' * 72}{RESET}")
    print(f"  {CYAN}{BOLD}🚀  Transaction Simulator — Routing through Fraud Detection API{RESET}")
    print(f"{BOLD}{'═' * 72}{RESET}")
    print(f"  {GREY}API URL   : {API_URL}{RESET}")
    print(f"  {GREY}Users     : {len(users)}{RESET}")
    print(f"  {GREY}Fraud rate: ~5%   |   Speed: 0.3 s / transaction{RESET}")
    print(f"{BOLD}{'═' * 72}{RESET}\n")

    counters = {"total": 0, "fraud_sim": 0, "fraud_det": 0, "correct": 0}

    while True:
        payload, is_fraud_sim = generate_transaction()
        counters["total"] += 1
        if is_fraud_sim:
            counters["fraud_sim"] += 1

        try:
            resp = requests.post(API_URL, json=payload, timeout=5)

            if resp.status_code == 200:
                r = resp.json()
                is_det   = r.get("is_fraud", False)
                risk_lvl = r.get("risk_level", "?")
                prob     = r.get("fraud_probability", 0.0)
                txn_id   = r.get("transaction_id", "?")

                if is_det:
                    counters["fraud_det"] += 1

                correct = (is_fraud_sim == is_det)
                if correct:
                    counters["correct"] += 1

                # ── Format terminal line ───────────────────────────────────
                status_str = f"{RED}{BOLD}🔴 FRAUD {RESET}" if is_det else f"{GREEN}🟢 NORMAL{RESET}"
                sim_str    = f"{RED}[SIM:FRAUD]{RESET}" if is_fraud_sim else f"{GREY}[SIM:NORM] {RESET}"
                chk        = f"{GREEN}✓{RESET}" if correct else f"{RED}✗{RESET}"

                # Risk level colour
                if risk_lvl == "HIGH":
                    rl_str = f"{RED}{risk_lvl:<6}{RESET}"
                elif risk_lvl == "MEDIUM":
                    rl_str = f"{YELLOW}{risk_lvl:<6}{RESET}"
                else:
                    rl_str = f"{GREEN}{risk_lvl:<6}{RESET}"

                prob_color = RED if prob > 0.75 else (YELLOW if prob > 0.45 else GREEN)

                print(
                    f"{status_str} | "
                    f"#{str(txn_id):<6} | "
                    f"User:{str(payload['user_id']):<4} | "
                    f"₹{payload['amount']:>10,.2f} | "
                    f"{payload['merchant']:<18} | "
                    f"{payload['location']:<12} | "
                    f"P={prob_color}{prob:.3f}{RESET} [{rl_str}] | "
                    f"{sim_str} {chk}"
                )

                # Print running stats every 25 transactions
                if counters["total"] % 25 == 0:
                    acc = counters["correct"] / counters["total"] * 100
                    dr  = counters["fraud_det"] / counters["total"] * 100
                    print(
                        f"\n  {BOLD}{CYAN}── Stats ({counters['total']} txns) ──"
                        f"  Simulated Frauds: {counters['fraud_sim']}"
                        f"  |  Detected: {counters['fraud_det']}"
                        f"  |  Detection Rate: {dr:.1f}%"
                        f"  |  Overall Accuracy: {acc:.1f}%{RESET}\n"
                    )

            else:
                print(f"  {RED}⚠  API Error {resp.status_code}: {resp.text[:80]}{RESET}")

        except requests.exceptions.ConnectionError:
            print(
                f"  {RED}✗  Cannot reach API — is the server running?{RESET}\n"
                f"     Run: {CYAN}uvicorn backend.main:app --reload{RESET}"
            )
            time.sleep(4)
            continue

        except Exception as e:
            print(f"  {RED}✗  Unexpected error: {e}{RESET}")

        time.sleep(0.3)   # ~3 transactions/sec — readable in real-time
