"use client";

import { useState } from "react";

import { ResultsTable } from "@/components/results-table";
import { ScoreCard } from "@/components/score-card";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Progress } from "@/components/ui/progress";
import { useAnalysisStream } from "@/lib/use-analysis-stream";

export function AnalyzePanel() {
  const [brand, setBrand] = useState("Yolando");
  const [domain, setDomain] = useState("yolando.ai");
  const [category, setCategory] = useState("AI brand-visibility tools");
  const { status, results, progress, summary, error, run } = useAnalysisStream();

  const onSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!brand.trim()) return;
    run({
      brand: brand.trim(),
      domain: domain.trim() || null,
      category: category.trim() || null,
    });
  };

  const streaming = status === "streaming";
  const pct = progress.total ? (progress.done / progress.total) * 100 : 0;

  return (
    <div className="flex flex-col gap-6">
      <Card>
        <form onSubmit={onSubmit} className="flex flex-col gap-4">
          <div className="grid gap-4 sm:grid-cols-3">
            <div>
              <Label htmlFor="brand">Brand</Label>
              <Input
                id="brand"
                value={brand}
                onChange={(e) => setBrand(e.target.value)}
                placeholder="Acme"
                required
              />
            </div>
            <div>
              <Label htmlFor="domain">Domain (optional)</Label>
              <Input
                id="domain"
                value={domain}
                onChange={(e) => setDomain(e.target.value)}
                placeholder="acme.com"
              />
            </div>
            <div>
              <Label htmlFor="category">Category (optional)</Label>
              <Input
                id="category"
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                placeholder="project management tools"
              />
            </div>
          </div>
          <div className="flex items-center gap-3">
            <Button type="submit" disabled={streaming}>
              {streaming ? "Analyzing…" : "Analyze visibility"}
            </Button>
            {streaming && (
              <span className="text-sm text-slate-500">
                {progress.done} / {progress.total} queries
              </span>
            )}
          </div>
        </form>
      </Card>

      {error && (
        <Card className="border-rose-200 bg-rose-50 text-sm text-rose-700">
          {error} — is the backend running on{" "}
          <code className="font-mono">localhost:8000</code>?
        </Card>
      )}

      {(streaming || results.length > 0) && (
        <div className="flex flex-col gap-4">
          {streaming && <Progress value={pct} />}
          {summary && <ScoreCard summary={summary} />}
          <ResultsTable results={results} />
        </div>
      )}
    </div>
  );
}
