import { useEffect, useState } from "react";
import { getApiErrorMessage, getModelRuns } from "../api.js";
import EmptyState from "../components/EmptyState.jsx";

const formatMetric = (value) => value == null ? "-" : `${(value * 100).toFixed(1)}%`;

export default function ModelEvaluation({ refreshVersion }) {
  const [runs, setRuns] = useState([]); const [error, setError] = useState("");
  useEffect(() => { getModelRuns().then(setRuns).catch((requestError) => setError(getApiErrorMessage(requestError, "Could not load model runs."))); }, [refreshVersion]);
  if (error) return <div className="page"><p className="error-message">{error}</p></div>;
  if (!runs.length) return <div className="page"><EmptyState title="No model run recorded" description="Run python -m app.ml.train to train the synthetic baseline and capture evaluation metrics." /></div>;
  const run = runs[0];
  return <div className="page"><div><p className="eyebrow">Model Governance</p><h2>Model Performance</h2></div><div className="stats-grid"><div className="stat-card"><span>Accuracy</span><strong>{formatMetric(run.accuracy)}</strong></div><div className="stat-card"><span>Precision</span><strong>{formatMetric(run.precision)}</strong></div><div className="stat-card"><span>Recall</span><strong>{formatMetric(run.recall)}</strong></div><div className="stat-card"><span>F1 Score</span><strong>{formatMetric(run.f1_score)}</strong></div></div><section className="analytics-card"><h3>{run.version} on {run.dataset_name}</h3><p>ROC-AUC: <strong>{formatMetric(run.roc_auc)}</strong></p><p>Confusion matrix: <code>{JSON.stringify(run.confusion_matrix)}</code></p><p className="muted">Trained {new Date(run.trained_at).toLocaleString()}</p></section></div>;
}
