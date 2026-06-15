import { Card } from "@/components/ui/card";
import type { AnalysisResult, AnalysisSummary } from "@/lib/types";

function band(score: number): { label: string; tone: string } {
  if (score >= 70) return { label: "Strong visibility", tone: "text-teal-600" };
  if (score >= 40) return { label: "Moderate visibility", tone: "text-amber-600" };
  if (score > 0) return { label: "Low visibility", tone: "text-orange-600" };
  return { label: "Invisible to AI", tone: "text-rose-600" };
}

function pct(value: number): string {
  return `${Math.round(value * 100)}%`;
}

export function ScoreCard({ summary }: { summary: AnalysisResult | AnalysisSummary }) {
  const { label, tone } = band(summary.visibility_score);
  return (
    <Card className="flex flex-col gap-3">
      <div className="flex items-end justify-between">
        <div>
          <div className="text-xs uppercase tracking-wide text-slate-500">
            Visibility score
          </div>
          <div className="flex items-baseline gap-2">
            <span className="font-mono text-4xl font-bold text-slate-900">
              {summary.visibility_score.toFixed(1)}
            </span>
            <span className="text-sm text-slate-400">/ 100</span>
          </div>
        </div>
        <span className={`text-sm font-semibold ${tone}`}>{label}</span>
      </div>
      <div className="grid grid-cols-2 gap-3 border-t border-slate-100 pt-3 text-sm">
        <div>
          <div className="text-slate-500">Mention rate</div>
          <div className="font-medium text-slate-900">{pct(summary.mention_rate)}</div>
        </div>
        <div>
          <div className="text-slate-500">Recommendation rate</div>
          <div className="font-medium text-slate-900">
            {pct(summary.recommendation_rate)}
          </div>
        </div>
      </div>
    </Card>
  );
}
