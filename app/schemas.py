"""Pydantic request/response models.

These are the API's public contract. FastAPI turns them into the OpenAPI
schema, which is what a frontend's codegen consumes to get a type-safe client.
They are deliberately separate from the SQLModel tables (models.py): DTOs at
the edge, entities in the database.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AnalyzeRequest(BaseModel):
    brand: str = Field(..., min_length=1, examples=["Yolando"])
    domain: str | None = Field(default=None, examples=["yolando.ai"])
    category: str | None = Field(
        default=None,
        description="Market category, e.g. 'generative engine optimization tools'.",
        examples=["AI brand-visibility tools"],
    )
    aliases: list[str] = Field(
        default_factory=list,
        description="Alternate spellings/names to also count as a mention.",
    )
    prompts: list[str] | None = Field(
        default=None, description="Override the default buyer-intent prompts."
    )
    models: list[str] | None = Field(
        default=None,
        description="Subset of provider names to query (default: all available).",
    )


class MentionResult(BaseModel):
    prompt: str
    model: str
    mentioned: bool
    recommended: bool
    rank: int | None = Field(
        default=None, description="1-based position when the answer is a ranked list."
    )
    excerpt: str | None = None
    score: float = Field(description="Per-(prompt, model) visibility score, 0..1.")
    latency_ms: int
    cached: bool


class AnalysisSummary(BaseModel):
    # Lets FastAPI serialize SQLModel ORM rows straight into this DTO.
    model_config = ConfigDict(from_attributes=True)

    id: int | None = None
    brand: str
    domain: str | None = None
    category: str | None = None
    visibility_score: float = Field(description="Aggregate score, 0..100.")
    mention_rate: float = Field(description="Fraction of queries that mentioned the brand.")
    recommendation_rate: float
    created_at: datetime


class AnalysisResult(AnalysisSummary):
    results: list[MentionResult]


# --- Server-Sent Events payloads (streaming endpoint) ---


class StreamProgress(BaseModel):
    type: str = "progress"
    done: int
    total: int
    result: MentionResult


class StreamDone(BaseModel):
    type: str = "summary"
    summary: AnalysisResult
