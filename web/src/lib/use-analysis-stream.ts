"use client";

import { useCallback, useRef, useState } from "react";

import { apiBaseUrl } from "@/lib/client";
import type {
  AnalysisResult,
  AnalyzeRequest,
  MentionResult,
  ProgressEvent,
  SummaryEvent,
} from "@/lib/types";

export type StreamStatus = "idle" | "streaming" | "done" | "error";

/**
 * Drives the SSE endpoint: POSTs the request, reads the event-stream, and
 * surfaces results incrementally so the UI fills in live instead of blocking
 * on the full analysis.
 */
export function useAnalysisStream() {
  const [status, setStatus] = useState<StreamStatus>("idle");
  const [results, setResults] = useState<MentionResult[]>([]);
  const [progress, setProgress] = useState({ done: 0, total: 0 });
  const [summary, setSummary] = useState<AnalysisResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  const run = useCallback(async (req: AnalyzeRequest) => {
    abortRef.current?.abort();
    const ctrl = new AbortController();
    abortRef.current = ctrl;

    setStatus("streaming");
    setResults([]);
    setSummary(null);
    setError(null);
    setProgress({ done: 0, total: 0 });

    const handleFrame = (frame: string) => {
      let event = "message";
      let data = "";
      for (const line of frame.split("\n")) {
        if (line.startsWith("event:")) event = line.slice(6).trim();
        else if (line.startsWith("data:")) data += line.slice(5).trim();
      }
      if (!data) return;

      if (event === "progress") {
        const payload = JSON.parse(data) as ProgressEvent;
        setResults((prev) => [...prev, payload.result]);
        setProgress({ done: payload.done, total: payload.total });
      } else if (event === "summary") {
        const payload = JSON.parse(data) as SummaryEvent;
        setSummary(payload.summary);
      }
    };

    try {
      const res = await fetch(`${apiBaseUrl}/api/analyze/stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(req),
        signal: ctrl.signal,
      });
      if (!res.ok || !res.body) {
        throw new Error(`Request failed (${res.status})`);
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      // SSE frames are separated by a blank line.
      for (;;) {
        const { value, done } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        let sep: number;
        while ((sep = buffer.indexOf("\n\n")) !== -1) {
          handleFrame(buffer.slice(0, sep));
          buffer = buffer.slice(sep + 2);
        }
      }
      setStatus("done");
    } catch (err) {
      if ((err as Error).name === "AbortError") return;
      setError((err as Error).message);
      setStatus("error");
    }
  }, []);

  return { status, results, progress, summary, error, run };
}
