"use client";

import { useState } from "react";

import { useCreateDashboard, useDashboards } from "@/hooks/use-dashboards";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { api } from "@/lib/api-client";

interface Props {
  savedQueryId: string;
}

export function PinToDashboardMenu({ savedQueryId }: Props) {
  const [open, setOpen] = useState(false);
  const [newName, setNewName] = useState("");
  const [status, setStatus] = useState<string | null>(null);
  const { data: dashboards } = useDashboards();
  const createDashboard = useCreateDashboard();

  async function pinTo(dashboardId: string) {
    await api.post(`/api/dashboards/${dashboardId}/widgets`, { saved_query_id: savedQueryId });
    setStatus("Pinned!");
    setTimeout(() => setStatus(null), 2000);
    setOpen(false);
  }

  async function handleCreateAndPin() {
    if (!newName.trim()) return;
    const dashboard = await createDashboard.mutateAsync(newName.trim());
    setNewName("");
    await pinTo(dashboard.id);
  }

  return (
    <div className="relative inline-block">
      <Button variant="outline" size="sm" onClick={() => setOpen((v) => !v)}>
        {status ?? "Pin to dashboard"}
      </Button>
      {open && (
        <div className="absolute right-0 z-10 mt-2 w-64 rounded-md border border-border bg-card p-2 shadow-lg">
          {dashboards?.map((d) => (
            <button
              key={d.id}
              onClick={() => pinTo(d.id)}
              className="block w-full rounded-md px-2 py-1.5 text-left text-sm hover:bg-accent"
            >
              {d.name}
            </button>
          ))}
          {dashboards?.length === 0 && (
            <p className="px-2 py-1 text-xs text-muted-foreground">No dashboards yet.</p>
          )}
          <div className="mt-2 flex gap-1 border-t border-border pt-2">
            <Input
              placeholder="New dashboard name"
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              className="h-8 text-xs"
            />
            <Button size="sm" onClick={handleCreateAndPin} disabled={!newName.trim()}>
              Add
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
