export default function MethodologyPage({ cutoffUsed, timezone }) {
  return (
    <article className="page page--methodology fade-in">
      <section className="card">
        <h2>Data sources</h2>
        <p>
          National UK wind data comes from Elexon Insights: <strong>WINDFOR</strong> (wind
          generation forecasts) and <strong>FUELHH</strong> filtered to fuel type{" "}
          <strong>WIND</strong> (half-hourly actual outturn). This application analyses{" "}
          <strong>historical January 2026</strong> delivery periods only. It does not place trades
          or calculate a utility&apos;s full procurement requirement.
        </p>
      </section>

      <section className="card">
        <h2>Forecast selection</h2>
        <p>
          For each hourly delivery period, WindLens selects the{" "}
          <strong>latest WINDFOR publish on or before the configured decision cutoff</strong> on
          the calendar day before the UK settlement date. The active cutoff in your session is{" "}
          <strong>
            {cutoffUsed || "—"} {timezone || "Europe/London"}
          </strong>
          . The default <strong>09:20 Europe/London</strong> day-before time is an{" "}
          <strong>analytical assumption</strong>, not a verified official market gate closure.
        </p>
      </section>

      <section className="card">
        <h2>Matching and metrics</h2>
        <ul className="method-list">
          <li>
            Forecasts are hourly; actuals are aggregated from two half-hour FUELHH periods into an
            hourly average when both halves are present.
          </li>
          <li>
            <strong>Forecast error = forecast − actual</strong> (MW).{" "}
            <strong>Positive bias</strong> means forecasts tended to{" "}
            <strong>overestimate</strong> wind; negative bias means{" "}
            <strong>underestimate</strong>.
          </li>
          <li>
            <strong>MAE</strong> — average absolute error. <strong>RMSE</strong> — penalises large
            errors more. Metrics use only valid matched pairs; missing actuals are not treated as
            zero.
          </li>
        </ul>
      </section>

      <section className="card">
        <h2>Limitations</h2>
        <ul className="method-list">
          <li>
            The API returns the <strong>selected as-of forecast</strong> for each hour (
            <code>publish_time</code> on each series row), not the full publication history needed
            for a complete forecast-evolution chart.
          </li>
          <li>
            Date filters on charts and tables change the <strong>view</strong> only; headline KPIs
            on Overview reflect the full matched sample for the chosen cutoff.
          </li>
          <li>
            Scope is national wind only — no demand, prices, or other fuels in these accuracy
            metrics.
          </li>
        </ul>
      </section>
    </article>
  );
}
