export function LoadingBanner() {
  return (
    <div className="status-banner status-banner--loading" role="status" aria-live="polite">
      <div className="spinner" aria-hidden="true" />
      <div>
        <strong>Loading analysis</strong>
        <p>Fetching Elexon data via FastAPI — this may take a few seconds.</p>
      </div>
    </div>
  );
}

export function ErrorBanner({ message, onRetry }) {
  return (
    <div className="status-banner status-banner--error" role="alert">
      <div>
        <strong>Could not load data</strong>
        <p>{message}</p>
      </div>
      <button type="button" className="btn btn-primary" onClick={onRetry}>
        Retry
      </button>
    </div>
  );
}
