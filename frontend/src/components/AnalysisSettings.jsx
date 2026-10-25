const PRESETS = ["08:00", "09:20", "10:30", "12:00", "15:30"];

export default function AnalysisSettings({
  value,
  activeCutoff,
  defaultCutoff,
  timezone,
  onChange,
  onApply,
  disabled,
}) {
  return (
    <section className="card card--settings" aria-labelledby="settings-heading">
      <div className="settings-head">
        <h2 id="settings-heading">Analysis settings</h2>
        <p className="settings-active">
          Active cutoff:{" "}
          <strong>
            {activeCutoff || "—"} {timezone || "Europe/London"}
          </strong>{" "}
          (day before delivery)
        </p>
      </div>
      <div className="settings-row">
        <label htmlFor="cutoff-input">Decision cutoff</label>
        <input
          id="cutoff-input"
          type="time"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          disabled={disabled}
        />
        <button type="button" className="btn btn-primary" onClick={onApply} disabled={disabled}>
          Recalculate
        </button>
      </div>
      <div className="settings-presets" role="group" aria-label="Cutoff presets">
        {PRESETS.map((preset) => (
          <button
            key={preset}
            type="button"
            className={`btn btn-ghost btn-sm ${value === preset ? "is-active" : ""}`}
            onClick={() => onChange(preset)}
            disabled={disabled}
          >
            {preset}
          </button>
        ))}
        {defaultCutoff && (
          <button
            type="button"
            className="btn btn-ghost btn-sm"
            onClick={() => onChange(defaultCutoff)}
            disabled={disabled}
          >
            Default ({defaultCutoff})
          </button>
        )}
      </div>
    </section>
  );
}
