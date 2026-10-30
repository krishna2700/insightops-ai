"use client";

import { useDeleteQuery, useQueryHistory } from "@/hooks/use-query-engine";
import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";

interface Props {
  selectedId: string | null;
  onSelect: (id: string) => void;
}

export function HistorySidebar({ selectedId, onSelect }: Props) {
  const { data: history, isLoading } = useQueryHistory();
  const deleteMutation = useDeleteQuery();

  return (
    <div className="flex h-full w-72 flex-col border-r border-border">
      <div className="border-b border-border p-3">
        <p className="text-sm font-semibold">Query history</p>
      </div>
      <div className="flex-1 overflow-y-auto px-2 py-2">
        {isLoading && <p className="p-2 text-sm text-muted-foreground">Loading...</p>}
        {history?.map((item) => (
          <div
            key={item.id}
            onClick={() => onSelect(item.id)}
            className={cn(
              "group mb-1 cursor-pointer rounded-md px-2 py-2 text-sm hover:bg-accent",
              selectedId === item.id && "bg-accent"
            )}
          >
            <div className="flex items-start justify-between gap-2">
              <p className="line-clamp-2 flex-1">{item.question}</p>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  deleteMutation.mutate(item.id);
                  if (selectedId === item.id) onSelect("");
                }}
                className="hidden shrink-0 text-xs text-destructive underline group-hover:inline"
              >
                delete
              </button>
            </div>
            <div className="mt-1 flex items-center gap-2">
              {item.status === "error" ? (
                <Badge variant="destructive">error</Badge>
              ) : (
                <Badge variant="outline">{item.row_count} rows</Badge>
              )}
            </div>
          </div>
        ))}
        {history?.length === 0 && (
          <p className="p-2 text-sm text-muted-foreground">No queries yet. Ask something!</p>
        )}
      </div>
    </div>
  );
}
