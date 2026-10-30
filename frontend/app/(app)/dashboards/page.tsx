"use client";

import { useState } from "react";
import Link from "next/link";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { useCreateDashboard, useDashboards, useDeleteDashboard } from "@/hooks/use-dashboards";

export default function DashboardsPage() {
  const { data: dashboards, isLoading } = useDashboards();
  const createDashboard = useCreateDashboard();
  const deleteDashboard = useDeleteDashboard();
  const [name, setName] = useState("");

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    if (!name.trim()) return;
    await createDashboard.mutateAsync(name.trim());
    setName("");
  }

  return (
    <main className="h-full overflow-y-auto p-6">
      <h1 className="mb-1 text-xl font-semibold">Dashboards</h1>
      <p className="mb-4 text-sm text-muted-foreground">
        Pin query results from the Query page to build a live dashboard -- widgets re-run their SQL
        every time you open it, so the numbers are never stale.
      </p>

      <form onSubmit={handleCreate} className="mb-6 flex max-w-md gap-2">
        <Input placeholder="New dashboard name" value={name} onChange={(e) => setName(e.target.value)} />
        <Button type="submit" disabled={!name.trim() || createDashboard.isPending}>
          Create
        </Button>
      </form>

      {isLoading && <p className="text-sm text-muted-foreground">Loading...</p>}

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {dashboards?.map((d) => (
          <Card key={d.id}>
            <CardContent className="flex items-center justify-between p-4">
              <Link href={`/dashboards/${d.id}`} className="font-medium hover:underline">
                {d.name}
              </Link>
              <Button
                variant="outline"
                size="sm"
                onClick={() => deleteDashboard.mutate(d.id)}
                disabled={deleteDashboard.isPending}
              >
                Delete
              </Button>
            </CardContent>
          </Card>
        ))}
      </div>
      {dashboards?.length === 0 && (
        <p className="text-sm text-muted-foreground">
          No dashboards yet. Create one above, then pin results to it from the Query page.
        </p>
      )}
    </main>
  );
}
