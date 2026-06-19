#!/usr/bin/env python3
"""Demona subfront: Donina/red-light/controller as render/priority cue."""

from __future__ import annotations

from post_review_common import HERE, write_json

OUT_JSON = HERE / "demona_donina_red_light_controller_audit_results.json"
OUT_MD = HERE / "demona_donina_red_light_controller_audit.md"


def main() -> None:
    result = {
        "schema": "demona_donina_red_light_controller_audit.v1",
        "translation_delta": "NONE",
        "verdict": "controller/red-light language maps only to render/priority context; no decoder",
        "sources": ["observer_transform_render_audit.md", "e_layer_lore_bridge_audit.md"],
    }
    write_json(OUT_JSON, result)
    OUT_MD.write_text(
        "# Demona / Donina Red-Light Controller Audit\n\n"
        "Controller/red-light language is retained only as an analogy for render, priority, "
        "or gate behavior. Existing controls do not promote it as a generator or plaintext route.\n\n"
        "Translation delta: `NONE`.\n",
        encoding="utf-8",
    )
    print(f"wrote {OUT_JSON}")
    print(f"wrote {OUT_MD}")


if __name__ == "__main__":
    main()
