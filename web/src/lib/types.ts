import type { components } from "@/lib/api/schema";

// Single source of truth: every type is derived from the generated schema, so
// the frontend can never drift from the backend contract.
export type AnalyzeRequest = components["schemas"]["AnalyzeRequest"];
export type AnalysisResult = components["schemas"]["AnalysisResult"];
export type AnalysisSummary = components["schemas"]["AnalysisSummary"];
export type MentionResult = components["schemas"]["MentionResult"];

// The SSE endpoint streams binary, so it isn't a typed OpenAPI operation — but
// its payloads are composed from the generated component types above, so they
// still stay in sync with the backend.
export type ProgressEvent = {
  type: "progress";
  done: number;
  total: number;
  result: MentionResult;
};

export type SummaryEvent = {
  type: "summary";
  summary: AnalysisResult;
};
