import { useAnimatedNumber } from "../hooks/useAnimatedNumber.js";
import { formatCoveragePct } from "../utils/format.js";

const TIPS = {
  mae: "Average size of forecast mistakes in MW, ignoring direction.",
  bias: "Mean forecast − actual. Positive means overestimation.",
  rmse: "Like MAE, but large errors count more (MW).",
  coverage: "Matched hourly periods with complete actual data.",
};

function KpiCard({ label, display, tip, tone, animate, unit = "MW" }) {
  const animated = useAnimatedNumber(typeof animate === "number" ? animate : null);
  const shown =
    typeof animate === "number"
      ? `${Math.round(animated).toLocaleString("en-GB")} ${unit}`
      : display;

  return (
    <article
      className={`kpi-card ${tone ? `kpi-card--${tone}` : ""}`}
      title={tip}
    >
      <h3>{label}</h3>
      <p className="kpi-value">{shown}</p>
      {tip ? <p className="kpi-tip">{tip}</p> : null}
    </article>
  );
}

export default function KpiGrid({ metrics, coverage, loading }) {
  if (loading || !metrics || !coverage) {
    return (
      <section className="kpi-row" aria-label="Accuracy metrics" aria-busy="true">
        {[1, 2, 3, 4].map((i) => (
          <article key={i} className="kpi-card kpi-card--skeleton">
            <div className="skeleton-line" />
            <div className="skeleton-line skeleton-line--lg" />
          </article>
        ))}
      </section>
    );
  }

  const matched = coverage.matched_hourly_pairs ?? 0;
  const hourlyActuals = coverage.hourly_actuals_with_both_half_hours ?? 0;
  const bias = metrics.bias;
  const biasTone =
    bias === null || bias === undefined
      ? undefined
      : bias > 0
        ? "warn"
        : bias < 0
          ? "cool"
          : undefined;

  const biasDisplay =
    bias === null || bias === undefined
      ? "—"
      : `${bias > 0 ? "+" : ""}${Math.round(bias).toLocaleString("en-GB")} MW`;

  return (
    <section className="kpi-row" aria-label="Accuracy metrics">
      <KpiCard
        label="Mean Absolute Error"
        display={`${Math.round(metrics.mae ?? 0).toLocaleString("en-GB")} MW`}
        animate={metrics.mae ?? undefined}
        unit="MW"
        tip={TIPS.mae}
      />
      <KpiCard
        label="Forecast Bias"
        display={biasDisplay}
        tip={TIPS.bias}
        tone={biasTone}
      />
      <KpiCard
        label="Root Mean Squared Error"
        display={`${Math.round(metrics.rmse ?? 0).toLocaleString("en-GB")} MW`}
        animate={metrics.rmse ?? undefined}
        unit="MW"
        tip={TIPS.rmse}
      />
      <KpiCard
        label="Matched Hours / Coverage"
        display={`${matched.toLocaleString("en-GB")} · ${formatCoveragePct(matched, hourlyActuals)}`}
        tip={TIPS.coverage}
      />
    </section>
  );
}
