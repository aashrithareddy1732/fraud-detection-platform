import { useEffect, useState } from "react";
import { getAnalytics, getApiErrorMessage } from "../api.js";
import EmptyState from "../components/EmptyState.jsx";
import LoadingSkeleton from "../components/LoadingSkeleton.jsx";

function RankedList({ title, values }) {
  return <section className="analytics-card"><h3>{title}</h3>{Object.keys(values).length ? <ol>{Object.entries(values).map(([name, count]) => <li key={name}><span>{name}</span><strong>{count}</strong></li>)}</ol> : <p className="muted">No data yet.</p>}</section>;
}

export default function Analytics({ refreshVersion }) {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  useEffect(() => {
    getAnalytics().then(setData).catch((requestError) => setError(getApiErrorMessage(requestError, "Could not load analytics.")));
  }, [refreshVersion]);
  if (error) return <div className="page"><p className="error-message">{error}</p></div>;
  if (!data) return <div className="page"><LoadingSkeleton rows={5} /></div>;
  if (!Object.keys(data.transactions_by_country).length) return <div className="page"><EmptyState title="Analytics will appear here" description="Generate and score transactions to build operational insights." /></div>;
  const maxTrend = Math.max(...data.daily_fraud_trend.map((point) => point.fraud + point.legitimate), 1);
  return <div className="page"><div><p className="eyebrow">Fraud Risk Operations</p><h2>Fraud Analytics</h2></div><div className="analytics-grid"><RankedList title="Transactions by Country" values={data.transactions_by_country} /><RankedList title="Transactions by Merchant Category" values={data.transactions_by_category} /></div><section className="analytics-card"><h3>Daily Fraud Trend</h3><div className="trend-chart">{data.daily_fraud_trend.map((point) => <div key={point.date} className="trend-column" title={`${point.date}: ${point.fraud} fraud`}><i style={{ height: `${((point.fraud + point.legitimate) / maxTrend) * 100}%` }} /><span>{point.date.slice(5)}</span></div>)}</div></section></div>;
}
