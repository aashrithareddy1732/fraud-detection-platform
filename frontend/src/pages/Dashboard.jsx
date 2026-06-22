import { useEffect, useState } from "react";
import { generateTransactions, getApiErrorMessage, getMetrics, getTransactions, predictTransaction } from "../api.js";
import EmptyState from "../components/EmptyState.jsx";
import LoadingSkeleton from "../components/LoadingSkeleton.jsx";
import RiskCharts from "../components/RiskCharts.jsx";
import StatCard from "../components/StatCard.jsx";

export default function Dashboard({ refreshVersion, onDataChanged }) {
  const [metrics, setMetrics] = useState(null);
  const [transactions, setTransactions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function loadDashboard() {
    setLoading(true);
    setError("");
    try {
      const [metricData, transactionData] = await Promise.all([getMetrics(), getTransactions()]);
      setMetrics(metricData);
      setTransactions(transactionData);
    } catch (requestError) {
      setError(getApiErrorMessage(requestError, "Could not load dashboard data."));
    } finally {
      setLoading(false);
    }
  }

  async function seedAndScore() {
    setLoading(true);
    setError("");
    try {
      const generated = await generateTransactions(30);
      await Promise.all(generated.map((item) => predictTransaction(item.transaction_id)));
      await loadDashboard();
      onDataChanged();
    } catch (requestError) {
      setError(getApiErrorMessage(requestError, "Could not generate and score transactions."));
      setLoading(false);
    }
  }

  useEffect(() => {
    loadDashboard();
  }, [refreshVersion]);

  return (
    <div className="page dashboard-page">
      <div className="page-header dashboard-header">
        <div>
          <p className="eyebrow">Fraud Risk Operations</p>
          <h2>Transaction Risk Command Center</h2>
          <p className="page-subtitle">Monitor synthetic card activity, triage risk, and explain every decision.</p>
        </div>
        <button onClick={seedAndScore} disabled={loading}>
          {loading ? "Working..." : "Generate and score batch"}
        </button>
      </div>

      {error && <p className="message error-message">{error}</p>}
      {loading && !metrics ? <LoadingSkeleton rows={4} /> : (
        <div className="stats-grid">
          <StatCard label="Total Transactions" value={metrics?.total_transactions ?? 0} />
          <StatCard label="Fraud Detected" value={metrics?.fraud_detected ?? 0} />
          <StatCard label="Average Risk Score" value={metrics?.average_risk_score ?? 0} />
          <StatCard label="High-Risk Transactions" value={metrics?.high_risk_transactions ?? 0} />
        </div>
      )}

      {!loading && !transactions.length ? (
        <EmptyState title="No activity to review" description="Generate a synthetic batch to populate the monitoring workspace." />
      ) : (
        <RiskCharts transactions={transactions} />
      )}
    </div>
  );
}
