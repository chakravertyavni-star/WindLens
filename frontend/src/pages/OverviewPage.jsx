import AnalysisSettings from "../components/AnalysisSettings.jsx";
import DateRangeFilter from "../components/DateRangeFilter.jsx";
import ForecastChart from "../components/ForecastChart.jsx";
import InsightBanner from "../components/InsightBanner.jsx";
import KpiGrid from "../components/KpiGrid.jsx";

const FILTER_HINT =
  "Date filter applies to the chart below only. Headline metrics use all matched hours for the selected cutoff.";

export default function OverviewPage({
  metrics,
  coverage,
  loading,
  error,
  series,
  settlementDates,
  dateFrom,
  dateTo,
  setDateFrom,
  setDateTo,
  draftCutoff,
  cutoffUsed,
  config,
  onCutoffChange,
  onCutoffApply,
}) {
  return (
    <div className="page page--overview fade-in">
      <InsightBanner metrics={metrics} loading={loading} error={error} />

      <KpiGrid metrics={metrics} coverage={coverage} loading={loading} />

      <div className="overview-grid">
        <section className="card card--chart" aria-labelledby="main-chart-title">
          <div className="card-head card-head--split">
            <div>
              <h2 id="main-chart-title">Forecast vs actual generation</h2>
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
          </div>
          <ForecastChart
            data={series}
            dateFrom={dateFrom || null}
            dateTo={dateTo || null}
            tall
          />
        </section>

        <AnalysisSettings
          value={draftCutoff}
          activeCutoff={cutoffUsed}
          defaultCutoff={config?.decision_cutoff_local_time}
          timezone={config?.decision_cutoff_timezone}
          onChange={onCutoffChange}
          onApply={onCutoffApply}
          disabled={loading}
        />
      </div>
    </div>
  );
}
