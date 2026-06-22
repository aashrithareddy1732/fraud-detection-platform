from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.config import settings
from app.models import PipelineRun, Prediction, PredictionHistory, Transaction
from app.schemas import BatchPredictionRead, PredictionRead, PredictionRequest
from app.services.audit import record_audit
from app.services.fraud_model import fraud_model, serialize_reasons

router = APIRouter(prefix="/api", tags=["predictions"])


def get_or_create_transaction(request: PredictionRequest, db: Session) -> Transaction:
    if request.transaction_id:
        transaction = db.query(Transaction).filter_by(transaction_id=request.transaction_id).first()
        if not transaction:
            raise HTTPException(status_code=404, detail="Transaction not found")
        return transaction

    if request.transaction:
        existing = db.query(Transaction).filter_by(transaction_id=request.transaction.transaction_id).first()
        if existing:
            return existing
        transaction = Transaction(**request.transaction.model_dump())
        db.add(transaction)
        db.commit()
        db.refresh(transaction)
        return transaction

    raise HTTPException(status_code=400, detail="Provide transaction_id or transaction")


def score_transaction(transaction: Transaction, db: Session) -> dict:
    """Persist one current prediction per transaction for consistent dashboard metrics."""
    result = fraud_model.predict(
        {
            "transaction_id": transaction.transaction_id,
            "customer_id": transaction.customer_id,
            "amount": transaction.amount,
            "merchant_category": transaction.merchant_category,
            "country": transaction.country,
            "hour_of_day": transaction.hour_of_day,
            "is_weekend": transaction.is_weekend,
            "device_type": transaction.device_type,
            "transaction_velocity": transaction.transaction_velocity,
        }
    )
    prediction = (
        db.query(Prediction)
        .filter_by(transaction_id=transaction.transaction_id)
        .order_by(Prediction.id.desc())
        .first()
    )
    if prediction is None:
        prediction = Prediction(transaction_id=transaction.transaction_id)
        db.add(prediction)

    prediction.fraud_probability = result["fraud_probability"]
    prediction.risk_score = result["risk_score"]
    prediction.risk_level = result["risk_level"]
    prediction.prediction = result["prediction"]
    prediction.top_reasons = serialize_reasons(result["top_reasons"])
    db.add(
        PredictionHistory(
            transaction_id=transaction.transaction_id,
            fraud_probability=result["fraud_probability"],
            risk_score=result["risk_score"],
            risk_level=result["risk_level"],
            prediction=result["prediction"],
            model_version=settings.model_version,
        )
    )
    record_audit(db, "prediction_scored", "transaction", transaction.transaction_id, {"model_version": settings.model_version, "risk_level": result["risk_level"]})
    return result


@router.post("/predict", response_model=PredictionRead)
def predict(request: PredictionRequest, db: Session = Depends(get_db)):
    transaction = get_or_create_transaction(request, db)
    result = score_transaction(transaction, db)
    db.commit()
    return result


@router.post("/predict/all", response_model=BatchPredictionRead)
def predict_all(db: Session = Depends(get_db)):
    transactions = db.query(Transaction).order_by(Transaction.created_at.desc()).all()
    results = [score_transaction(transaction, db) for transaction in transactions]
    db.add(PipelineRun(pipeline_name="batch_scoring", status="completed", records_processed=len(results)))
    db.commit()
    return {"scored_count": len(results), "predictions": results}
