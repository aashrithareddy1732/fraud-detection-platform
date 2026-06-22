export default function RiskBadge({ level = "unknown" }) {
  return <span className={`risk-badge ${level}`}>{level}</span>;
}

