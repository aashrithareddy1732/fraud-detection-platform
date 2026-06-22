from app.services.fraud_model import fraud_model


def score_record(record: dict) -> dict:
    return fraud_model.predict(record)
