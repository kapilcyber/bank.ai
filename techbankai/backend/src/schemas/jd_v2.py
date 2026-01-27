"""V2 schemas for JD structure and per-resume evidence (library-dimensions only)."""

from __future__ import annotations

from typing import Dict, List, Literal, Optional
from pydantic import BaseModel, Field, field_validator


Priority = Literal["MUST", "SHOULD", "NICE"]
Confidence = Literal["high", "medium", "low", "none"]


class JDSelectedDimensionV2(BaseModel):
    """A JD-selected dimension from the backend dimension library."""

    dimension_id: str = Field(..., description="Must be a valid backend dimension library id")
    priority: Priority = Field("SHOULD", description="Relative importance. Backend may ignore for weighting.")
    required_skills: List[str] = Field(default_factory=list)
    preferred_skills: List[str] = Field(default_factory=list)
    # Optional; must not affect scoring
    evidence_snippets: Optional[List[str]] = Field(default=None)


class JDStructureV2(BaseModel):
    jd_role: str = Field(default="Not mentioned")
    min_experience_years: float = Field(default=0.0, ge=0.0)
    selected_dimensions: List[JDSelectedDimensionV2] = Field(default_factory=list)


class DimensionEvidenceV2(BaseModel):
    confidence: Confidence = Field(..., description="high|medium|low|none")
    evidence_skills: List[str] = Field(default_factory=list)
    # Optional; must not affect scoring
    evidence_text: Optional[str] = Field(default=None)


class ResumeEvidenceV2(BaseModel):
    """Evidence keyed by dimension id."""

    evidence_by_dimension: Dict[str, DimensionEvidenceV2] = Field(default_factory=dict)

    @field_validator("evidence_by_dimension")
    @classmethod
    def _keys_must_be_non_empty(cls, v: Dict[str, DimensionEvidenceV2]):
        # Basic structural validation; library validation happens in service layer where we have the library.
        for k in v.keys():
            if not isinstance(k, str) or not k.strip():
                raise ValueError("dimension id keys must be non-empty strings")
        return v



