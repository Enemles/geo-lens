import { Badge } from "@/components/ui/badge";
import type { MentionResult } from "@/lib/types";

export function ResultsTable({ results }: { results: MentionResult[] }) {
  if (results.length === 0) return null;
  return (
    <div className="overflow-hidden rounded-xl border border-slate-200">
      <table className="w-full text-sm">
        <thead className="bg-slate-50 text-left text-xs uppercase tracking-wide text-slate-500">
          <tr>
            <th className="px-4 py-2 font-medium">Query</th>
            <th className="px-4 py-2 font-medium">Model</th>
            <th className="px-4 py-2 font-medium">Result</th>
            <th className="px-4 py-2 text-right font-medium">Score</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {results.map((r, i) => (
            <tr key={i} className="align-top">
              <td className="max-w-md px-4 py-3 text-slate-700">{r.prompt}</td>
              <td className="px-4 py-3">
                <Badge>{r.model}</Badge>
              </td>
              <td className="px-4 py-3">
                <div className="flex flex-wrap gap-1.5">
                  {r.mentioned ? (
                    <Badge tone="positive">mentioned</Badge>
                  ) : (
                    <Badge tone="muted">not mentioned</Badge>
                  )}
                  {r.recommended && <Badge tone="positive">recommended</Badge>}
                  {r.rank != null && <Badge>rank #{r.rank}</Badge>}
                </div>
              </td>
              <td className="px-4 py-3 text-right font-mono text-slate-900">
                {r.score.toFixed(2)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
