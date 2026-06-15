"""SQLModel tables — the persisted entities.

SQLModel gives one class that is both the Pydantic model and the SQLAlchemy
table, which is why it pairs naturally with FastAPI. SQLite in dev, Postgres
in prod — the models don't change.
"""

from datetime import datetime, timezone

from sqlmodel import Field, Relationship, SQLModel


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Analysis(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    brand: str = Field(index=True)
    domain: str | None = None
    category: str | None = None
    visibility_score: float = 0.0
    mention_rate: float = 0.0
    recommendation_rate: float = 0.0
    created_at: datetime = Field(default_factory=_utcnow)

    mentions: list["Mention"] = Relationship(
        back_populates="analysis",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )


class Mention(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    analysis_id: int | None = Field(default=None, foreign_key="analysis.id", index=True)
    prompt: str
    model: str
    mentioned: bool = False
    recommended: bool = False
    rank: int | None = None
    excerpt: str | None = None
    score: float = 0.0
    latency_ms: int = 0
    cached: bool = False

    analysis: Analysis | None = Relationship(back_populates="mentions")
