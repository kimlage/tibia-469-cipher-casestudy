from __future__ import annotations

import json
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports" / "test_results"
REGISTRY = HERE / "hypothesis_registry.yaml"
BASELINE = ROOT / "analysis/generator_search_20260618/tape_based_formula_469.json"


def write_result(name: str, result: dict, lines: list[str]) -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / f"{name}.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (REPORTS / f"{name}.md").write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> None:
    registry = yaml.safe_load(REGISTRY.read_text(encoding="utf-8"))
    baseline = json.loads(BASELINE.read_text(encoding="utf-8"))
    hypotheses = registry["hypotheses"]
    required = {
        "H-AUTH1",
        "H-AUTH2",
        "H-AUTH3",
        "H-GEN1",
        "H-GEN2",
        "H-GEN3",
        "H-GEN3B",
        "H-GEN3C",
        "H-GEN3D",
        "H-GEN3E",
        "H-GEN3F",
        "H-GEN3G",
        "H-GEN3H",
        "H-GEN3I",
        "H-GEN3J",
        "H-GEN3K",
        "H-GEN3L",
        "H-GEN3M",
        "H-GEN3N",
        "H-GEN3O",
        "H-GEN3P",
        "H-GEN3Q",
        "H-GEN4",
        "H-GEN4A",
        "H-GEN5",
    }
    semantic_policy = registry["semantic_policy"]
    checks = {
        "all_required_hypotheses_present": set(hypotheses) == required,
        "baseline_exists": BASELINE.exists(),
        "baseline_roundtrips_70": baseline["validation"]["books_roundtrip_ok"] == 70,
        "baseline_translation_delta_none": baseline["translation_delta"] == "NONE",
        "registry_translation_delta_none": registry["translation_delta"] == "NONE",
        "no_plaintext_from_authorial_model": semantic_policy["no_plaintext_from_authorial_model"] is True,
        "no_fan_gloss_as_ground_truth": semantic_policy["no_fan_gloss_as_ground_truth"] is True,
        "no_llm_prose_as_evidence": semantic_policy["no_llm_prose_as_evidence"] is True,
    }
    blocked_use_ok = {
        key: bool(value.get("blocked_use") or value.get("promotion_rule"))
        for key, value in hypotheses.items()
    }
    all_ok = all(checks.values()) and all(blocked_use_ok.values())
    result = {
        "schema": "first_principles_hypothesis_audit.v1",
        "test": "01_first_principles_hypothesis_audit",
        "classification": "mechanism_prior_integrated" if all_ok else "incomplete",
        "translation_delta": "NONE",
        "checks": checks,
        "blocked_or_promotion_rules_present": blocked_use_ok,
        "baseline_formula": str(BASELINE.relative_to(ROOT)),
        "baseline_verdict": baseline["verdict"],
        "baseline_books_roundtrip": baseline["validation"]["books_roundtrip_ok"],
    }
    lines = [
        "# First-Principles Hypothesis Audit",
        "",
        f"Verdict: `{result['classification']}`. Translation delta: `NONE`.",
        "",
        "This audit converts the report's first-principles claims into bounded",
        "authorial/mechanical hypotheses. It does not infer private intent and",
        "does not promote plaintext.",
        "",
        "## Checks",
        "",
        "| Check | Verified |",
        "|---|---:|",
    ]
    for key, ok in checks.items():
        lines.append(f"| `{key}` | `{ok}` |")
    lines += [
        "",
        "## Hypotheses",
        "",
        "| ID | Status | Guard present |",
        "|---|---|---:|",
    ]
    for key, value in hypotheses.items():
        lines.append(f"| `{key}` | `{value['status']}` | `{blocked_use_ok[key]}` |")
    lines += [
        "",
        "## Conclusion",
        "",
        "The report is integrated as a mechanism-search prior. Semantic progress",
        "remains zero until official ground truth appears.",
    ]
    write_result("01_first_principles_hypothesis_audit", result, lines)


if __name__ == "__main__":
    main()
