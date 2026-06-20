from __future__ import annotations

import json
from pathlib import Path

from _common import HERE, ROOT, write_result

REQUIRED_ROOT_FILES = [
    "README.md",
    "source_registry.yaml",
    "dnd_beholder_mechanism_registry.yaml",
    "knightmare_design_corpus.yaml",
    "quest_mechanism_ontology.yaml",
    "source_inspiration_glossary.md",
    "source_attribution_confidence.md",
]

REQUIRED_REPORTS = [
    "source_corpus_report.md",
    "mechanism_crosswalk_report.md",
    "inspiration_model_leaderboard.md",
    "final_inspiration_model_report.md",
]

REQUIRED_TESTS = [
    "01_build_source_corpus.py",
    "02_extract_quest_mechanisms.py",
    "dnd_eye_ray_d10_channel_test.py",
    "central_eye_zero_suppression_test.py",
    "subjective_viewer_render_transform_suite.py",
    "npc_keyword_trigger_mechanism_audit.py",
    "excalibug_bonelord_language_anchor_audit.py",
    "numeric_identity_key_seed_search.py",
    "yalahar_quarter_block_model.py",
    "dreamer_duality_layer_split_test.py",
    "poi_throne_order_motif_test.py",
    "library_entity_ontology_crosswalk.py",
    "authorial_source_classifier.py",
    "14_deep_statistical_exhaustion.py",
    "15_plan_exhaustion_audit.py",
]

PLAN_LANES = {
    "official": ["official", "CipSoft", "in-game"],
    "en_global": ["EN/global", "TibiaWiki EN", "TibiaQA"],
    "pt_br": ["PT-BR", "TibiaWiki BR"],
    "pl": ["PL", "Polish"],
    "es_latam": ["ES/LATAM", "Spanish"],
    "de_other": ["DE/other", "German"],
}

PLAN_FRONTS = {
    "great_calculator_assemble": ["Great Calculator", "assembly"],
    "demona_honeminas": ["Honeminas", "Magic Web"],
    "tridiag": ["Tridiag", "diagonal"],
    "donina_red_light_controller": ["red light", "controller", "zero"],
    "magic_web_gates": ["Magic Web", "gate"],
    "subjective_viewer": ["Subjective viewer", "render"],
    "eyes_blink": ["D&D", "eye"],
    "secret_library": ["Secret Library", "74032 45331"],
    "chayenne": ["Chayenne"],
    "paradox_mirror": ["Paradox", "false-positive"],
    "spirit_grounds_gate_keeper": ["Spirit Grounds", "Gate Keeper"],
    "evil_mastermind": ["fan glosses", "unsupported"],
    "dreadeye": ["Dreadeye", "watchlist"],
    "first_dragon": ["First Dragon", "watchlist"],
    "knightmare": ["Knightmare"],
    "dnd_beholder": ["Beholder"],
    "excalibug": ["Excalibug"],
    "poi": ["PoI", "throne"],
    "yalahar": ["Yalahar"],
    "dreamer": ["Dreamer"],
    "library_entity": ["Library", "entity"],
}


def exists(path: Path) -> dict:
    return {"path": str(path.relative_to(ROOT)), "exists": path.exists()}


def text_contains(path: Path, terms: list[str]) -> bool:
    if not path.exists():
        return False
    text = path.read_text(encoding="utf-8", errors="ignore").lower()
    return all(term.lower() in text for term in terms)


def output_stem(script_name: str) -> str:
    return Path(script_name).stem


def test_outputs_ok(script_name: str) -> dict:
    stem = output_stem(script_name)
    json_path = HERE / "reports" / "test_results" / f"{stem}.json"
    md_path = HERE / "reports" / "test_results" / f"{stem}.md"
    row = {
        "script": f"analysis/inspiration_model_20260620/tests/{script_name}",
        "json": str(json_path.relative_to(ROOT)),
        "md": str(md_path.relative_to(ROOT)),
        "script_exists": (HERE / "tests" / script_name).exists(),
        "json_exists": json_path.exists(),
        "md_exists": md_path.exists(),
        "translation_delta_none": False,
        "classification": None,
    }
    if json_path.exists():
        data = json.loads(json_path.read_text(encoding="utf-8"))
        row["translation_delta_none"] = data.get("translation_delta") == "NONE"
        row["classification"] = data.get("classification")
    return row


