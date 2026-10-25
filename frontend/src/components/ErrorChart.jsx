import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { formatDeliveryLabel, formatMw } from "../utils/format.js";

export default function ErrorChart({ data, dateFrom, dateTo }) {
  const filtered = data.filter((row) => {
    const day = row.settlement_date;
    if (dateFrom && day < dateFrom) return false;
    if (dateTo && day > dateTo) return false;
    return true;
  });

  if (!filtered.length) {
    return (
      <div className="empty-state empty-state--compact" role="status">
        No error data for the selected range.
      </div>
    );
  }

  const chartData = filtered.map((row) => ({
    ...row,
    label: formatDeliveryLabel(row.hour_start),
  }));

  return (
    <div className="chart-wrap chart-wrap--error">
      <ResponsiveContainer width="100%" height={240}>
        <BarChart data={chartData} margin={{ top: 8, right: 12, left: 4, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--grid)" vertical={false} />
          <XAxis dataKey="label" hide />
          <YAxis
            tick={{ fontSize: 10, fill: "var(--text-muted)" }}
            tickLine={false}
            axisLine={false}
            width={48}
          />
          <Tooltip
            formatter={(v) => formatMw(v, 0)}
            labelFormatter={(_, items) =>
              items?.[0]?.payload?.hour_start
                ? formatDeliveryLabel(items[0].payload.hour_start)
                : ""
            }
          />
          <ReferenceLine y={0} stroke="var(--navy)" strokeWidth={1.5} />
          <Bar dataKey="forecast_error" name="Forecast − actual" isAnimationActive={false}>
            {chartData.map((entry) => (
              <Cell
                key={entry.hour_start}
                fill={entry.forecast_error >= 0 ? "var(--amber)" : "var(--teal-deep)"}
                fillOpacity={0.85}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
