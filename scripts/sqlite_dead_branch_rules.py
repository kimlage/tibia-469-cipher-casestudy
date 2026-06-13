#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Sequence


@dataclass(frozen=True)
class DeadBranchRule:
    label: str
    patterns: Sequence[str]
    reason: str


KNOWN_DEAD_BRANCH_RULES: Sequence[DeadBranchRule] = (
    DeadBranchRule(
        label="ac010_wrapper_workbook",
        patterns=(
            "ac010",
            "itelbenna",
            "telbennai",
            "tleitelb",
            "leitelbenna",
            "fiininsb",
            "ifiininsb",
            "niifini",
            "ltasttnv",
            "vnnfieeeiiinfasi",
            "fasiatnvi",
        ),
        reason="AC010 wrapper/workbook and isolated force-probe branches were exhausted or unsafe.",
    ),
    DeadBranchRule(
        label="ac008_workbook_tuning",
        patterns=(
            "ac008",
            "ivifastfneie",
            "ifastfnei",
            "ifvi",
            "naesestienfatc",
        ),
        reason="AC008 pair 1+3 was promoted; further workbook tuning repeated no-op or toxic basins.",
    ),
    DeadBranchRule(
        label="ac013_017_019_shoulder",
        patterns=(
            "ac013",
            "ac017",
            "ac019",
            "nstaefieie",
            "nstaefieief",
        ),
        reason="AC013/AC017/AC019 shoulder probes closed as shallow tuning.",
    ),
    DeadBranchRule(
        label="direct_3478",
        patterns=(
            "3478",
            "bonelordname_3478",
            "knightmare1",
        ),
        reason="Direct 3478 anchor-only lanes dropped candidates without useful uptake.",
    ),
    DeadBranchRule(
        label="hellgate_book38_macro_peel",
        patterns=(
            "hellgate",
            "book38",
            "onafieiveinletfnaastvafenteeaeiseteivifastfneie",
        ),
        reason="Book38/Hellgate head-macro peel lanes were clean no-ops.",
    ),
    DeadBranchRule(
        label="crib6_book60_btilbeta",
        patterns=(
            "crib6",
            "book60",
            "btilbeta",
            "eiinb",
            "iinb",
        ),
        reason="Crib6/IIN/Book60/BTILBETA branch closed without useful local gain.",
    ),
    DeadBranchRule(
        label="chay1_pair_decomp",
        patterns=(
            "chay1",
            "aett",
        ),
        reason="Chay1 pair/subfamily decomposition repeated DP_UNUSED or no-op.",
    ),
    DeadBranchRule(
        label="stalled_midright_chay2",
        patterns=(
            "chay2",
            "tisete",
            "midright",
            "fiftleitelbast",
        ),
        reason="Mid-right and Chay2 confirmation lanes stalled without persisted checkpoint.",
    ),
)


def _norm(value: object) -> str:
    return str(value or "").strip().lower()


def matching_dead_rules(values: Iterable[object]) -> List[DeadBranchRule]:
    haystack = " ".join(_norm(value) for value in values if _norm(value))
    if not haystack:
        return []
    out: List[DeadBranchRule] = []
    for rule in KNOWN_DEAD_BRANCH_RULES:
        for pattern in rule.patterns:
            needle = _norm(pattern)
            if not needle:
                continue
            if needle in haystack:
                out.append(rule)
                break
    return out
