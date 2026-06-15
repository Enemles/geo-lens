"""Streaming endpoint (Server-Sent Events).

The frontend wants progress as it happens, not a 30-second spinner. This streams
one SSE `progress` event per (prompt, model) as it completes, then a final
`summary` event — the same shaped data as POST /api/analyze, delivered live.

Consume from the browser with fetch + a streaming reader, or EventSource-style
tooling. Each event is: `event: <name>\\ndata: <json>\\n\\n`.
"""

from collections.abc import AsyncIterator

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from ..dependencies import get_analyzer
from ..schemas import (
    AnalysisResult,
    AnalyzeRequest,
    StreamDone,
    StreamProgress,
)
from ..services.analyzer import Analyzer

router = APIRouter(prefix="/api", tags=["analysis"])


def _sse(event: str, data: str) -> str:
    return f"event: {event}\ndata: {data}\n\n"


@router.post("/analyze/stream")
async def analyze_stream(
    req: AnalyzeRequest, analyzer: Analyzer = Depends(get_analyzer)
) -> StreamingResponse:
    async def events() -> AsyncIterator[str]:
        async for result, summary, done, total in analyzer.analyze_stream(req):
            if result is not None:
                payload = StreamProgress(done=done, total=total, result=result)
                yield _sse("progress", payload.model_dump_json())
            elif summary is not None:
                full = AnalysisResult(**summary.model_dump(), results=[])
                yield _sse("summary", StreamDone(summary=full).model_dump_json())

    return StreamingResponse(
        events(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
