const COLORS = {
  fraud: "#c24132",
  legitimate: "#2f855a",
  high: "#c24132",
  medium: "#d97706",
  low: "#2f855a",
};

function DonutChart({ fraud, legitimate }) {
  const total = fraud + legitimate;
  const fraudAngle = total ? Math.round((fraud / total) * 360) : 0;
  const background = total
    ? `conic-gradient(${COLORS.fraud} 0deg ${fraudAngle}deg, ${COLORS.legitimate} ${fraudAngle}deg 360deg)`
    : "#e7edf0";

  return (
    <section className="chart-card">
      <div>
        <p className="chart-label">Prediction Split</p>
        <h3>Fraud vs Legit</h3>
      </div>
      <div className="donut-layout">
        <div className="donut" style={{ background }}><span>{total}</span></div>
        <div className="chart-legend">
          <p><i className="legend-dot fraud" />Fraud <strong>{fraud}</strong></p>
          <p><i className="legend-dot legitimate" />Legitimate <strong>{legitimate}</strong></p>
        </div>
      </div>
    </section>
  );
}

function RiskBarChart({ distribution }) {
  const maximum = Math.max(...Object.values(distribution), 1);
  return (
    <section className="chart-card">
      <div>
        <p className="chart-label">Scored Transactions</p>
        <h3>Risk Distribution</h3>
      </div>
      <div className="bar-chart">
        {Object.entries(distribution).map(([level, count]) => (
          <div className="bar-row" key={level}>
            <span>{level}</span>
            <div className="bar-track"><i className={level} style={{ width: `${(count / maximum) * 100}%` }} /></div>
            <strong>{count}</strong>
          </div>
        ))}
      </div>
    </section>
  );
}

export default function RiskCharts({ transactions }) {
  const scored = transactions.filter((transaction) => transaction.latest_prediction);
  const fraud = scored.filter((transaction) => transaction.latest_prediction.prediction === "fraud").length;
  const legitimate = scored.length - fraud;
  const distribution = scored.reduce(
    (result, transaction) => {
      result[transaction.latest_prediction.risk_level] += 1;
      return result;
    },
    { low: 0, medium: 0, high: 0 }
  );

  return (
    <div className="chart-grid">
      <DonutChart fraud={fraud} legitimate={legitimate} />
      <RiskBarChart distribution={distribution} />
    </div>
  );
}
