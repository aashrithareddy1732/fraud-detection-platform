import random
import uuid

from app.services.feature_engineering import COUNTRIES, DEVICE_TYPES, MERCHANT_CATEGORIES


def generate_transaction() -> dict:
    risky = random.random() < 0.18
    amount = round(random.uniform(8, 450), 2)
    country = random.choice(["US", "US", "US", "CA", "GB", "DE"])
    hour = random.randint(6, 22)
    velocity = random.randint(1, 5)

    if risky:
        amount = round(random.uniform(900, 6500), 2)
        country = random.choice(["NG", "BR", "CN", "FR"])
        hour = random.choice([0, 1, 2, 3, 4, 23])
        velocity = random.randint(8, 24)

    return {
        "transaction_id": f"txn_{uuid.uuid4().hex[:12]}",
        "customer_id": f"cust_{random.randint(1000, 9999)}",
        "amount": amount,
        "merchant_category": random.choice(MERCHANT_CATEGORIES),
        "country": country,
        "hour_of_day": hour,
        "is_weekend": random.choice([True, False]),
        "device_type": random.choice(DEVICE_TYPES),
        "transaction_velocity": velocity,
    }


def generate_transactions(count: int) -> list[dict]:
    return [generate_transaction() for _ in range(count)]


def synthetic_label(transaction: dict) -> int:
    score = 0
    score += 2 if transaction["amount"] >= 1000 else 0
    score += 2 if transaction["country"] in {"NG", "BR", "CN"} else 0
    score += 1 if transaction["hour_of_day"] <= 5 else 0
    score += 2 if transaction["transaction_velocity"] >= 8 else 0
    score += 1 if transaction["merchant_category"] in {"luxury", "electronics"} else 0
    return int(score >= 4)

