"use client";

import { use } from "react";

import { ChartRenderer } from "@/components/query/ChartRenderer";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { useDashboard, useRemoveWidget } from "@/hooks/use-dashboards";

export default function DashboardDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const { data: dashboard, isLoading } = useDashboard(id);
  const removeWidget = useRemoveWidget(id);

  if (isLoading) return <div className="p-6 text-sm text-muted-foreground">Loading dashboard...</div>;
  if (!dashboard) return <div className="p-6 text-sm text-muted-foreground">Dashboard not found.</div>;

  return (
    <main className="h-full overflow-y-auto p-6">
      <h1 className="mb-4 text-xl font-semibold">{dashboard.name}</h1>

      {dashboard.widgets.length === 0 && (
        <p className="text-sm text-muted-foreground">
          No widgets pinned yet. Run a query on the Query page and use &ldquo;Pin to dashboard&rdquo;.
        </p>
      )}

      <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
        {dashboard.widgets.map((widget) => (
          <Card key={widget.id}>
            <CardContent className="p-4">
              <div className="mb-3 flex items-start justify-between gap-2">
                <div>
                  <h3 className="font-medium">{widget.query.chart_spec?.title ?? widget.query.question}</h3>
                  <p className="text-xs text-muted-foreground">{widget.query.question}</p>
                </div>
                <div className="flex shrink-0 items-center gap-2">
                  <Badge variant="outline">{widget.query.row_count} rows</Badge>
                  <Button variant="outline" size="sm" onClick={() => removeWidget.mutate(widget.id)}>
                    Remove
                  </Button>
                </div>
              </div>
              <ChartRenderer result={widget.query} />
            </CardContent>
          </Card>
        ))}
      </div>
    </main>
  );
}
