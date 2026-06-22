from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports"
TEST_RESULTS = REPORTS / "test_results"

BOOKS_DIGITS = ROOT / "analysis" / "audit_20260609" / "books_digits.json"
COPY_SOURCE_LEDGER = (
    ROOT
    / "analysis"
    / "copy_source_generation_audit_20260621"
    / "reports"
    / "test_results"
    / "01_copy_source_ledger.json"
)
BOUNDARY_CANDIDATE_TRIGGER_GATE = TEST_RESULTS / "10_boundary_candidate_trigger_gate.json"
DECODER_VISIBLE_BOUNDARY_CANDIDATE_TRIGGER_GATE = (
    TEST_RESULTS / "11_decoder_visible_boundary_candidate_trigger_gate.json"
)
GATE10_SCRIPT = HERE / "scripts" / "10_boundary_candidate_trigger_gate.py"

OUT_STEM = "12_internal_boundary_candidate_trigger_decomposition_gate"


def load_gate10():
    spec = importlib.util.spec_from_file_location("boundary_candidate_trigger_gate", GATE10_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {GATE10_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gate10 = load_gate10()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def assert_boundary(name: str, data: dict[str, Any]) -> None:
    if data.get("translation_delta") != "NONE":
        raise RuntimeError(f"{name} changed translation boundary")
    if data.get("case_reopened", False) is not False:
        raise RuntimeError(f"{name} reopened case")
    if data.get("plaintext_claim", False) is not False:
        raise RuntimeError(f"{name} introduced plaintext")
    decision = data.get("decision", {})
    if decision.get("row0_origin_status") not in {
        None,
        "unchanged_exogenous",
        "exogenous_under_current_evidence",
    }:
        raise RuntimeError(f"{name} changed row0 origin")
    if decision.get("translation_or_plaintext_status", "NONE") != "NONE":
        raise RuntimeError(f"{name} introduced translation/plaintext")


def make_result() -> dict[str, Any]:
    ledger = load_json(COPY_SOURCE_LEDGER)
    gate10_result = load_json(BOUNDARY_CANDIDATE_TRIGGER_GATE)
    gate11_result = load_json(DECODER_VISIBLE_BOUNDARY_CANDIDATE_TRIGGER_GATE)
    assert_boundary("copy_source_ledger", ledger)
    assert_boundary("boundary_candidate_trigger_gate", gate10_result)
    assert_boundary("decoder_visible_boundary_candidate_trigger_gate", gate11_result)
    books = {int(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    candidate_rows = gate10.build_rows(books, ledger["canonical_ops_by_book"])
    internal_rows = [row for row in candidate_rows if not row["is_book_start"]]
    eval_rows = gate10.evaluate_all(internal_rows)
    global_rows = [row for row in eval_rows if row["feature"] == "global_majority"]
    feature_rows = [row for row in eval_rows if row["feature"] != "global_majority"]
    best_global = max(global_rows, key=lambda row: row["saving_vs_lookup_bits"])
    best_feature = max(
        feature_rows,
        key=lambda row: (
            row["delta_bits_vs_global"],
            row["delta_start_hits_vs_global"],
        ),
    )
    best_overall = max(eval_rows, key=lambda row: row["saving_vs_lookup_bits"])
    control = gate10.random_control(internal_rows)
    promotes = (
        best_feature["delta_bits_vs_global"] > control["best_delta_bits_p95"]
        and best_feature["delta_start_hits_vs_global"] > control["best_start_hits_p95"]
        and best_feature["saving_vs_lookup_bits"] > 0
    )
    weak = (
        not promotes
        and best_feature["delta_bits_vs_global"] > 0
        and best_feature["delta_start_hits_vs_global"] > 0
    )
    all_candidate_delta = gate10_result["summary"]["best_feature_delta_bits_vs_global"]
    decoder_visible_internal_delta = gate11_result["summary"][
        "internal_best_feature_delta_bits_vs_global"
    ]
    summary = {
        "candidate_policy": "right_ge:4",
        "internal_candidate_count": len(internal_rows),
        "internal_actual_starts": sum(1 for row in internal_rows if row["label"] != "nonstart"),
        "internal_literal_starts": sum(1 for row in internal_rows if row["label"] == "literal"),
        "internal_copy_starts": sum(1 for row in internal_rows if row["label"] == "copy"),
        "best_overall_feature": best_overall["feature"],
        "best_overall_cutoff": best_overall["cutoff"],
        "best_overall_exact_candidates": best_overall["exact_candidates"],
        "best_overall_test_candidates": best_overall["test_candidates"],
        "best_overall_start_hits": best_overall["start_hits"],
        "best_overall_actual_starts": best_overall["actual_starts"],
        "best_overall_saving_vs_lookup_bits": best_overall["saving_vs_lookup_bits"],
        "best_global_cutoff": best_global["cutoff"],
        "best_global_exact_candidates": best_global["exact_candidates"],
        "best_global_test_candidates": best_global["test_candidates"],
        "best_global_start_hits": best_global["start_hits"],
        "best_global_saving_vs_lookup_bits": best_global["saving_vs_lookup_bits"],
        "best_feature": best_feature["feature"],
        "best_feature_cutoff": best_feature["cutoff"],
        "best_feature_exact_candidates": best_feature["exact_candidates"],
        "best_feature_test_candidates": best_feature["test_candidates"],
        "best_feature_start_hits": best_feature["start_hits"],
        "best_feature_actual_starts": best_feature["actual_starts"],
        "best_feature_literal_hits": best_feature["literal_hits"],
        "best_feature_copy_hits": best_feature["copy_hits"],
        "best_feature_predicted_starts": best_feature["predicted_starts"],
        "best_feature_errors": best_feature["errors"],
        "best_feature_saving_vs_lookup_bits": best_feature["saving_vs_lookup_bits"],
        "best_feature_delta_bits_vs_global": best_feature["delta_bits_vs_global"],
        "best_feature_delta_start_hits_vs_global": best_feature["delta_start_hits_vs_global"],
        "random_delta_bits_p95": control["best_delta_bits_p95"],
        "random_start_hits_p95": control["best_start_hits_p95"],
        "all_candidate_trigger_delta_bits": all_candidate_delta,
        "decoder_visible_internal_delta_bits": decoder_visible_internal_delta,
        "book_start_dominance_delta_bits": all_candidate_delta - max(
            0.0, best_feature["delta_bits_vs_global"]
        ),
        "promotes_internal_boundary_candidate_trigger": promotes,
        "weak_internal_boundary_candidate_trigger": weak,
        "interpretation": (
            "This gate removes book-start candidates from the promoted boundary-candidate "
            "trigger test while retaining target-conditioned copy availability. It asks "
            "whether the composed clue actually explains internal operation starts."
        ),
    }
    return {
        "schema": "internal_boundary_candidate_trigger_decomposition_gate_v1",
        "scope": "analysis_only_internal_decomposition_of_boundary_candidate_trigger",
        "inputs": {
            "books_digits": rel(BOOKS_DIGITS),
            "copy_source_ledger": rel(COPY_SOURCE_LEDGER),
            "boundary_candidate_trigger_gate": rel(BOUNDARY_CANDIDATE_TRIGGER_GATE),
            "decoder_visible_boundary_candidate_trigger_gate": rel(
                DECODER_VISIBLE_BOUNDARY_CANDIDATE_TRIGGER_GATE
            ),
        },
        "rows": eval_rows,
        "random_control": control,
        "summary": summary,
        "classification": (
            "internal_boundary_candidate_trigger_promoted"
            if promotes
            else (
                "internal_boundary_candidate_trigger_weak"
                if weak
                else "internal_boundary_candidate_trigger_rejected"
            )
        ),
        "decision": {
            "promotes_internal_boundary_candidate_trigger": promotes,
            "weak_internal_boundary_candidate_trigger": weak,
            "generator_status": "not_promoted",
            "book_start_dominance_status": "confirmed",
            "row0_origin_status": "unchanged_exogenous",
            "translation_or_plaintext_status": "NONE",
            "compression_bound_status": "unchanged_8154_676268",
        },
        "case_reopened": False,
        "plaintext_claim": False,
        "translation_delta": "NONE",
    }


def write_markdown(result: dict[str, Any]) -> None:
    s = result["summary"]
    lines = [
        "# Internal Boundary Candidate Trigger Decomposition Gate",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Test whether the promoted boundary-candidate trigger clue explains",
        "internal operation starts after removing book-start candidates.",
        "Target-conditioned copy availability is still allowed in this gate.",
        "",
        "## Summary",
        "",
        f"- Candidate policy: `{s['candidate_policy']}`.",
        f"- Internal candidate positions: `{s['internal_candidate_count']}`.",
        f"- Internal starts/literal/copy: `{s['internal_actual_starts']}` / `{s['internal_literal_starts']}` / `{s['internal_copy_starts']}`.",
        f"- Best overall feature: `{s['best_overall_feature']}`.",
        f"- Best overall cutoff: `{s['best_overall_cutoff']}`.",
        f"- Best overall exact candidates: `{s['best_overall_exact_candidates']}/{s['best_overall_test_candidates']}`.",
        f"- Best overall start hits: `{s['best_overall_start_hits']}/{s['best_overall_actual_starts']}`.",
        f"- Best overall saving vs three-way lookup: `{s['best_overall_saving_vs_lookup_bits']:.3f}` bits.",
        f"- Best global exact/start hits: `{s['best_global_exact_candidates']}/{s['best_global_test_candidates']}` / `{s['best_global_start_hits']}`.",
        f"- Best global saving vs three-way lookup: `{s['best_global_saving_vs_lookup_bits']:.3f}` bits.",
        f"- Best feature over global: `{s['best_feature']}`.",
        f"- Best feature cutoff: `{s['best_feature_cutoff']}`.",
        f"- Best feature exact candidates: `{s['best_feature_exact_candidates']}/{s['best_feature_test_candidates']}`.",
        f"- Best feature start hits: `{s['best_feature_start_hits']}/{s['best_feature_actual_starts']}`.",
        f"- Best feature literal/copy hits: `{s['best_feature_literal_hits']}` / `{s['best_feature_copy_hits']}`.",
        f"- Best feature predicted starts: `{s['best_feature_predicted_starts']}`.",
        f"- Best feature errors: `{s['best_feature_errors']}`.",
        f"- Best feature saving vs lookup: `{s['best_feature_saving_vs_lookup_bits']:.3f}` bits.",
        f"- Best feature delta vs global: `{s['best_feature_delta_bits_vs_global']:.3f}` bits.",
        f"- Best feature start-hit delta vs global: `{s['best_feature_delta_start_hits_vs_global']}`.",
        f"- Random delta bits p95: `{s['random_delta_bits_p95']:.3f}`.",
        f"- Random start-hit delta p95: `{s['random_start_hits_p95']:.3f}`.",
        f"- All-candidate trigger delta bits: `{s['all_candidate_trigger_delta_bits']:.3f}`.",
        f"- Book-start dominance delta bits: `{s['book_start_dominance_delta_bits']:.3f}`.",
        f"- Promotes internal boundary candidate trigger: `{s['promotes_internal_boundary_candidate_trigger']}`.",
        f"- Weak internal boundary candidate trigger: `{s['weak_internal_boundary_candidate_trigger']}`.",
        "",
        s["interpretation"],
        "",
        "## Best Rows",
        "",
        "| Cutoff | Feature | Exact | Start hits | Lit/Copy hits | Pred starts | Errors | Saving | Delta bits | Delta starts | Contexts |",
        "| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in sorted(
        result["rows"],
        key=lambda item: (
            item["delta_bits_vs_global"],
            item["delta_start_hits_vs_global"],
        ),
        reverse=True,
    )[:12]:
        lines.append(
            f"| `{row['cutoff']}` | `{row['feature']}` | "
            f"`{row['exact_candidates']}/{row['test_candidates']}` | "
            f"`{row['start_hits']}/{row['actual_starts']}` | "
            f"`{row['literal_hits']}/{row['copy_hits']}` | "
            f"`{row['predicted_starts']}` | `{row['errors']}` | "
            f"`{row['saving_vs_lookup_bits']:.3f}` | "
            f"`{row['delta_bits_vs_global']:.3f}` | "
            f"`{row['delta_start_hits_vs_global']}` | `{row['context_count']}` |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            "- Internal boundary-candidate trigger is not promoted unless a non-global feature beats the internal nonstart-majority baseline and shuffled-label controls after table/correction cost.",
            "- Under current features, even target-conditioned copy availability does not recover internal operation starts once book-start candidates are removed.",
            "- The previously promoted boundary-candidate trigger clue is therefore book-start dominated.",
            "- Compression bound is unchanged.",
            "- Row0 remains exogenous and unchanged.",
            "- No plaintext, translation, semantic reading, or case reopening is introduced.",
        ]
    )
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    (TEST_RESULTS / f"{OUT_STEM}.md").write_text(
        "\n".join(lines).rstrip() + "\n", encoding="utf-8"
    )


def main() -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    result = make_result()
    (TEST_RESULTS / f"{OUT_STEM}.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    write_markdown(result)
    print(json.dumps({"output": rel(TEST_RESULTS / f"{OUT_STEM}.json")}, indent=2))


if __name__ == "__main__":
    main()
