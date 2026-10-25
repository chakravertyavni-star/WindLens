import DateRangeFilter from "../components/DateRangeFilter.jsx";
import ErrorChart from "../components/ErrorChart.jsx";
import PeriodTable from "../components/PeriodTable.jsx";

const FILTER_HINT =
  "Charts and table respect the date filter. Summary KPIs on Overview use the full matched sample.";

export default function ForecastAnalysisPage({
  series,
  settlementDates,
  dateFrom,
  dateTo,
  setDateFrom,
  setDateTo,
}) {
  return (
    <div className="page fade-in">
      <section className="card" aria-labelledby="explore-heading">
        <div className="card-head">
          <h2 id="explore-heading">Explore forecast errors</h2>
          <p className="card-lead">
            Hourly forecast minus actual (MW). Positive bars mean the forecast was higher than
            outturn.
          </p>
          <DateRangeFilter
            dateFrom={dateFrom}
            dateTo={dateTo}
            minDate={settlementDates[0]}
            maxDate={settlementDates[settlementDates.length - 1]}
            onFromChange={setDateFrom}
            onToChange={setDateTo}
            onClear={() => {
              setDateFrom("");
              setDateTo("");
            }}
            hint={FILTER_HINT}
          />
        </div>
        <ErrorChart data={series} dateFrom={dateFrom || null} dateTo={dateTo || null} />
      </section>

      <section className="card card--table" aria-labelledby="table-section-title">
        <h2 id="table-section-title" className="visually-hidden">
          Delivery period detail
        </h2>
        <PeriodTable series={series} />
      </section>
    </div>
  );
}
