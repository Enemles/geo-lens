import Link from "next/link";

import { AnalyzePanel } from "@/components/analyze-panel";

export default function Home() {
  return (
    <main className="mx-auto max-w-4xl px-6 py-12">
      <header className="mb-8">
        <div className="mb-2 h-1 w-16 rounded bg-gradient-to-r from-teal-500 to-violet-500" />
        <h1 className="font-display text-3xl font-bold tracking-tight text-slate-900">
          GEO Lens
        </h1>
        <p className="mt-2 max-w-2xl text-slate-600">
          Measure how visible a brand is to AI assistants. We ask several models
          realistic buyer-intent questions and score whether your brand gets
          mentioned, recommended, and ranked — streamed live as each query lands.
        </p>
        <Link
          href="/history"
          className="mt-3 inline-block text-sm font-medium text-teal-600 hover:underline"
        >
          View past analyses →
        </Link>
      </header>

      <AnalyzePanel />
    </main>
  );
}
