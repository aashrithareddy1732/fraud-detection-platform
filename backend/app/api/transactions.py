import csv
from io import StringIO

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Prediction, Transaction
from app.schemas import GenerateTransactionsRequest, TransactionRead, UploadTransactionsRead
from app.services.audit import record_audit
from app.services.data_quality import prepare_uploaded_records, transaction_summary
from app.services.fraud_model import deserialize_reasons
from app.services.transaction_generator import generate_transactions

router = APIRouter(prefix="/api/transactions", tags=["transactions"])


def to_transaction_read(transaction: Transaction) -> TransactionRead:
    latest_prediction = None
    if transaction.predictions:
        prediction = max(transaction.predictions, key=lambda item: item.id)
        latest_prediction = {
            "transaction_id": prediction.transaction_id,
            "fraud_probability": prediction.fraud_probability,
            "risk_score": prediction.risk_score,
            "risk_level": prediction.risk_level,
            "prediction": prediction.prediction,
            "top_reasons": deserialize_reasons(prediction.top_reasons),
        }
    return TransactionRead(
        transaction_id=transaction.transaction_id,
        transaction_summary=transaction_summary({
            "merchant_category": transaction.merchant_category,
            "country": transaction.country,
            "amount": transaction.amount,
        }),
        customer_id=transaction.customer_id,
        amount=transaction.amount,
        merchant_category=transaction.merchant_category,
        country=transaction.country,
        hour_of_day=transaction.hour_of_day,
        is_weekend=transaction.is_weekend,
        device_type=transaction.device_type,
        transaction_velocity=transaction.transaction_velocity,
        created_at=transaction.created_at,
        latest_prediction=latest_prediction,
    )


@router.post("/generate", response_model=list[TransactionRead])
def generate(request: GenerateTransactionsRequest, db: Session = Depends(get_db)):
    transactions = []
    for item in generate_transactions(request.count):
        record = Transaction(**item)
        db.add(record)
        transactions.append(record)
    db.commit()
    for transaction in transactions:
        db.refresh(transaction)
    return [to_transaction_read(transaction) for transaction in transactions]


@router.get("/template")
def download_template():
    columns = "transaction_id,customer_id,amount,merchant_category,country,hour_of_day,is_weekend,device_type,transaction_velocity"
    example = "txn_example_001,cust_example_001,99.95,fuel,US,14,false,mobile,2"
    return Response(
        content=f"{columns}\n{example}\n",
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=transaction-upload-template.csv"},
    )


@router.post("/upload", response_model=UploadTransactionsRead)
async def upload_transactions(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Upload a .csv file.")
    content = await file.read()
    try:
        records = list(csv.DictReader(StringIO(content.decode("utf-8-sig"))))
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=400, detail="CSV must use UTF-8 encoding.") from exc
    if not records:
        raise HTTPException(status_code=400, detail="CSV contains no data rows.")

    prepared, issues = prepare_uploaded_records(records)
    seen_ids: set[str] = set()
    duplicate_ids: set[str] = set()
    for record in prepared:
        if record["transaction_id"] in seen_ids:
            duplicate_ids.add(record["transaction_id"])
        seen_ids.add(record["transaction_id"])
    if duplicate_ids:
        issues.extend({"row": index, "type": "duplicate_transaction_id", "transaction_id": record["transaction_id"]} for index, record in enumerate(prepared, start=2) if record["transaction_id"] in duplicate_ids)
    if issues:
        raise HTTPException(status_code=422, detail={"message": "Upload validation failed. No rows were imported.", "issues": issues[:100]})
    existing_ids = {
        value[0] for value in db.query(Transaction.transaction_id).filter(Transaction.transaction_id.in_([record["transaction_id"] for record in prepared])).all()
    }
    if existing_ids:
        raise HTTPException(status_code=409, detail={"message": "CSV contains transaction IDs already stored.", "transaction_ids": sorted(existing_ids)})
    transactions = [Transaction(**record) for record in prepared]
    db.add_all(transactions)
    record_audit(db, "csv_transactions_uploaded", "transaction_batch", file.filename, {"imported_count": len(transactions)})
    db.commit()
    for transaction in transactions:
        db.refresh(transaction)
    return {"imported_count": len(transactions), "transactions": [to_transaction_read(transaction) for transaction in transactions]}


@router.get("", response_model=list[TransactionRead])
def list_transactions(db: Session = Depends(get_db)):
    transactions = (
        db.query(Transaction)
        .outerjoin(Prediction)
        .order_by(Transaction.created_at.desc())
        .limit(250)
        .all()
    )
    return [to_transaction_read(transaction) for transaction in transactions]
