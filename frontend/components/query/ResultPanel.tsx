"use client";

import { useState } from "react";

import type { QueryResult } from "@/lib/types";
import { ChartRenderer } from "@/components/query/ChartRenderer";
import { PinToDashboardMenu } from "@/components/query/PinToDashboardMenu";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";

export function ResultPanel({ result }: { result: QueryResult }) {
  const [showSql, setShowSql] = useState(true);

  if (result.status === "error") {
    return (
      <Card className="p-4">
        <p className="text-sm font-medium text-destructive">Query failed</p>
        <p className="mt-1 text-sm text-muted-foreground">{result.error_message}</p>
      </Card>
    );
  }

  return (
    <div className="flex flex-col gap-4">
      <Card>
        <CardContent className="p-4">
          <div className="mb-2 flex items-center justify-between">
            <button
              onClick={() => setShowSql((v) => !v)}
              className="text-xs font-medium text-muted-foreground hover:text-foreground"
            >
              {showSql ? "Hide" : "Show"} generated SQL
            </button>
            <Badge variant="outline">{result.row_count} rows</Badge>
          </div>
          {showSql && (
            <pre className="overflow-x-auto rounded-md bg-secondary p-3 text-xs">
              <code>{result.sql}</code>
            </pre>
          )}
          {result.explanation && <p className="mt-2 text-sm text-muted-foreground">{result.explanation}</p>}
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-4">
          <div className="mb-3 flex items-center justify-between">
            <h3 className="font-medium">{result.chart_spec?.title ?? "Result"}</h3>
            <PinToDashboardMenu savedQueryId={result.id} />
          </div>
          <ChartRenderer result={result} />
          {result.chart_spec?.insight && (
            <p className="mt-3 border-t border-border pt-3 text-sm text-muted-foreground">
              {result.chart_spec.insight}
            </p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
