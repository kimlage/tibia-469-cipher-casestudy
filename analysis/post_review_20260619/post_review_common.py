#!/usr/bin/env python3
"""Shared helpers for the 2026-06-19 post-review closure artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
GEN = ROOT / "analysis" / "generator_search_20260618"
LORE = ROOT / "analysis" / "lore_audit_20260618"
EYE = ROOT / "analysis" / "eye_model_20260619"


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def first_table_row(report: Path, marker: str) -> str:
    lines = report.read_text(encoding="utf-8").splitlines()
    for idx, line in enumerate(lines):
        if marker in line:
            for probe in lines[idx + 1 :]:
                if probe.startswith("|") and not set(probe.replace("|", "").strip()) <= {"-", ":"}:
                    return probe
    return ""


def report_exists(name: str) -> bool:
    return (GEN / name).exists() or (EYE / name).exists() or (LORE / name).exists()
