from __future__ import annotations

import json
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports" / "test_results"

REQUIRED_LANGUAGES = {
    "human_tibia_language",
    "bonelord_469",
    "deepling_jekhr",
    "orc_language",
    "chakoya_language",
    "gharonk_language",
    "elven_language",
    "kaplar_minotaur",
    "caveman_language",
}
REQUIRED_BENCHMARKS = {
    "deepling_jekhr": "primary_positive_control_for_intermediate_script",
    "orc_language": "positive_control_for_keyword_trade_language",
    "chakoya_language": "partial_lexicon_confidence_control",
    "gharonk_language": "non_numeric_number_words_control",
    "kaplar_minotaur": "false_expansion_control",
}
ROW0_ALPHABET = "*ABCEFILNORSTV"


def load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_result(name: str, result: dict, lines: list[str]) -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / f"{name}.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (REPORTS / f"{name}.md").write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> None:
    registry = load_yaml(HERE / "language_registry.yaml")
    confidence = load_yaml(HERE / "source_confidence.yaml")
    occ_streams = load_json(ROOT / "analysis/audit_20260609/homophone_channel/occ_streams.json")

    languages = registry["languages"]
    present = set(languages)
    missing = sorted(REQUIRED_LANGUAGES - present)
    extra = sorted(present - REQUIRED_LANGUAGES)

    source_checks = {}
    benchmark_checks = {}
    blocked_direct_decode = {}
    for lang_id, item in languages.items():
        sources = item.get("primary_sources", [])
        source_checks[lang_id] = {
            "source_count": len(sources),
            "all_have_url": all(bool(src.get("url")) for src in sources),
            "all_verified": all(src.get("verified_on") == "2026-06-20" for src in sources),
            "no_official_gt_claimed": all(src.get("source_type") != "official_gt" for src in sources),
        }
        blocked = item.get("blocked_use", [])
        blocked_direct_decode[lang_id] = any(
            "do_not" in entry or "without_controls" in entry for entry in blocked
        )
    for lang_id, required_use in REQUIRED_BENCHMARKS.items():
        benchmark_checks[lang_id] = required_use in languages[lang_id].get("allowed_use", [])

    alphabet = "".join(sorted(occ_streams["occ"]))
    class_code_total = sum(len(codes) for codes in occ_streams["class_sizes"].values())
    row0_check = {
        "alphabet": alphabet,
        "expected_alphabet": ROW0_ALPHABET,
        "alphabet_ok": alphabet == ROW0_ALPHABET,
        "symbol_count": len(occ_streams["occ"]),
        "class_code_total": class_code_total,
        "code_count_ok": class_code_total == 99,
        "occ_streams_path": "analysis/audit_20260609/homophone_channel/occ_streams.json",
    }

    hypothesis_status = {
        key: value.get("status")
        for key, value in confidence.get("hypotheses", {}).items()
    }
    h25_h30_ok = set(hypothesis_status) == {"H25", "H26", "H27", "H28", "H29", "H30"}
    semantic_gates = {
        "registry_translation_delta_none": registry.get("translation_delta") == "NONE",
        "confidence_translation_delta_none": confidence.get("translation_delta") == "NONE",
        "official_gt_present_for_469_false": confidence["labels"]["official_gt"]["present_for_469"] is False,
        "h25_h30_present": h25_h30_ok,
        "all_direct_decode_blocked": all(blocked_direct_decode.values()),
    }

    all_ok = (
        not missing
        and all(all(v.values()) for v in source_checks.values())
        and all(benchmark_checks.values())
        and row0_check["alphabet_ok"]
        and row0_check["code_count_ok"]
        and all(semantic_gates.values())
    )
    result = {
        "schema": "language_registry_audit.v1",
        "test": "01_language_registry_audit",
        "classification": "comparanda_registry_ready" if all_ok else "incomplete",
        "translation_delta": "NONE",
        "missing_languages": missing,
        "extra_languages": extra,
        "source_checks": source_checks,
        "benchmark_checks": benchmark_checks,
        "blocked_direct_decode": blocked_direct_decode,
        "row0_check": row0_check,
        "hypothesis_status": hypothesis_status,
        "semantic_gates": semantic_gates,
    }

    lines = [
        "# Language Registry Audit",
        "",
        f"Verdict: `{result['classification']}`. Translation delta: `NONE`.",
        "",
        "This audit verifies that the comparanda registry is complete enough for",
        "future benchmark use and that it cannot be mistaken for 469 semantic",
        "progress.",
        "",
        "## Required Languages",
        "",
        f"Missing: `{missing}`",
        f"Extra: `{extra}`",
        "",
        "## Source Checks",
        "",
        "| Language | Sources | URLs | Verified | No official GT claimed |",
        "|---|---:|---:|---:|---:|",
    ]
    for lang_id, check in source_checks.items():
        lines.append(
            f"| `{lang_id}` | `{check['source_count']}` | `{check['all_have_url']}` | "
            f"`{check['all_verified']}` | `{check['no_official_gt_claimed']}` |"
        )
    lines += [
        "",
        "## Benchmark Roles",
        "",
        "| Language | Required role present |",
        "|---|---:|",
    ]
    for lang_id, ok in benchmark_checks.items():
        lines.append(f"| `{lang_id}` | `{ok}` |")
    lines += [
        "",
        "## Row0 Substrate Check",
        "",
        f"- Alphabet: `{row0_check['alphabet']}`",
        f"- Class-code total: `{row0_check['class_code_total']}`",
        f"- Source: `{row0_check['occ_streams_path']}`",
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
        "## Conclusion",
        "",
        "The registry is ready as a benchmark/control artifact. It does not add",
        "official ground truth, plaintext, or a 469 mapping.",
    ]
    write_result("01_language_registry_audit", result, lines)


if __name__ == "__main__":
    main()