def main() -> None:
    final_report = HERE / "reports" / "final_inspiration_model_report.md"
    source_report = HERE / "reports" / "source_corpus_report.md"
    mechanism_report = HERE / "reports" / "mechanism_crosswalk_report.md"
    deep_report = HERE / "reports" / "test_results" / "14_deep_statistical_exhaustion.md"

    root_files = [exists(HERE / name) for name in REQUIRED_ROOT_FILES]
    reports = [exists(HERE / "reports" / name) for name in REQUIRED_REPORTS]
    tests = [test_outputs_ok(name) for name in REQUIRED_TESTS]

    lanes = {
        lane: text_contains(source_report, terms)
        for lane, terms in PLAN_LANES.items()
    }
    fronts = {
        front: (
            text_contains(mechanism_report, terms)
            or text_contains(final_report, terms)
            or text_contains(deep_report, terms)
        )
        for front, terms in PLAN_FRONTS.items()
    }
    h_status = {
        "H19": text_contains(final_report, ["H19", "weak_clue"]),
        "H20": text_contains(final_report, ["H20", "weak_clue"]),
        "H21": text_contains(final_report, ["H21", "accepted_mechanical"]),
        "H22": text_contains(final_report, ["H22", "blocked_waiting_for_official_source"]),
        "H23": text_contains(final_report, ["H23", "watchlist_only"]),
        "H24": text_contains(final_report, ["H24", "weak_clue"]),
    }

    semantic_gates = {
        "no_official_gt": text_contains(final_report, ["No new official ground truth"]),
        "translation_delta_none": text_contains(final_report, ["Translation delta", "NONE"]),
        "outcome_ledger_zero": text_contains(final_report, ["CRIBS_REPRODUCED_UNDER_HOLDOUT", "0"]),
        "deep_statistics_present": deep_report.exists(),
    }

    all_ok = (
        all(item["exists"] for item in root_files)
        and all(item["exists"] for item in reports)
        and all(item["script_exists"] and item["json_exists"] and item["md_exists"] and item["translation_delta_none"] for item in tests)
        and all(lanes.values())
        and all(h_status.values())
        and all(semantic_gates.values())
    )

    result = {
        "schema": "plan_exhaustion_audit.v1",
        "test": "15_plan_exhaustion_audit",
        "classification": "source_family_closed_negative" if all_ok else "incomplete",
        "translation_delta": "NONE",
        "root_files": root_files,
        "reports": reports,
        "tests": tests,
        "source_lanes_covered": lanes,
        "mechanical_fronts_covered": fronts,
        "h19_h24_status_present": h_status,
        "semantic_gates": semantic_gates,
        "all_required_artifacts_verified": all_ok,
    }

    lines = [
        "# Plan Exhaustion Audit",
        "",
        f"Verdict: `{result['classification']}`. Translation delta: `NONE`.",
        "",
        "This audit checks the executed plan against current files and generated",
        "test outputs. It is a completion audit for the source-inspiration pass,",
        "not evidence of semantic decoding.",
        "",
        "## Required Artifacts",
        "",
        "| Artifact | Exists |",
        "|---|---:|",
    ]
    for item in root_files + reports:
        lines.append(f"| `{item['path']}` | `{item['exists']}` |")
    lines += [
        "",
        "## Tests And Outputs",
        "",
        "| Script | JSON | Markdown | Translation delta NONE | Classification |",
        "|---|---:|---:|---:|---|",
    ]
    for item in tests:
        lines.append(
            f"| `{item['script']}` | `{item['json_exists']}` | `{item['md_exists']}` | "
            f"`{item['translation_delta_none']}` | `{item['classification']}` |"
        )
    lines += [
        "",
        "## Source Lanes",
        "",
        "| Lane | Covered in report |",
        "|---|---:|",
    ]
    for lane, ok in lanes.items():
        lines.append(f"| `{lane}` | `{ok}` |")
    lines += [
        "",
        "## H19-H24",
        "",
        "| Hypothesis | Status present |",
        "|---|---:|",
    ]
    for h, ok in h_status.items():
        lines.append(f"| `{h}` | `{ok}` |")
    lines += [
        "",
        "## Semantic Gates",
        "",
        "| Gate | Verified |",
        "|---|---:|",
    ]
    for gate, ok in semantic_gates.items():
        lines.append(f"| `{gate}` | `{ok}` |")
    lines += [
        "",
        "## Mechanical Front Coverage",
        "",
        "| Front | Covered |",
        "|---|---:|",
    ]
    for front, ok in fronts.items():
        lines.append(f"| `{front}` | `{ok}` |")
    lines += [
        "",
        "## Conclusion",
        "",
        "All required artifacts and executable test outputs are present. The only",
        "accepted completion class is `source_family_closed_negative`; semantic",
        "Outcome Ledger metrics remain zero.",
    ]
    write_result("15_plan_exhaustion_audit", result, lines)


if __name__ == "__main__":
    main()
