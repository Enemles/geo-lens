import Link from "next/link";

import { ScoreCard } from "@/components/score-card";
import { api } from "@/lib/client";

// Fetched on the server (React Server Component) via the same typed client,
// fresh on every request.
export const dynamic = "force-dynamic";

export default async function HistoryPage() {
  const { data, error } = await api.GET("/api/analyses", {
    params: { query: { limit: 20 } },
  });

  return (
    <main className="mx-auto max-w-4xl px-6 py-12">
      <header className="mb-8">
        <Link
          href="/"
          className="text-sm font-medium text-teal-600 hover:underline"
        >
          ← New analysis
        </Link>
        <h1 className="font-display mt-2 text-3xl font-bold tracking-tight text-slate-900">
          Past analyses
        </h1>
      </header>

      {error && (
        <p className="text-sm text-rose-600">
          Couldn&apos;t reach the backend. Is it running on localhost:8000?
        </p>
      )}

      {data && data.length === 0 && (
        <p className="text-slate-500">No analyses yet — run one from the home page.</p>
      )}

      <div className="grid gap-4 sm:grid-cols-2">
        {data?.map((summary) => (
          <div key={summary.id} className="flex flex-col gap-2">
            <div className="flex items-baseline justify-between">
              <span className="font-medium text-slate-900">{summary.brand}</span>
              <span className="text-xs text-slate-400">
                {new Date(summary.created_at).toLocaleString()}
              </span>
            </div>
            <ScoreCard summary={summary} />
          </div>
        ))}
      </div>
    </main>
  );
}
