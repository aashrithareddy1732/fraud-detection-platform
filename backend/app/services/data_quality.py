from collections import Counter
import uuid

from app.services.feature_engineering import COUNTRIES, DEVICE_TYPES, MERCHANT_CATEGORIES

REQUIRED_UPLOAD_FIELDS = {
    "amount", "merchant_category", "country", "hour_of_day", "is_weekend",
    "device_type", "transaction_velocity",
}


def transaction_summary(record: dict) -> str:
    category = str(record["merchant_category"]).replace("_", " ").title()
    return f"{category} transaction in {record['country']} for ${float(record['amount']):,.2f}"


def _to_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    normalized = str(value).strip().lower()
    if normalized in {"true", "1", "yes", "y"}:
        return True
    if normalized in {"false", "0", "no", "n"}:
        return False
    raise ValueError("is_weekend must be true/false")


def prepare_uploaded_records(records: list[dict]) -> tuple[list[dict], list[dict]]:
    valid_records: list[dict] = []
    issues: list[dict] = []
    for index, record in enumerate(records, start=2):
        missing = sorted(field for field in REQUIRED_UPLOAD_FIELDS if str(record.get(field, "")).strip() == "")
        if missing:
            issues.append({"row": index, "type": "missing_fields", "fields": missing})
            continue
        try:
            prepared = {
                "transaction_id": str(record.get("transaction_id") or f"txn_{uuid.uuid4().hex[:12]}").strip(),
                "customer_id": str(record.get("customer_id") or f"cust_upload_{uuid.uuid4().hex[:8]}").strip(),
                "amount": float(record["amount"]),
                "merchant_category": str(record["merchant_category"]).strip().lower(),
                "country": str(record["country"]).strip().upper(),
                "hour_of_day": int(record["hour_of_day"]),
                "is_weekend": _to_bool(record["is_weekend"]),
                "device_type": str(record["device_type"]).strip().lower(),
                "transaction_velocity": int(record["transaction_velocity"]),
            }
        except (TypeError, ValueError) as exc:
            issues.append({"row": index, "type": "invalid_value", "detail": str(exc)})
            continue
        if prepared["amount"] < 0:
            issues.append({"row": index, "type": "invalid_amount"})
        elif prepared["country"] not in COUNTRIES:
            issues.append({"row": index, "type": "invalid_country", "country": prepared["country"]})
        elif prepared["merchant_category"] not in MERCHANT_CATEGORIES:
            issues.append({"row": index, "type": "invalid_merchant_category"})
        elif prepared["device_type"] not in DEVICE_TYPES:
            issues.append({"row": index, "type": "invalid_device_type"})
        elif not 0 <= prepared["hour_of_day"] <= 23 or prepared["transaction_velocity"] < 0:
            issues.append({"row": index, "type": "invalid_transaction_values"})
        else:
            valid_records.append(prepared)
    return valid_records, issues


def validate_records(records: list[dict]) -> dict:
    valid_records, issues = prepare_uploaded_records(records)
    issue_counts: Counter[str] = Counter(issue["type"] for issue in issues)
    return {
        "records_checked": len(records),
        "valid_records": len(valid_records),
        "issue_counts": dict(issue_counts),
        "issues": issues[:100],
    }
