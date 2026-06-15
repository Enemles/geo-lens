"""Analysis endpoints: run an analysis and read history."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select

from ..database import get_session
from ..dependencies import get_analyzer
from ..models import Analysis, Mention
from ..schemas import AnalysisResult, AnalysisSummary, AnalyzeRequest, MentionResult
from ..services.analyzer import Analyzer

router = APIRouter(prefix="/api", tags=["analysis"])


def _persist(session: Session, summary: AnalysisSummary, results: list[MentionResult]) -> Analysis:
    row = Analysis(
        brand=summary.brand,
        domain=summary.domain,
        category=summary.category,
        visibility_score=summary.visibility_score,
        mention_rate=summary.mention_rate,
        recommendation_rate=summary.recommendation_rate,
        mentions=[Mention(**r.model_dump()) for r in results],
    )
    session.add(row)
    session.commit()
    session.refresh(row)
    return row


@router.post("/analyze", response_model=AnalysisResult)
async def analyze(
    req: AnalyzeRequest,
    analyzer: Analyzer = Depends(get_analyzer),
    session: Session = Depends(get_session),
) -> AnalysisResult:
    summary, results = await analyzer.analyze(req)
    row = _persist(session, summary, results)
    return AnalysisResult(
        **summary.model_dump(exclude={"id"}), id=row.id, results=results
    )


@router.get("/analyses", response_model=list[AnalysisSummary])
def list_analyses(
    session: Session = Depends(get_session),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> list[Analysis]:
    stmt = select(Analysis).order_by(Analysis.id.desc()).offset(offset).limit(limit)
    return list(session.exec(stmt).all())


@router.get("/analyses/{analysis_id}", response_model=AnalysisResult)
def get_analysis(
    analysis_id: int, session: Session = Depends(get_session)
) -> AnalysisResult:
    row = session.get(Analysis, analysis_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Analysis not found")
    results = [
        MentionResult.model_validate(m, from_attributes=True) for m in row.mentions
    ]
    return AnalysisResult(
        id=row.id,
        brand=row.brand,
        domain=row.domain,
        category=row.category,
        visibility_score=row.visibility_score,
        mention_rate=row.mention_rate,
        recommendation_rate=row.recommendation_rate,
        created_at=row.created_at,
        results=results,
    )


@router.delete("/analyses/{analysis_id}", status_code=204)
def delete_analysis(analysis_id: int, session: Session = Depends(get_session)) -> None:
    row = session.get(Analysis, analysis_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Analysis not found")
    session.delete(row)
    session.commit()
