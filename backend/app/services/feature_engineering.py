import pandas as pd

MERCHANT_CATEGORIES = ["grocery", "travel", "electronics", "fuel", "entertainment", "luxury"]
COUNTRIES = ["US", "CA", "GB", "FR", "DE", "NG", "BR", "IN", "CN"]
DEVICE_TYPES = ["mobile", "desktop", "tablet", "pos_terminal"]
UNUSUAL_COUNTRIES = {"NG", "BR", "CN"}


def transaction_to_features(transaction: dict) -> pd.DataFrame:
    """Transform one transaction into model-ready features.

    When a real dataset is added later, keep this function as the single place
    where raw fields become model features.
    """
    row = {
        "amount": float(transaction["amount"]),
        "hour_of_day": int(transaction["hour_of_day"]),
        "is_weekend": int(bool(transaction["is_weekend"])),
        "transaction_velocity": int(transaction["transaction_velocity"]),
        "is_unusual_country": int(transaction["country"] in UNUSUAL_COUNTRIES),
        "is_late_night": int(int(transaction["hour_of_day"]) <= 5),
        "is_high_amount": int(float(transaction["amount"]) >= 1000),
    }

    for category in MERCHANT_CATEGORIES:
        row[f"merchant_category_{category}"] = int(transaction["merchant_category"] == category)
    for device in DEVICE_TYPES:
        row[f"device_type_{device}"] = int(transaction["device_type"] == device)

    return pd.DataFrame([row])


def transactions_to_training_frame(transactions: list[dict]) -> pd.DataFrame:
    frames = [transaction_to_features(transaction) for transaction in transactions]
    return pd.concat(frames, ignore_index=True)

