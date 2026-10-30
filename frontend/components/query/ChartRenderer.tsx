"use client";

import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type { QueryResult } from "@/lib/types";

const COLORS = ["#4f46e5", "#06b6d4", "#f59e0b", "#ef4444", "#10b981", "#8b5cf6", "#ec4899"];

interface Props {
  result: QueryResult;
}

export function ChartRenderer({ result }: Props) {
  const spec = result.chart_spec;

  if (!spec || spec.chart_type === "table" || result.rows.length === 0) {
    return <DataTable columns={result.columns} rows={result.rows} />;
  }

  const { x_key, y_keys } = spec;

  if (spec.chart_type === "bar" && x_key) {
    return (
      <ResponsiveContainer width="100%" height={320}>
        <BarChart data={result.rows}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
          <XAxis dataKey={x_key} tick={{ fontSize: 12 }} />
          <YAxis tick={{ fontSize: 12 }} />
          <Tooltip contentStyle={{ fontSize: 12 }} />
          {y_keys.length > 1 && <Legend wrapperStyle={{ fontSize: 12 }} />}
          {y_keys.map((key, i) => (
            <Bar key={key} dataKey={key} fill={COLORS[i % COLORS.length]} radius={[4, 4, 0, 0]} />
          ))}
        </BarChart>
      </ResponsiveContainer>
    );
  }

  if (spec.chart_type === "line" && x_key) {
    return (
      <ResponsiveContainer width="100%" height={320}>
        <LineChart data={result.rows}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
          <XAxis dataKey={x_key} tick={{ fontSize: 12 }} />
          <YAxis tick={{ fontSize: 12 }} />
          <Tooltip contentStyle={{ fontSize: 12 }} />
          {y_keys.length > 1 && <Legend wrapperStyle={{ fontSize: 12 }} />}
          {y_keys.map((key, i) => (
            <Line
              key={key}
              type="monotone"
              dataKey={key}
              stroke={COLORS[i % COLORS.length]}
              strokeWidth={2}
              dot={false}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    );
  }

  if (spec.chart_type === "area" && x_key) {
    return (
      <ResponsiveContainer width="100%" height={320}>
        <AreaChart data={result.rows}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
          <XAxis dataKey={x_key} tick={{ fontSize: 12 }} />
          <YAxis tick={{ fontSize: 12 }} />
          <Tooltip contentStyle={{ fontSize: 12 }} />
          {y_keys.map((key, i) => (
            <Area
              key={key}
              type="monotone"
              dataKey={key}
              stroke={COLORS[i % COLORS.length]}
              fill={COLORS[i % COLORS.length]}
              fillOpacity={0.2}
            />
          ))}
        </AreaChart>
      </ResponsiveContainer>
    );
  }

  if (spec.chart_type === "pie" && x_key && y_keys[0]) {
    const valueKey = y_keys[0];
    return (
      <ResponsiveContainer width="100%" height={320}>
        <PieChart>
          <Tooltip contentStyle={{ fontSize: 12 }} />
          <Legend wrapperStyle={{ fontSize: 12 }} />
          <Pie
            data={result.rows}
            dataKey={valueKey}
            nameKey={x_key}
            cx="50%"
            cy="50%"
            outerRadius={110}
            label={(entry) => String(entry.name ?? "")}
          >
            {result.rows.map((_, i) => (
              <Cell key={i} fill={COLORS[i % COLORS.length]} />
            ))}
          </Pie>
        </PieChart>
      </ResponsiveContainer>
    );
  }

  return <DataTable columns={result.columns} rows={result.rows} />;
}

function DataTable({ columns, rows }: { columns: string[]; rows: Record<string, unknown>[] }) {
  if (rows.length === 0) {
    return <p className="p-4 text-sm text-muted-foreground">No rows returned.</p>;
  }
  return (
    <div className="max-h-96 overflow-auto rounded-md border border-border">
      <table className="w-full text-sm">
        <thead className="sticky top-0 bg-secondary text-left text-muted-foreground">
          <tr>
            {columns.map((col) => (
              <th key={col} className="p-2 px-3 font-medium">
                {col}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr key={i} className="border-t border-border">
              {columns.map((col) => (
                <td key={col} className="p-2 px-3">
                  {String(row[col] ?? "")}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
