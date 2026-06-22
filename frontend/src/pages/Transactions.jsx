import { useEffect, useMemo, useState } from "react";
import { downloadTransactionTemplate, generateTransactions, getApiErrorMessage, getTransactions, predictAllTransactions, predictTransaction, uploadTransactions } from "../api.js";
import TransactionTable from "../components/TransactionTable.jsx";

const initialFilters = { riskLevel: "all", country: "all", category: "all", prediction: "all", minAmount: "", maxAmount: "", startDate: "", endDate: "" };
const PAGE_SIZE = 20;

export default function Transactions({ onInvestigate, onDataChanged, refreshVersion }) {
  const [transactions, setTransactions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [batchScoring, setBatchScoring] = useState(false);
  const [predictingId, setPredictingId] = useState("");
  const [error, setError] = useState("");
  const [filters, setFilters] = useState(initialFilters);
  const [sort, setSort] = useState({ key: "created_at", direction: "desc" });
  const [page, setPage] = useState(1);
  const [uploading, setUploading] = useState(false);
  const [uploadIssues, setUploadIssues] = useState([]);
  const [uploadMessage, setUploadMessage] = useState("");

  async function loadTransactions() {
    setLoading(true);
    setError("");
    try {
      setTransactions(await getTransactions());
    } catch (requestError) {
      setError(getApiErrorMessage(requestError, "Could not load transactions."));
    } finally {
      setLoading(false);
    }
  }

  async function handleGenerate() {
    setLoading(true);
    setError("");
    try {
      await generateTransactions(15);
      await loadTransactions();
      onDataChanged();
    } catch (requestError) {
      setError(getApiErrorMessage(requestError, "Could not generate transactions."));
    } finally {
      setLoading(false);
    }
  }

  async function handleUpload(event) {
    const file = event.target.files?.[0];
    if (!file) return;
    setUploading(true);
    setError("");
    setUploadMessage("");
    setUploadIssues([]);
    try {
      const result = await uploadTransactions(file);
      setUploadMessage(`${result.imported_count} transactions imported successfully.`);
      await loadTransactions();
      onDataChanged();
    } catch (requestError) {
      const detail = requestError.response?.data?.detail;
      setError(getApiErrorMessage(requestError, "Could not upload transactions."));
      setUploadIssues(Array.isArray(detail?.issues) ? detail.issues : []);
    } finally {
      setUploading(false);
      event.target.value = "";
    }
  }

  async function handleScoreAll() {
    setBatchScoring(true);
    setError("");
    try {
      await predictAllTransactions();
      await loadTransactions();
      onDataChanged();
    } catch (requestError) {
      setError(getApiErrorMessage(requestError, "Could not score all transactions."));
    } finally {
      setBatchScoring(false);
    }
  }

  async function handlePredict(transactionId) {
    setPredictingId(transactionId);
    setError("");
    try {
      await predictTransaction(transactionId);
      await loadTransactions();
      onDataChanged();
    } catch (requestError) {
      setError(getApiErrorMessage(requestError, "Could not score this transaction."));
    } finally {
      setPredictingId("");
    }
  }

  function updateFilter(name, value) {
    setFilters((current) => ({ ...current, [name]: value }));
    setPage(1);
  }

  function handleSort(key) {
    setSort((current) => ({
      key,
      direction: current.key === key && current.direction === "asc" ? "desc" : "asc",
    }));
  }

  const countries = useMemo(() => [...new Set(transactions.map((transaction) => transaction.country))].sort(), [transactions]);
  const categories = useMemo(() => [...new Set(transactions.map((transaction) => transaction.merchant_category))].sort(), [transactions]);
  const visibleTransactions = useMemo(() => {
    const riskRank = { low: 1, medium: 2, high: 3 };
    return transactions
      .filter((transaction) => filters.riskLevel === "all" || transaction.latest_prediction?.risk_level === filters.riskLevel)
      .filter((transaction) => filters.country === "all" || transaction.country === filters.country)
      .filter((transaction) => filters.category === "all" || transaction.merchant_category === filters.category)
      .filter((transaction) => filters.prediction === "all" || transaction.latest_prediction?.prediction === filters.prediction)
      .filter((transaction) => !filters.minAmount || transaction.amount >= Number(filters.minAmount))
      .filter((transaction) => !filters.maxAmount || transaction.amount <= Number(filters.maxAmount))
      .filter((transaction) => !filters.startDate || transaction.created_at.slice(0, 10) >= filters.startDate)
      .filter((transaction) => !filters.endDate || transaction.created_at.slice(0, 10) <= filters.endDate)
      .sort((left, right) => {
        const getValue = (transaction) => {
          if (sort.key === "risk_score") return transaction.latest_prediction?.risk_score ?? -1;
          if (sort.key === "risk_level") return riskRank[transaction.latest_prediction?.risk_level] ?? 0;
          return transaction[sort.key];
        };
        const a = getValue(left);
        const b = getValue(right);
        const comparison = typeof a === "string" ? a.localeCompare(b) : a - b;
        return sort.direction === "asc" ? comparison : -comparison;
      });
  }, [transactions, filters, sort]);
  const pageCount = Math.max(1, Math.ceil(visibleTransactions.length / PAGE_SIZE));
  const paginatedTransactions = visibleTransactions.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);

  function exportCsv() {
    const header = ["transaction_id", "amount", "country", "merchant_category", "risk_score", "risk_level", "prediction"];
    const lines = visibleTransactions.map((transaction) => [transaction.transaction_id, transaction.amount, transaction.country, transaction.merchant_category, transaction.latest_prediction?.risk_score ?? "", transaction.latest_prediction?.risk_level ?? "", transaction.latest_prediction?.prediction ?? ""].join(","));
    const url = URL.createObjectURL(new Blob([[header.join(","), ...lines].join("\n")], { type: "text/csv" }));
    const link = document.createElement("a"); link.href = url; link.download = "fraud-transactions.csv"; link.click(); URL.revokeObjectURL(url);
  }

  useEffect(() => {
    loadTransactions();
  }, [refreshVersion]);

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <p className="eyebrow">Transaction Monitor</p>
          <h2>AI Fraud Investigation Platform</h2>
        </div>
        <div className="button-group">
          <button className="secondary" onClick={handleScoreAll} disabled={loading || batchScoring || !transactions.length}>
            {batchScoring ? "Scoring all..." : "Score all transactions"}
          </button>
          <button onClick={handleGenerate} disabled={loading || batchScoring}>
            {loading ? "Generating..." : "Generate transactions"}
          </button>
        </div>
      </div>

      <section className="upload-panel">
        <div>
          <p className="field-label">Import Transactions</p>
          <p className="muted">Upload a CSV with transaction details. Missing transaction and customer IDs are generated automatically.</p>
        </div>
        <div className="button-group">
          <button className="secondary" onClick={downloadTransactionTemplate}>Download CSV template</button>
          <label className="upload-button">
            {uploading ? "Uploading..." : "Upload CSV"}
            <input type="file" accept=".csv,text/csv" disabled={uploading} onChange={handleUpload} />
          </label>
        </div>
      </section>
      {uploadMessage && <p className="message success-message">{uploadMessage}</p>}
      {uploadIssues.length > 0 && <section className="validation-panel"><strong>CSV validation errors</strong><ul>{uploadIssues.map((issue, index) => <li key={`${issue.row}-${index}`}>Row {issue.row}: {issue.type}{issue.fields ? ` (${issue.fields.join(", ")})` : issue.detail ? ` (${issue.detail})` : ""}</li>)}</ul></section>}

      <div className="filter-bar" aria-label="Transaction filters">
        <label>Risk level
          <select value={filters.riskLevel} onChange={(event) => updateFilter("riskLevel", event.target.value)}>
            <option value="all">All levels</option>
            <option value="low">Low</option>
            <option value="medium">Medium</option>
            <option value="high">High</option>
          </select>
        </label>
        <label>Country
          <select value={filters.country} onChange={(event) => updateFilter("country", event.target.value)}>
            <option value="all">All countries</option>
            {countries.map((country) => <option key={country} value={country}>{country}</option>)}
          </select>
        </label>
        <label>Merchant category
          <select value={filters.category} onChange={(event) => updateFilter("category", event.target.value)}>
            <option value="all">All categories</option>
            {categories.map((category) => <option key={category} value={category}>{category}</option>)}
          </select>
        </label>
        <label>Prediction
          <select value={filters.prediction} onChange={(event) => updateFilter("prediction", event.target.value)}><option value="all">All predictions</option><option value="fraud">Fraud</option><option value="legitimate">Legitimate</option></select>
        </label>
        <label>Min amount<input type="number" min="0" value={filters.minAmount} onChange={(event) => updateFilter("minAmount", event.target.value)} /></label>
        <label>Max amount<input type="number" min="0" value={filters.maxAmount} onChange={(event) => updateFilter("maxAmount", event.target.value)} /></label>
        <label>Start date<input type="date" value={filters.startDate} onChange={(event) => updateFilter("startDate", event.target.value)} /></label>
        <label>End date<input type="date" value={filters.endDate} onChange={(event) => updateFilter("endDate", event.target.value)} /></label>
        <button className="text-button" onClick={() => setFilters(initialFilters)} disabled={loading}>Clear filters</button>
        <button className="text-button" onClick={exportCsv} disabled={!visibleTransactions.length}>Export CSV</button>
      </div>

      {error && <p className="message error-message">{error}</p>}
      <p className="result-count">Showing {visibleTransactions.length} of {transactions.length} transactions</p>
      <TransactionTable
        transactions={paginatedTransactions}
        onPredict={handlePredict}
        onInvestigate={onInvestigate}
        predictingId={predictingId}
        disabled={loading || batchScoring}
        loading={loading}
        sort={sort}
        onSort={handleSort}
      />
      <div className="pagination"><button className="secondary" disabled={page === 1} onClick={() => setPage((value) => value - 1)}>Previous</button><span>Page {page} of {pageCount}</span><button className="secondary" disabled={page === pageCount} onClick={() => setPage((value) => value + 1)}>Next</button></div>
    </div>
  );
}
