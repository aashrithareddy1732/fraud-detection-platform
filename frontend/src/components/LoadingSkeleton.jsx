export default function LoadingSkeleton({ rows = 4 }) {
  return (
    <div className="skeleton-stack" aria-label="Loading content" aria-busy="true">
      {Array.from({ length: rows }, (_, index) => (
        <div className="skeleton-row" key={index}>
          <span />
          <span />
          <span />
          <span />
        </div>
      ))}
    </div>
  );
}
