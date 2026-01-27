from __future__ import annotations

from typing import Any, Dict, Iterable, List


def _as_list(v: Any) -> List[Any]:
    if v is None:
        return []
    if isinstance(v, list):
        return v
    if isinstance(v, str):
        # Handle comma-separated skills sometimes stored as a string
        return [s.strip() for s in v.split(",") if s.strip()]
    return [v]


def _norm(s: Any) -> str:
    if s is None:
        return ""
    if not isinstance(s, str):
        s = str(s)
    return " ".join(s.strip().split()).lower()


def build_canonical_resume_skills(
    resume_skills: Iterable[str] | None,
    parsed_data: Dict[str, Any] | None,
) -> List[str]:
    """
    Canonical resume skill set (normalized, deduped, stable-sorted).

    MUST be the UNION of:
    - resume.skills
    - parsed_data.resume_technical_skills
    - parsed_data.all_skills
    """
    parsed_data = parsed_data or {}

    merged: List[Any] = []
    merged.extend(list(resume_skills or []))
    merged.extend(_as_list(parsed_data.get("resume_technical_skills")))
    merged.extend(_as_list(parsed_data.get("all_skills")))

    out = {_norm(x) for x in merged}
    out.discard("")
    return sorted(out)


