import { useMemo, useState } from "react";
import { formatDeliveryLabel, formatMw } from "../utils/format.js";

const PAGE_SIZE = 25;

export default function PeriodTable({ series }) {
  const [query, setQuery] = useState("");
  const [sortKey, setSortKey] = useState("hour_start");
  const [sortDir, setSortDir] = useState("asc");
  const [page, setPage] = useState(1);

  const rows = useMemo(() => {
    let list = [...series];
    if (query.trim()) {
      const q = query.trim().toLowerCase();
      list = list.filter(
        (r) =>
          r.hour_start.toLowerCase().includes(q) ||
          r.settlement_date.includes(q),
      );
    }
    list.sort((a, b) => {
      const av = a[sortKey];
      const bv = b[sortKey];
      if (av < bv) return sortDir === "asc" ? -1 : 1;
      if (av > bv) return sortDir === "asc" ? 1 : -1;
      return 0;
    });
    return list;
  }, [series, query, sortKey, sortDir]);

  const totalPages = Math.max(1, Math.ceil(rows.length / PAGE_SIZE));
  const safePage = Math.min(page, totalPages);
  const pageRows = rows.slice((safePage - 1) * PAGE_SIZE, safePage * PAGE_SIZE);

  function toggleSort(key) {
    setPage(1);
    if (sortKey === key) setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    else {
      setSortKey(key);
      setSortDir("asc");
    }
  }

  return (
    <div className="table-block">
      <div className="table-toolbar">
        <label className="search-field">
          <span className="visually-hidden">Search by date or timestamp</span>
          <input
            type="search"
            placeholder="Search delivery time…"
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              setPage(1);
            }}
          />
        </label>
        <p className="table-meta">
          {rows.length.toLocaleString("en-GB")} rows · page {safePage} of {totalPages}
        </p>
      </div>
      <div className="table-scroll table-scroll--paged">
        <table>
          <thead>
            <tr>
              <th scope="col">
                <button type="button" className="th-btn" onClick={() => toggleSort("hour_start")}>
                  Delivery (UTC)
                </button>
              </th>
              <th scope="col">
                <button type="button" className="th-btn" onClick={() => toggleSort("forecast_mw")}>
                  Forecast (MW)
                </button>
              </th>
              <th scope="col">
                <button type="button" className="th-btn" onClick={() => toggleSort("actual_mw")}>
                  Actual (MW)
                </button>
              </th>
              <th scope="col">
                <button type="button" className="th-btn" onClick={() => toggleSort("forecast_error")}>
                  Error (MW)
                </button>
              </th>
            </tr>
          </thead>
          <tbody>
            {pageRows.map((row) => (
              <tr key={row.hour_start}>
                <td>{formatDeliveryLabel(row.hour_start)}</td>
                <td className="num">{formatMw(row.forecast_mw, 0)}</td>
                <td className="num">{formatMw(row.actual_mw, 0)}</td>
                <td className={`num ${row.forecast_error > 0 ? "pos" : row.forecast_error < 0 ? "neg" : ""}`}>
                  {formatMw(row.forecast_error, 0)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="table-pagination">
        <button
          type="button"
          className="btn btn-ghost btn-sm"
          disabled={safePage <= 1}
          onClick={() => setPage((p) => Math.max(1, p - 1))}
        >
          Previous
        </button>
        <button
          type="button"
          className="btn btn-ghost btn-sm"
          disabled={safePage >= totalPages}
          onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
        >
          Next
        </button>
      </div>
    </div>
  );
}
