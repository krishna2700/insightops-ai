export interface User {
  id: string;
  email: string;
  full_name: string | null;
}

export type ChartType = "bar" | "line" | "pie" | "area" | "table";

export interface ChartSpec {
  chart_type: ChartType;
  title: string;
  x_key: string | null;
  y_keys: string[];
  insight: string;
}

export interface QueryResult {
  id: string;
  question: string;
  sql: string;
  explanation: string | null;
  columns: string[];
  rows: Record<string, unknown>[];
  row_count: number;
  chart_spec: ChartSpec | null;
  status: "success" | "error";
  error_message: string | null;
  created_at: string;
}

export interface SavedQuerySummary {
  id: string;
  question: string;
  sql: string;
  status: string;
  row_count: number;
  created_at: string;
}

export interface TableColumn {
  name: string;
  type: string;
  nullable: boolean;
}

export interface TableSchema {
  table: string;
  columns: TableColumn[];
  foreign_keys: { columns: string[]; references_table: string; references_columns: string[] }[];
}

export interface DashboardSummary {
  id: string;
  name: string;
  created_at: string;
}

export interface DashboardWidget {
  id: string;
  position: number;
  query: QueryResult;
}

export interface DashboardDetail extends DashboardSummary {
  widgets: DashboardWidget[];
}
