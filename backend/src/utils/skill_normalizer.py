"""Skill normalization helpers for deterministic matching (V2)."""

from __future__ import annotations

from typing import Iterable, List, Set


def normalize_skill(s: str) -> str:
    if not isinstance(s, str):
        s = str(s) if s is not None else ""
    return " ".join(s.strip().split()).lower()


def normalize_skills(skills: Iterable[str]) -> List[str]:
    out: Set[str] = set()
    for s in skills or []:
        if s is None:
            continue
        ns = normalize_skill(s)
        if ns:
            out.add(ns)
    return sorted(out)


def intersection(a: Iterable[str], b: Iterable[str]) -> List[str]:
    na = set(normalize_skills(a))
    nb = set(normalize_skills(b))
    return sorted(na.intersection(nb))


def difference(a: Iterable[str], b: Iterable[str]) -> List[str]:
    na = set(normalize_skills(a))
    nb = set(normalize_skills(b))
    return sorted(na.difference(nb))



