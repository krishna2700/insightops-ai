"use client";

import { useState } from "react";

import { HistorySidebar } from "@/components/query/HistorySidebar";
import { ResultPanel } from "@/components/query/ResultPanel";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { useRerunQuery, useRunQuery } from "@/hooks/use-query-engine";
import type { QueryResult } from "@/lib/types";

const EXAMPLE_QUESTIONS = [
  "What was total revenue by month for the last 12 months?",
  "Who are the top 10 customers by total spend?",
  "What's the average order value by customer segment?",
  "Which product categories have the highest revenue?",
  "How many orders were refunded or cancelled, by month?",
];

export default function QueryPage() {
  const [question, setQuestion] = useState("");
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [result, setResult] = useState<QueryResult | null>(null);

  const runQuery = useRunQuery();
  const rerunQuery = useRerunQuery();

  async function handleAsk(q?: string) {
    const text = (q ?? question).trim();
    if (!text || runQuery.isPending) return;
    setQuestion("");
    try {
      const response = await runQuery.mutateAsync(text);
      setResult(response);
      setSelectedId(response.id);
    } catch {
      // error surfaced via runQuery.error below
    }
  }

  async function handleSelectHistory(id: string) {
    if (!id) {
      setSelectedId(null);
      setResult(null);
      return;
    }
    setSelectedId(id);
    try {
      const response = await rerunQuery.mutateAsync(id);
      setResult(response);
    } catch {
      // ignore -- rerunQuery.error not surfaced for history clicks to keep it lightweight
    }
  }

  return (
    <div className="flex h-full">
      <HistorySidebar selectedId={selectedId} onSelect={handleSelectHistory} />

      <main className="flex flex-1 flex-col overflow-y-auto p-6">
        <h1 className="mb-1 text-xl font-semibold">Ask your data</h1>
        <p className="mb-4 text-sm text-muted-foreground">
          Plain English in, live PostgreSQL + a chart out. Every query runs through an automatic
          safety validator and a read-only database role before it ever touches real data.
        </p>

        <div className="mb-3 flex flex-wrap gap-2">
          {EXAMPLE_QUESTIONS.map((q) => (
            <button
              key={q}
              onClick={() => handleAsk(q)}
              className="rounded-full border border-border px-3 py-1 text-xs text-muted-foreground hover:bg-accent hover:text-accent-foreground"
            >
              {q}
            </button>
          ))}
        </div>

        <div className="mb-6 flex gap-2">
          <Textarea
            placeholder="e.g. What were our top 5 products by revenue last quarter?"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                handleAsk();
              }
            }}
          />
          <Button onClick={() => handleAsk()} disabled={!question.trim() || runQuery.isPending}>
            {runQuery.isPending ? "Thinking..." : "Ask"}
          </Button>
        </div>

        {runQuery.isError && (
          <p className="mb-4 text-sm text-destructive">
            {(runQuery.error as Error)?.message ?? "Something went wrong."}
          </p>
        )}

        {result ? (
          <ResultPanel result={result} />
        ) : (
          <p className="text-sm text-muted-foreground">
            Ask a question above, or try one of the examples.
          </p>
        )}
      </main>
    </div>
  );
}
