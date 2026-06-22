export default function EmptyState({ title, description }) {
  return (
    <div className="empty-state-panel">
      <div className="empty-illustration" aria-hidden="true">
        <span />
        <span />
        <span />
      </div>
      <strong>{title}</strong>
      <p>{description}</p>
    </div>
  );
}
