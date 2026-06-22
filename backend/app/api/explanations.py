from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import InvestigationReport, Prediction, Transaction
from app.schemas import ExplanationRead, ExplanationRequest
from app.services.fraud_model import deserialize_reasons, fraud_model, serialize_reasons
from app.services.openai_explainer import explain_prediction
from app.services.audit import record_audit

router = APIRouter(prefix="/api", tags=["explanations"])


@router.post("/explain", response_model=ExplanationRead)
def explain(request: ExplanationRequest, db: Session = Depends(get_db)):
    transaction = db.query(Transaction).filter_by(transaction_id=request.transaction_id).first()
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")

    latest = (
        db.query(Prediction)
        .filter_by(transaction_id=request.transaction_id)
        .order_by(Prediction.id.desc())
        .first()
    )

    transaction_payload = {
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

    if latest:
        prediction_payload = {
            "transaction_id": latest.transaction_id,
            "fraud_probability": latest.fraud_probability,
            "risk_score": latest.risk_score,
            "risk_level": latest.risk_level,
            "prediction": latest.prediction,
            "top_reasons": deserialize_reasons(latest.top_reasons),
        }
    else:
        prediction_payload = fraud_model.predict(transaction_payload)
        db.add(
            Prediction(
                transaction_id=prediction_payload["transaction_id"],
                fraud_probability=prediction_payload["fraud_probability"],
                risk_score=prediction_payload["risk_score"],
                risk_level=prediction_payload["risk_level"],
                prediction=prediction_payload["prediction"],
                top_reasons=serialize_reasons(prediction_payload["top_reasons"]),
            )
        )
        db.commit()

    explanation = explain_prediction(prediction_payload, transaction_payload)
    db.add(InvestigationReport(transaction_id=transaction.transaction_id, explanation=explanation))
    record_audit(db, "investigation_report_generated", "transaction", transaction.transaction_id)
    db.commit()

    return ExplanationRead(
        transaction_id=transaction.transaction_id,
        fraud_probability=prediction_payload["fraud_probability"],
        risk_score=prediction_payload["risk_score"],
        risk_level=prediction_payload["risk_level"],
        top_reasons=prediction_payload["top_reasons"],
        explanation=explanation,
    )
