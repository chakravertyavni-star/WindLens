import { useCallback, useEffect, useRef, useState } from "react";
import { fetchConfig, fetchMetrics, fetchSeries } from "../api/windApi.js";

export function useAnalysis(cutoff) {
  const [config, setConfig] = useState(null);
  const [metricsPayload, setMetricsPayload] = useState(null);
  const [seriesPayload, setSeriesPayload] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const configRef = useRef(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      if (!configRef.current) {
        configRef.current = await fetchConfig();
        setConfig(configRef.current);
      }
      const params = cutoff ? { cutoff } : {};
      const [metrics, series] = await Promise.all([
        fetchMetrics(params),
        fetchSeries({ ...params, limit: 2000 }),
      ]);
      setMetricsPayload(metrics);
      setSeriesPayload(series);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
      setMetricsPayload(null);
      setSeriesPayload(null);
    } finally {
      setLoading(false);
    }
  }, [cutoff]);

  useEffect(() => {
    load();
  }, [load]);

  return { config, metricsPayload, seriesPayload, loading, error, retry: load };
}
