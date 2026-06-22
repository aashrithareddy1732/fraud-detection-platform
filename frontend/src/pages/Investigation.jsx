import { useEffect, useMemo, useState } from "react";
import { explainTransaction, getApiErrorMessage, getTimeline, getTransactions, predictTransaction, recordInvestigationAction } from "../api.js";
import RiskBadge from "../components/RiskBadge.jsx";

export default function Investigation({ selectedTransactionId, onSelectTransaction, onDataChanged, refreshVersion }) {
  const [transactions, setTransactions] = useState([]);
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [timeline, setTimeline] = useState([]);
  const [actionLoading, setActionLoading] = useState(false);

  const activeId = selectedTransactionId || transactions[0]?.transaction_id || "";
  const activeTransaction = useMemo(
    () => transactions.find((transaction) => transaction.transaction_id === activeId),
    [transactions, activeId]
  );

  async function loadTransactions() {
    setLoading(true);
    setError("");
    try {
      const data = await getTransactions();
      setTransactions(data);
      if (!selectedTransactionId && data.length) {
        onSelectTransaction(data[0].transaction_id);
      }
    } catch (requestError) {
      setError(getApiErrorMessage(requestError, "Could not load transactions for investigation."));
    } finally {
      setLoading(false);
    }
  }

  async function investigate(transactionId) {
    if (!transactionId) return;
    setLoading(true);
    setError("");
    setReport(null);
    try {
      await predictTransaction(transactionId);
      const explanation = await explainTransaction(transactionId);
      setReport(explanation);
      setTimeline(await getTimeline(transactionId));
      onDataChanged();
    } catch (requestError) {
      setError(getApiErrorMessage(requestError, "Could not prepare the investigation report."));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadTransactions();
  }, [refreshVersion]);

  useEffect(() => {
    if (activeId) {
      investigate(activeId);
    }
  }, [activeId]);

  async function handleAction(action) {
    if (!activeId) return;
    setActionLoading(true);
    try {
      await recordInvestigationAction(activeId, action);
      setTimeline(await getTimeline(activeId));
    } catch (requestError) {
      setError(getApiErrorMessage(requestError, "Could not record the investigation action."));
    } finally {
      setActionLoading(false);
    }
  }

  return (
    <div className="page two-column">
      <section>
        <div className="page-header">
          <div>
            <p className="eyebrow">AI Fraud Investigation Platform</p>
            <h2>Case Investigation</h2>
          </div>
        </div>
        <label className="field-label" htmlFor="transaction-select">
          Transaction
        </label>
        <select
          id="transaction-select"
          value={activeId}
          disabled={loading || !transactions.length}
          onChange={(event) => onSelectTransaction(event.target.value)}
        >
          {transactions.map((transaction) => (
            <option key={transaction.transaction_id} value={transaction.transaction_id}>{transaction.transaction_summary}</option>
          ))}
        </select>
        {activeTransaction && (
          <div className="detail-list">
            <p><span>Transaction Summary</span>{activeTransaction.transaction_summary}</p>
            <p><span>Customer</span>{activeTransaction.customer_id}</p>
            <p><span>Amount</span>${activeTransaction.amount.toLocaleString()}</p>
            <p><span>Country</span>{activeTransaction.country}</p>
            <p><span>Category</span>{activeTransaction.merchant_category}</p>
            <p><span>Velocity</span>{activeTransaction.transaction_velocity}</p>
          </div>
        )}
      </section>

      <section className="investigation-panel">
        {loading && <p className="muted">Preparing investigation...</p>}
        {error && <p className="message error-message">{error}</p>}
        {report && (
          <>
            <div className="score-row">
              <div>
                <span>Fraud Probability</span>
                <strong>{Math.round(report.fraud_probability * 100)}%</strong>
              </div>
              <div>
                <span>Risk Score</span>
                <strong>{report.risk_score}</strong>
              </div>
              <RiskBadge level={report.risk_level} />
            </div>
            <h3>Top Reasons</h3>
            <ul className="reason-list">
              {report.top_reasons.map((reason) => (
                <li key={reason}>{reason}</li>
              ))}
            </ul>
            <h3>AI Explanation</h3>
            <p>{report.explanation}</p>
            <div className="recommendation-panel">
              <h3>Recommended Action</h3>
              <p>{report.risk_level === "high" ? "Block or hold for analyst review." : report.risk_level === "medium" ? "Review supporting customer and merchant context." : "Approve unless external signals contradict the score."}</p>
              <div className="button-group action-buttons">
                <button className="secondary" disabled={actionLoading} onClick={() => handleAction("approve")}>Approve</button>
                <button className="secondary" disabled={actionLoading} onClick={() => handleAction("review")}>Review</button>
                <button className="danger-button" disabled={actionLoading} onClick={() => handleAction("block")}>Block</button>
              </div>
            </div>
            <div className="timeline">
              <h3>Transaction Timeline</h3>
              {timeline.map((event, index) => <p key={`${event.type}-${index}`}><span>{new Date(event.created_at).toLocaleString()}</span>{event.detail}</p>)}
            </div>
          </>
        )}
        {!loading && !transactions.length && <p className="empty-state">Generate transactions to begin.</p>}
      </section>
    </div>
  );
}
