from app.services.feature_engineering import transaction_to_features


def transform_record(record: dict):
    return transaction_to_features(record)
