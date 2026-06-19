#!/usr/bin/env python3
"""Demona subfront: Honeminas vectors as generator selectors."""

from __future__ import annotations

from post_review_common import HERE, write_json

OUT_JSON = HERE / "demona_honeminas_vector_audit_results.json"
OUT_MD = HERE / "demona_honeminas_vector_audit.md"


def main() -> None:
    result = {
        "schema": "demona_honeminas_vector_audit.v1",
        "translation_delta": "NONE",
        "verdict": "primary vectors are absent as exact corpus substrings; short 3478 is structural/common only",
        "sources": ["honeminas_vector_report.md", "deep_verification_report.md"],
    }
    write_json(OUT_JSON, result)
    OUT_MD.write_text(
        "# Demona / Honeminas Vector Audit\n\n"
        "Primary vectors `43153` and `34784` have zero exact hits in the 70-book corpus; "
        "`3478` is a short structural overlap and is not probative. No plaintext or seed is promoted.\n\n"
        "Translation delta: `NONE`.\n",
        encoding="utf-8",
    )
    print(f"wrote {OUT_JSON}")
    print(f"wrote {OUT_MD}")


if __name__ == "__main__":
    main()
