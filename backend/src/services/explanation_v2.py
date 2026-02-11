"""Deterministic 2-sentence explanation generator (V2)."""

from __future__ import annotations

from typing import Dict, List, Optional


def _top_dimensions(breakdown: Dict[str, int], top_n: int = 2) -> List[str]:
    items = sorted((breakdown or {}).items(), key=lambda kv: (kv[1], kv[0]), reverse=True)
    return [k for k, _ in items[:top_n] if isinstance(k, str)]


def _lowest_dimension(breakdown: Dict[str, int]) -> Optional[str]:
    if not breakdown:
        return None
    items = sorted((breakdown or {}).items(), key=lambda kv: (kv[1], kv[0]))
    return items[0][0] if items else None


def build_explanation(
    total_score: int,
    breakdown: Dict[str, int],
    dimension_labels: Dict[str, str],
    matched_skills: List[str],
    missing_skills: List[str],
) -> str:
    """
    Return exactly two short sentences explaining the score.

    Does not depend on optional JD evidence snippets.
    """
    top_dims = _top_dimensions(breakdown, top_n=2)
    top_labels = [dimension_labels.get(d, d) for d in top_dims]

    strengths_part = " and ".join([lbl for lbl in top_labels if lbl]) or "key areas"
    matched_part = ""
    if matched_skills:
        matched_part = f" (matched: {', '.join(matched_skills[:3])})"

    gap_skill = missing_skills[0] if missing_skills else None
    low_dim = _lowest_dimension(breakdown)
    low_label = dimension_labels.get(low_dim, low_dim) if low_dim else None

    sentence1 = f"Scored {total_score}/100 with strongest alignment in {strengths_part}{matched_part}."

    if gap_skill:
        sentence2 = f"Main gap is {gap_skill}; improving this could raise the fit for the role."
    elif low_label:
        sentence2 = f"Main gap is weaker alignment in {low_label}; more direct evidence could improve the score."
    else:
        sentence2 = "No major gaps detected from the available resume evidence."

    return f"{sentence1} {sentence2}"



