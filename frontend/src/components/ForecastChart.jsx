import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { formatDeliveryLabel, formatMw } from "../utils/format.js";

function ChartTooltip({ active, payload }) {
  if (!active || !payload?.length) return null;
  const row = payload[0].payload;
  return (
    <div className="chart-tooltip">
      <p className="chart-tooltip-title">{formatDeliveryLabel(row.hour_start)} UTC</p>
      <p>
        <span className="dot dot--forecast" /> Forecast: {formatMw(row.forecast_mw, 0)}
      </p>
      <p>
        <span className="dot dot--actual" /> Actual: {formatMw(row.actual_mw, 0)}
      </p>
      <p>Error: {formatMw(row.forecast_error, 0)}</p>
    </div>
  );
}

export default function ForecastChart({ data, dateFrom, dateTo, tall }) {
  const filtered = data.filter((row) => {
    const day = row.settlement_date;
    if (dateFrom && day < dateFrom) return false;
    if (dateTo && day > dateTo) return false;
    return true;
  });

  if (!filtered.length) {
    return (
      <div className="empty-state" role="status">
        No series points for the selected date range.
      </div>
    );
  }

  const chartData = filtered.map((row) => ({
    ...row,
    label: formatDeliveryLabel(row.hour_start),
  }));

  const height = tall ? 420 : 380;

  return (
    <div className="chart-wrap chart-wrap--hero" style={{ minHeight: height }}>
      <ResponsiveContainer width="100%" height={height}>
        <LineChart data={chartData} margin={{ top: 12, right: 20, left: 4, bottom: 8 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--grid)" vertical={false} />
          <XAxis
            dataKey="label"
            tick={{ fontSize: 11, fill: "var(--text-muted)" }}
            interval="preserveStartEnd"
            minTickGap={28}
            tickLine={false}
          />
          <YAxis
            tick={{ fontSize: 11, fill: "var(--text-muted)" }}
            tickLine={false}
            axisLine={false}
            width={56}
            label={{
              value: "Generation (MW)",
              angle: -90,
              position: "insideLeft",
              fill: "var(--text-muted)",
              fontSize: 11,
              offset: 8,
            }}
          />
          <Tooltip content={<ChartTooltip />} />
          <Legend
            verticalAlign="top"
            align="right"
            iconType="line"
            wrapperStyle={{ fontSize: 12, paddingBottom: 8 }}
          />
          <Line
            type="monotone"
            dataKey="forecast_mw"
            name="Forecast"
            stroke="var(--line-forecast)"
            strokeWidth={2.5}
            dot={false}
            activeDot={{ r: 4 }}
            isAnimationActive={false}
          />
          <Line
            type="monotone"
            dataKey="actual_mw"
            name="Actual"
            stroke="var(--line-actual)"
            strokeWidth={2.5}
            dot={false}
            activeDot={{ r: 4 }}
            isAnimationActive={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
