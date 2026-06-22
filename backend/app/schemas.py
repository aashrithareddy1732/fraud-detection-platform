from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class TransactionBase(BaseModel):
    transaction_id: str
    customer_id: str
    amount: float = Field(..., ge=0)
    merchant_category: str
    country: str
    hour_of_day: int = Field(..., ge=0, le=23)
    is_weekend: bool
    device_type: str
    transaction_velocity: int = Field(..., ge=0)


class TransactionCreate(TransactionBase):
    pass


class TransactionRead(TransactionBase):
    transaction_summary: str
    created_at: datetime
    latest_prediction: Optional["PredictionRead"] = None

    class Config:
        from_attributes = True


class GenerateTransactionsRequest(BaseModel):
    count: int = Field(default=25, ge=1, le=500)


class UploadTransactionsRead(BaseModel):
    imported_count: int
    transactions: List[TransactionRead]


class PredictionRequest(BaseModel):
    transaction_id: Optional[str] = None
    transaction: Optional[TransactionCreate] = None


class PredictionRead(BaseModel):
    transaction_id: str
    fraud_probability: float
    risk_score: int
    risk_level: str
    prediction: str
    top_reasons: List[str]


class BatchPredictionRead(BaseModel):
    scored_count: int
    predictions: List[PredictionRead]


class MetricsRead(BaseModel):
    total_transactions: int
    fraud_detected: int
    average_risk_score: float
    high_risk_transactions: int


class ExplanationRequest(BaseModel):
    transaction_id: str


class ExplanationRead(BaseModel):
    transaction_id: str
    fraud_probability: float
    risk_score: int
    risk_level: str
    top_reasons: List[str]
    explanation: str


class InvestigationActionRequest(BaseModel):
    transaction_id: str
    action: str = Field(..., pattern="^(approve|review|block)$")
    note: str = Field(default="", max_length=1000)


class InvestigationActionRead(InvestigationActionRequest):
    actor: str
    created_at: datetime


class AnalyticsRead(BaseModel):
    fraud_vs_legitimate: dict[str, int]
    risk_distribution: dict[str, int]
    transactions_by_country: dict[str, int]
    transactions_by_category: dict[str, int]
    daily_fraud_trend: list[dict[str, int | str]]


class ModelRunRead(BaseModel):
    version: str
    accuracy: float | None = None
    precision: float | None = None
    recall: float | None = None
    f1_score: float | None = None
    roc_auc: float | None = None
    confusion_matrix: list[list[int]] = []
    dataset_name: str
    trained_at: datetime


class PipelineStatusRead(BaseModel):
    pipeline_name: str
    status: str
    records_processed: int
    details: dict
    created_at: datetime


class DataQualityRequest(BaseModel):
    records: list[dict]


TransactionRead.model_rebuild()
