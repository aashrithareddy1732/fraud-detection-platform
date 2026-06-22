from pathlib import Path
import json

import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, precision_score, recall_score, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from app.services.feature_engineering import transactions_to_training_frame
from app.services.transaction_generator import generate_transactions, synthetic_label
from app.config import settings
from app.database import Base, SessionLocal, engine
from app.models import ModelRun


def train_model(sample_size: int = 3000) -> Path:
    """Train on synthetic records until the real dataset is integrated."""
    transactions = generate_transactions(sample_size)
    labels = [synthetic_label(transaction) for transaction in transactions]
    features = transactions_to_training_frame(transactions)

    x_train, x_test, y_train, y_test = train_test_split(
        features,
        labels,
        test_size=0.2,
        random_state=42,
        stratify=labels,
    )

    model = Pipeline(
        steps=[
            ("scaler", StandardScaler()),
            ("classifier", RandomForestClassifier(n_estimators=120, random_state=42)),
        ]
    )
    model.fit(x_train, y_train)

    probabilities = model.predict_proba(x_test)[:, 1]
    predictions = (probabilities >= 0.5).astype(int)
    metrics = {
        "accuracy": float(accuracy_score(y_test, predictions)),
        "precision": float(precision_score(y_test, predictions, zero_division=0)),
        "recall": float(recall_score(y_test, predictions, zero_division=0)),
        "f1_score": float(f1_score(y_test, predictions, zero_division=0)),
        "roc_auc": float(roc_auc_score(y_test, probabilities)),
        "confusion_matrix": confusion_matrix(y_test, predictions).tolist(),
    }

    model_path = Path(__file__).with_name("model.joblib")
    joblib.dump(model, model_path)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        db.add(
            ModelRun(
                version=settings.model_version,
                dataset_name="synthetic_generator",
                accuracy=metrics["accuracy"],
                precision=metrics["precision"],
                recall=metrics["recall"],
                f1_score=metrics["f1_score"],
                roc_auc=metrics["roc_auc"],
                confusion_matrix=json.dumps(metrics["confusion_matrix"]),
            )
        )
        db.commit()
    finally:
        db.close()
    return model_path


if __name__ == "__main__":
    path = train_model()
    print(f"Saved model to {path}")
