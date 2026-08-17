from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Severity = Literal["info", "low", "medium", "high", "critical"]


class RoastSectionSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    key: str = Field(min_length=1, max_length=100)
    title: str = Field(min_length=1, max_length=255)
    content: str = Field(min_length=1)


class RoastFindingSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    category: str = Field(min_length=1, max_length=50)
    severity: Severity
    title: str = Field(min_length=1, max_length=255)
    roast_text: str = Field(min_length=1)
    actual_feedback: str = Field(min_length=1)


class RoastResponseSchema(BaseModel):
    """
    Strict schema the AI's raw JSON response must satisfy exactly —
    unknown fields are rejected (extra="forbid"), severity is restricted
    to the 5 allowed values, and at least one section/finding is
    required. apps.ai.services.roasting validates every raw response
    against this before anything is persisted; on failure it retries
    (bounded, exponential) rather than ever saving partial/invalid data.
    """

    model_config = ConfigDict(extra="forbid")

    summary: str = Field(min_length=1)
    sections: list[RoastSectionSchema] = Field(min_length=1)
    findings: list[RoastFindingSchema] = Field(min_length=1)
    final_verdict: str = Field(min_length=1)
    score: int | None = Field(default=None, ge=0, le=100)
