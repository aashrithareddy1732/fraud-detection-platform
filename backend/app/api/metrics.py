from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Prediction, Transaction
from app.schemas import MetricsRead

router = APIRouter(prefix="/api/metrics", tags=["metrics"])


@router.get("", response_model=MetricsRead)
def metrics(db: Session = Depends(get_db)):
    total_transactions = db.query(Transaction).count()
    latest_prediction_ids = (
        db.query(func.max(Prediction.id).label("prediction_id"))
        .group_by(Prediction.transaction_id)
        .subquery()
    )
    latest_predictions = db.query(Prediction).join(
        latest_prediction_ids, Prediction.id == latest_prediction_ids.c.prediction_id
    )
    fraud_detected = latest_predictions.filter(Prediction.prediction == "fraud").count()
    average_risk = latest_predictions.with_entities(func.avg(Prediction.risk_score)).scalar() or 0
    high_risk = latest_predictions.filter(Prediction.risk_level == "high").count()
    return MetricsRead(
        total_transactions=total_transactions,
        fraud_detected=fraud_detected,
        average_risk_score=round(float(average_risk), 2),
        high_risk_transactions=high_risk,
    )
