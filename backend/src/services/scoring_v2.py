"""
V2 scoring - deterministic and backend-owned.

Locked confidence multipliers (single source of truth):
- high   = 0.90
- medium = 0.65
- low    = 0.35
- none   = 0.00
"""

from __future__ import annotations

from typing import Dict


CONFIDENCE_MULTIPLIERS: Dict[str, float] = {
    "high": 0.90,
    "medium": 0.65,
    "low": 0.35,
    "none": 0.00,
}


def score_dimension(confidence: str, max_points: int) -> int:
    """Score a single dimension deterministically."""
    conf = (confidence or "none").strip().lower()
    mult = CONFIDENCE_MULTIPLIERS.get(conf, 0.0)
    # Round to nearest int points
    return int(round(max_points * mult))


def score_breakdown(confidence_by_dimension: Dict[str, str], weights: Dict[str, int]) -> Dict[str, int]:
    """Compute breakdown points per dimension id."""
    breakdown: Dict[str, int] = {}
    for dim_id, weight in (weights or {}).items():
        confidence = (confidence_by_dimension or {}).get(dim_id, "none")
        breakdown[dim_id] = score_dimension(confidence, int(weight))
    return breakdown


def score_total(breakdown: Dict[str, int]) -> int:
    total = sum(int(v) for v in (breakdown or {}).values())
    return max(0, min(100, int(total)))



