export default function DateRangeFilter({
  dateFrom,
  dateTo,
  minDate,
  maxDate,
  onFromChange,
  onToChange,
  onClear,
  hint,
}) {
  return (
    <div className="date-range">
      {hint ? <p className="date-range-hint">{hint}</p> : null}
      <div className="date-range-controls">
        <label>
          From
          <input
            type="date"
            value={dateFrom}
            min={minDate}
            max={maxDate}
            onChange={(e) => onFromChange(e.target.value)}
          />
        </label>
        <label>
          To
          <input
            type="date"
            value={dateTo}
            min={minDate}
            max={maxDate}
            onChange={(e) => onToChange(e.target.value)}
          />
        </label>
        <button type="button" className="btn btn-ghost btn-sm" onClick={onClear}>
          Clear
        </button>
      </div>
    </div>
  );
}
