import EmptyState from "./EmptyState.jsx";
import LoadingSkeleton from "./LoadingSkeleton.jsx";
import RiskBadge from "./RiskBadge.jsx";

function SortHeader({ label, column, sort, onSort }) {
  const active = sort.key === column;
  const direction = active ? (sort.direction === "asc" ? "ascending" : "descending") : "none";
  return (
    <th aria-sort={direction}>
      <button className={`sort-button ${active ? "active" : ""}`} onClick={() => onSort(column)}>
        {label}<span className="sort-indicator" aria-hidden="true" />
      </button>
    </th>
  );
}

export default function TransactionTable({ transactions, onInvestigate, onPredict, predictingId, disabled, loading, sort, onSort }) {
  if (loading) {
    return <div className="table-wrap"><LoadingSkeleton rows={7} /></div>;
  }

  if (!transactions.length) {
    return (
      <div className="table-wrap">
        <EmptyState title="No matching transactions" description="Try changing the filters or generate a new synthetic batch." />
      </div>
    );
  }

  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <SortHeader label="Transaction Summary" column="transaction_summary" sort={sort} onSort={onSort} />
            <SortHeader label="Amount" column="amount" sort={sort} onSort={onSort} />
            <SortHeader label="Country" column="country" sort={sort} onSort={onSort} />
            <SortHeader label="Category" column="merchant_category" sort={sort} onSort={onSort} />
            <SortHeader label="Risk Score" column="risk_score" sort={sort} onSort={onSort} />
            <SortHeader label="Risk Level" column="risk_level" sort={sort} onSort={onSort} />
            <th><span className="sr-only">Actions</span></th>
          </tr>
        </thead>
        <tbody>
          {transactions.map((transaction) => (
            <tr key={transaction.transaction_id}>
              <td>
                <strong>{transaction.transaction_summary}</strong>
                <span>{transaction.customer_id}</span>
              </td>
              <td>${transaction.amount.toLocaleString()}</td>
              <td>{transaction.country}</td>
              <td>{transaction.merchant_category}</td>
              <td>{transaction.latest_prediction?.risk_score ?? "Not scored"}</td>
              <td>
                {transaction.latest_prediction ? (
                  <RiskBadge level={transaction.latest_prediction.risk_level} />
                ) : (
                  <span className="muted">Pending</span>
                )}
              </td>
              <td className="actions">
                <button
                  onClick={() => onPredict(transaction.transaction_id)}
                  disabled={disabled || predictingId === transaction.transaction_id}
                >
                  {predictingId === transaction.transaction_id ? "Scoring..." : "Score"}
                </button>
                <button className="secondary" disabled={disabled} onClick={() => onInvestigate(transaction.transaction_id)}>
                  Investigate
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
