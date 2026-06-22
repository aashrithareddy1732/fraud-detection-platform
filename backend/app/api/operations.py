import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import InvestigationAction, InvestigationReport, ModelRun, PipelineRun, PredictionHistory, Transaction
from app.schemas import DataQualityRequest, InvestigationActionRead, InvestigationActionRequest, ModelRunRead, PipelineStatusRead
from app.services.audit import record_audit
from app.services.data_quality import validate_records

router = APIRouter(prefix="/api", tags=["operations"])


@router.post("/investigations/action", response_model=InvestigationActionRead)
def record_action(request: InvestigationActionRequest, db: Session = Depends(get_db)):
    if not db.query(Transaction).filter_by(transaction_id=request.transaction_id).first():
        raise HTTPException(status_code=404, detail="Transaction not found")
    action = InvestigationAction(**request.model_dump(), actor="local_analyst")
    db.add(action)
    record_audit(db, "investigation_action", "transaction", request.transaction_id, {"action": request.action})
    db.commit()
    db.refresh(action)
    return action


@router.get("/investigations/{transaction_id}/timeline")
def investigation_timeline(transaction_id: str, db: Session = Depends(get_db)):
    if not db.query(Transaction).filter_by(transaction_id=transaction_id).first():
        raise HTTPException(status_code=404, detail="Transaction not found")
    events = []
    for item in db.query(PredictionHistory).filter_by(transaction_id=transaction_id).all():
        events.append({"type": "prediction", "created_at": item.created_at, "detail": f"{item.risk_level} risk score {item.risk_score}"})
    for item in db.query(InvestigationReport).filter_by(transaction_id=transaction_id).all():
        events.append({"type": "ai_report", "created_at": item.created_at, "detail": "Investigation report generated"})
    for item in db.query(InvestigationAction).filter_by(transaction_id=transaction_id).all():
        events.append({"type": "action", "created_at": item.created_at, "detail": f"Analyst selected {item.action}"})
    return sorted(events, key=lambda item: item["created_at"], reverse=True)


@router.get("/pipeline/runs", response_model=list[PipelineStatusRead])
def pipeline_runs(db: Session = Depends(get_db)):
    return [
        {**{"pipeline_name": run.pipeline_name, "status": run.status, "records_processed": run.records_processed, "created_at": run.created_at}, "details": json.loads(run.details)}
        for run in db.query(PipelineRun).order_by(PipelineRun.id.desc()).limit(20)
    ]


@router.post("/pipeline/validate")
def validate_pipeline_data(request: DataQualityRequest, db: Session = Depends(get_db)):
    report = validate_records(request.records)
    db.add(PipelineRun(pipeline_name="data_quality_validation", status="completed", records_processed=len(request.records), details=json.dumps(report)))
    record_audit(db, "data_quality_validated", "pipeline", "data_quality_validation", {"records_checked": len(request.records)})
    db.commit()
    return report


@router.get("/models/runs", response_model=list[ModelRunRead])
def model_runs(db: Session = Depends(get_db)):
    return [
        {
            "version": run.version, "accuracy": run.accuracy, "precision": run.precision,
            "recall": run.recall, "f1_score": run.f1_score, "roc_auc": run.roc_auc,
            "confusion_matrix": json.loads(run.confusion_matrix), "dataset_name": run.dataset_name,
            "trained_at": run.trained_at,
        }
        for run in db.query(ModelRun).order_by(ModelRun.id.desc()).limit(20)
    ]
