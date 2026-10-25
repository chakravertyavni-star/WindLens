import { useEffect, useMemo, useState } from "react";
import CompactHeader from "./components/CompactHeader.jsx";
import Sidebar from "./components/Sidebar.jsx";
import { ErrorBanner, LoadingBanner } from "./components/StatusBanner.jsx";
import { useAnalysis } from "./hooks/useAnalysis.js";
import ForecastAnalysisPage from "./pages/ForecastAnalysisPage.jsx";
import MethodologyPage from "./pages/MethodologyPage.jsx";
import OverviewPage from "./pages/OverviewPage.jsx";
import "./App.css";

export default function App() {
  const [section, setSection] = useState("overview");
  const [appliedCutoff, setAppliedCutoff] = useState(null);
  const [draftCutoff, setDraftCutoff] = useState("09:20");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");

  const { config, metricsPayload, seriesPayload, loading, error, retry } =
    useAnalysis(appliedCutoff);

  useEffect(() => {
    if (config?.decision_cutoff_local_time && appliedCutoff === null) {
      setDraftCutoff(config.decision_cutoff_local_time);
    }
  }, [config, appliedCutoff]);

  const series = seriesPayload?.series ?? [];
  const metrics = metricsPayload?.metrics;
  const coverage = metricsPayload?.coverage;
  const cutoffUsed =
    metricsPayload?.cutoff_used ??
    seriesPayload?.cutoff_used ??
    config?.decision_cutoff_local_time;

  const settlementDates = useMemo(() => {
    const set = new Set(series.map((r) => r.settlement_date));
    return [...set].sort();
  }, [series]);

  const showEmpty =
    !loading && !error && series.length === 0 && metrics?.n === 0;

  function renderPage() {
    if (section === "forecast") {
      return (
        <ForecastAnalysisPage
          series={series}
          settlementDates={settlementDates}
          dateFrom={dateFrom}
          dateTo={dateTo}
          setDateFrom={setDateFrom}
          setDateTo={setDateTo}
        />
      );
    }
    if (section === "methodology") {
      return (
        <MethodologyPage cutoffUsed={cutoffUsed} timezone={config?.decision_cutoff_timezone} />
      );
    }
    return (
      <OverviewPage
        metrics={metrics}
        coverage={coverage}
        loading={loading}
        error={error}
        series={series}
        settlementDates={settlementDates}
        dateFrom={dateFrom}
        dateTo={dateTo}
        setDateFrom={setDateFrom}
        setDateTo={setDateTo}
        draftCutoff={draftCutoff}
        cutoffUsed={cutoffUsed}
        config={config}
        onCutoffChange={setDraftCutoff}
        onCutoffApply={() => setAppliedCutoff(draftCutoff)}
      />
    );
  }

  return (
    <div className="app-shell">
      <Sidebar active={section} onNavigate={setSection} />
      <div className="main-column">
        <CompactHeader />
        <main className="workspace">
          {loading && section !== "methodology" && <LoadingBanner />}
          {error && !loading && section !== "methodology" && (
            <ErrorBanner message={error} onRetry={retry} />
          )}
          {!error && showEmpty && section !== "methodology" && (
            <div className="empty-state" role="status">
              No matched delivery periods returned for this cutoff.
            </div>
          )}
          {section === "methodology" && renderPage()}
          {section !== "methodology" && (loading || (!error && !showEmpty)) && renderPage()}
        </main>
      </div>
    </div>
  );
}
