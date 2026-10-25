/**
 * HTTP client for the FastAPI backend. All dashboard data flows through here.
 */

export function apiBaseUrl() {
  return (import.meta.env.VITE_API_BASE_URL || "").replace(/\/$/, "");
}

function url(path, params = {}) {
  const baseUrl = apiBaseUrl();
  const search = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") {
      search.set(key, String(value));
    }
  });
  const qs = search.toString();
  return `${baseUrl}${path}${qs ? `?${qs}` : ""}`;
}

async function getJson(path, params) {
  const response = await fetch(url(path, params), {
    headers: { Accept: "application/json" },
  });
  if (!response.ok) {
    let detail = response.statusText;
    try {
      const body = await response.json();
      detail = body.detail ?? JSON.stringify(body);
    } catch {
      /* ignore */
    }
    throw new Error(`API ${response.status}: ${detail}`);
  }
  return response.json();
}

/** @returns {Promise<{ delivery_start: string, delivery_end: string, decision_cutoff_local_time: string, decision_cutoff_timezone: string }>} */
export function fetchConfig() {
  return getJson("/api/config");
}

/**
 * @param {{ cutoff?: string }} options
 * @returns {Promise<{ metrics: { n: number, mae: number|null, rmse: number|null, bias: number|null }, coverage: object, cutoff_used: string }>}
 */
export function fetchMetrics(options = {}) {
  return getJson("/api/metrics", { cutoff: options.cutoff });
}

/**
 * @param {{ cutoff?: string, limit?: number }} options
 * @returns {Promise<{ count: number, series: Array<object>, cutoff_used: string }>}
 */
export function fetchSeries(options = {}) {
  return getJson("/api/series", {
    cutoff: options.cutoff,
    limit: options.limit ?? 2000,
  });
}

export function fetchHealth() {
  return getJson("/api/health");
}
