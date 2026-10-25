import { formatSignedMw } from "../utils/format.js";

const NEAR_ZERO = 150;

export default function InsightBanner({ metrics, loading, error }) {
  if (loading) {
    return (
      <div className="insight-banner insight-banner--loading" role="status">
        <span className="insight-label">Key insight</span>
        <p>Analysing forecast accuracy for the selected cutoff…</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="insight-banner insight-banner--muted" role="status">
        <span className="insight-label">Key insight</span>
        <p>Insight unavailable until data loads successfully.</p>
      </div>
    );
  }

  const bias = metrics?.bias;
  if (bias === null || bias === undefined) {
    return (
      <div className="insight-banner insight-banner--muted" role="status">
        <span className="insight-label">Key insight</span>
        <p>No matched hours to summarise for this cutoff.</p>
      </div>
    );
  }

  let message;
  let tone = "neutral";
  if (bias > NEAR_ZERO) {
    tone = "positive";
    message = (
      <>
        Forecasts <strong>overestimated</strong> actual wind generation on average by{" "}
        <strong>{formatSignedMw(bias)}</strong> across matched delivery hours (forecast −
        actual).
      </>
    );
  } else if (bias < -NEAR_ZERO) {
    tone = "negative";
    message = (
      <>
        Forecasts <strong>underestimated</strong> actual wind generation on average by{" "}
        <strong>{formatSignedMw(bias)}</strong> across matched delivery hours (forecast −
        actual).
      </>
    );
  } else {
    message = (
      <>
        Average forecast bias was close to zero ({formatSignedMw(bias)}). Forecasts and
        actuals were broadly aligned on average for this cutoff.
      </>
    );
  }

  return (
    <div className={`insight-banner insight-banner--${tone}`} role="status">
      <span className="insight-label">Key insight</span>
      <p>{message}</p>
    </div>
  );
}
