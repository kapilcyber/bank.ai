"""V2 deterministic weight assignment for dynamically selected dimensions."""

from __future__ import annotations

from typing import Dict, List


def assign_equal_weights(dimension_ids: List[str]) -> Dict[str, int]:
    """
    Deterministically assign weights that sum to 100 by distributing equally.

    This is intentionally simple/stable (same selected dims -> same weights),
    and avoids making weights depend on GPT-provided priority labels.
    """
    ids = [d for d in (dimension_ids or []) if isinstance(d, str) and d.strip()]
    if not ids:
        return {}

    n = len(ids)
    base = 100 // n
    remainder = 100 - (base * n)

    weights: Dict[str, int] = {dim_id: base for dim_id in ids}

    # Distribute remainder deterministically by sorted ids
    for dim_id in sorted(ids)[:remainder]:
        weights[dim_id] += 1

    return weights



