from __future__ import annotations

import json
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports" / "test_results"

REQUIRED_LEXICA = [
    "jekhr_lexicon.tsv",
    "orcish_lexicon.tsv",
    "chakoya_lexicon.tsv",
    "gharonk_lexicon.tsv",
    "elven_lexicon.tsv",
    "kaplar_anchor.tsv",
    "tibia_spell_formulae.tsv",
]
REQUIRED_REPORTS = [
    "language_inventory_report.md",
    "lexicon_confidence_report.md",
    "intermediate_script_test_report.md",
    "final_language_comparanda_report.md",
]


def load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def write_result(name: str, result: dict, lines: list[str]) -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / f"{name}.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (REPORTS / f"{name}.md").write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def count_tsv_rows(path: Path) -> int:
    if not path.exists():
        return 0
    lines = [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    return max(0, len(lines) - 1)


def main() -> None:
    registry = load_yaml(HERE / "language_registry.yaml")
    confidence = load_yaml(HERE / "source_confidence.yaml")
    lexica = {
        name: {
            "path": f"analysis/language_comparanda_20260620/lexica/{name}",
            "exists": (HERE / "lexica" / name).exists(),
            "rows": count_tsv_rows(HERE / "lexica" / name),
        }
        for name in REQUIRED_LEXICA
    }
    reports = {
        name: {
            "path": f"analysis/language_comparanda_20260620/reports/{name}",
            "exists": (HERE / "reports" / name).exists(),
        }
        for name in REQUIRED_REPORTS
    }

    labels = confidence.get("labels", {})
    all_labels_block_promotion = all(
        not data.get("promotion_allowed", False)
        for key, data in labels.items()
        if key != "official_gt"
    )
    official_gt_gate = (
        labels["official_gt"]["promotion_allowed"] is True
        and labels["official_gt"]["present_for_469"] is False
    )
    source_roles = {
        lang_id: {
            "positive_or_control": any(
                role in " ".join(item.get("allowed_use", []))
                for role in ["control", "benchmark", "watchlist", "target_corpus"]
            ),
            "blocked_use_present": bool(item.get("blocked_use")),
        }
        for lang_id, item in registry["languages"].items()
    }

    readme = (HERE / "README.md").read_text(encoding="utf-8")
    stop_rules = {
        "no_plaintext_promotion": "No 469 plaintext" in readme,
        "mdl_required": "improve MDL" in registry.get("global_stop_rule", ""),
        "official_gt_required": "CipSoft/in-game" in registry.get("global_stop_rule", ""),
        "community_labels_present": {"fan_claim", "uncertain", "rejected_control", "community_reconstruction"}.issubset(labels),
    }

    all_ok = (
        all(item["exists"] and item["rows"] > 0 for item in lexica.values())
        and all(item["exists"] for item in reports.values())
        and all_labels_block_promotion
        and official_gt_gate
        and all(v["positive_or_control"] and v["blocked_use_present"] for v in source_roles.values())
        and all(stop_rules.values())
    )
    result = {
        "schema": "benchmark_readiness_audit.v1",
        "test": "02_benchmark_readiness_audit",
        "classification": "benchmark_ready_control_only" if all_ok else "benchmark_incomplete",
        "translation_delta": "NONE",
        "lexica": lexica,
        "reports": reports,
        "all_non_official_labels_block_promotion": all_labels_block_promotion,
        "official_gt_gate": official_gt_gate,
        "source_roles": source_roles,
        "stop_rules": stop_rules,
    }

    lines = [
        "# Benchmark Readiness Audit",
        "",
        f"Verdict: `{result['classification']}`. Translation delta: `NONE`.",
        "",
        "This audit checks whether the comparanda material is usable as future",
        "positive/negative controls while preserving the project closure gates.",
        "",
        "## Lexica",
        "",
        "| File | Exists | Rows |",
        "|---|---:|---:|",
    ]
    for item in lexica.values():
        lines.append(f"| `{item['path']}` | `{item['exists']}` | `{item['rows']}` |")
    lines += [
        "",
        "## Reports",
        "",
        "| File | Exists |",
        "|---|---:|",
    ]
    for item in reports.values():
        lines.append(f"| `{item['path']}` | `{item['exists']}` |")
    lines += [
        "",
        "## Stop Rules",
        "",
        "| Rule | Verified |",
        "|---|---:|",
    ]
    for rule, ok in stop_rules.items():
        lines.append(f"| `{rule}` | `{ok}` |")
    lines += [
        "",
        "## Conclusion",
        "",
        "The seed corpora are sufficient for registry-level future tests, not for",
        "new semantic claims. Full recovery benchmarks still require expanded",
        "transcripts/books per language before scoring.",
    ]
    write_result("02_benchmark_readiness_audit", result, lines)


if __name__ == "__main__":
    main()
