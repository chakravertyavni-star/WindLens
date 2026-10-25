/** @param {number|null|undefined} value */
export function formatMw(value, digits = 0) {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return "—";
  }
  return `${value.toLocaleString("en-GB", {
    maximumFractionDigits: digits,
    minimumFractionDigits: digits,
  })} MW`;
}

/** @param {number|null|undefined} value */
export function formatSignedMw(value) {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return "—";
  }
  const sign = value > 0 ? "+" : "";
  return `${sign}${value.toLocaleString("en-GB", { maximumFractionDigits: 0 })} MW`;
}

/** @param {string} isoUtc */
export function formatDeliveryLabel(isoUtc) {
  const d = new Date(isoUtc);
  return d.toLocaleString("en-GB", {
    timeZone: "UTC",
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  });
}

/** @param {number} matched @param {number} total */
export function formatCoveragePct(matched, total) {
  if (!total) return "—";
  return `${((matched / total) * 100).toFixed(1)}%`;
}
