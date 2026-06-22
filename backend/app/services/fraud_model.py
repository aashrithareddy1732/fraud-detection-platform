import json
from pathlib import Path

import joblib

from app.services.feature_engineering import transaction_to_features

MODEL_PATH = Path(__file__).resolve().parents[1] / "ml" / "model.joblib"


def rule_based_score(transaction: dict) -> tuple[float, list[str]]:
    risk_points = 0
    reasons: list[str] = []

    if transaction["amount"] >= 1000:
        risk_points += 30
        reasons.append("High transaction amount")
    if transaction["country"] in {"NG", "BR", "CN"}:
        risk_points += 25
        reasons.append("Transaction originated from an unusual country")
    if transaction["hour_of_day"] <= 5:
        risk_points += 15
        reasons.append("Late night transaction timing")
    if transaction["transaction_velocity"] >= 8:
        risk_points += 25
        reasons.append("High recent transaction velocity")
    if transaction["merchant_category"] in {"luxury", "electronics"}:
        risk_points += 5
        reasons.append("Higher-risk merchant category")

    risk_score = min(risk_points, 100)
    probability = round(risk_score / 100, 4)
    if not reasons:
        reasons.append("No major rule-based risk indicators detected")
    return probability, reasons[:4]


class FraudModel:
    def __init__(self) -> None:
        self.model = None
        self.load_model()

    def load_model(self) -> None:
        if MODEL_PATH.exists():
            self.model = joblib.load(MODEL_PATH)

    def predict(self, transaction: dict) -> dict:
        fallback_probability, reasons = rule_based_score(transaction)
        probability = fallback_probability

        if self.model is not None:
            features = transaction_to_features(transaction)
            probability = float(self.model.predict_proba(features)[0][1])
            # Keep explainability grounded in transparent business rules.
            _, reasons = rule_based_score(transaction)

        risk_score = int(round(probability * 100))
        if risk_score >= 70:
            risk_level = "high"
        elif risk_score >= 40:
            risk_level = "medium"
        else:
            risk_level = "low"

        return {
            "transaction_id": transaction["transaction_id"],
            "fraud_probability": round(probability, 4),
            "risk_score": risk_score,
            "risk_level": risk_level,
            "prediction": "fraud" if probability >= 0.5 else "legitimate",
            "top_reasons": reasons,
        }


fraud_model = FraudModel()


def serialize_reasons(reasons: list[str]) -> str:
    return json.dumps(reasons)


def deserialize_reasons(value: str) -> list[str]:
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return [value]

