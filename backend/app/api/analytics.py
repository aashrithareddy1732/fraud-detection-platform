from collections import Counter, defaultdict

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Prediction, Transaction
from app.schemas import AnalyticsRead

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("", response_model=AnalyticsRead)
def analytics(db: Session = Depends(get_db)):
    transactions = db.query(Transaction).all()
    latest: dict[str, Prediction] = {}
    for prediction in db.query(Prediction).order_by(Prediction.id.asc()).all():
        latest[prediction.transaction_id] = prediction

    fraud_vs_legitimate = Counter()
    risk_distribution = Counter({"low": 0, "medium": 0, "high": 0})
    country = Counter()
    category = Counter()
    daily = defaultdict(lambda: {"fraud": 0, "legitimate": 0})
    for transaction in transactions:
        country[transaction.country] += 1
        category[transaction.merchant_category] += 1
        prediction = latest.get(transaction.transaction_id)
        if not prediction:
            continue
        fraud_vs_legitimate[prediction.prediction] += 1
        risk_distribution[prediction.risk_level] += 1
        day = transaction.created_at.date().isoformat()
        daily[day][prediction.prediction] += 1

    return {
        "fraud_vs_legitimate": {"fraud": fraud_vs_legitimate["fraud"], "legitimate": fraud_vs_legitimate["legitimate"]},
        "risk_distribution": dict(risk_distribution),
        "transactions_by_country": dict(country.most_common()),
        "transactions_by_category": dict(category.most_common()),
        "daily_fraud_trend": [
            {"date": day, "fraud": values["fraud"], "legitimate": values["legitimate"]}
            for day, values in sorted(daily.items())
        ],
    }
