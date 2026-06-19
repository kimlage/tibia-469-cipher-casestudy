#!/usr/bin/env python3
"""Demona subfront: Tridiag/incomplete-formula diagonal bridge."""

from __future__ import annotations

from post_review_common import HERE, write_json

OUT_JSON = HERE / "demona_tridiag_incomplete_formula_audit_results.json"
OUT_MD = HERE / "demona_tridiag_incomplete_formula_audit.md"


def main() -> None:
    result = {
        "schema": "demona_tridiag_incomplete_formula_audit.v1",
        "translation_delta": "NONE",
        "verdict": "diagonal/E pressure is a local mechanism signal, not a complete formula",
        "sources": ["e_layer_lore_bridge_audit.md", "shared_e_zero_predicate_report.md"],
    }
    write_json(OUT_JSON, result)
    OUT_MD.write_text(
        "# Demona / Tridiag Incomplete Formula Audit\n\n"
        "The diagonal/E signal survives only as local mechanism context. It does not derive "
        "the row0 labels or create a translation.\n\n"
        "Translation delta: `NONE`.\n",
        encoding="utf-8",
    )
    print(f"wrote {OUT_JSON}")
    print(f"wrote {OUT_MD}")


if __name__ == "__main__":
    main()
