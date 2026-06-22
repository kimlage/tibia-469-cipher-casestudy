#!/usr/bin/env python3
"""Compile final report for the stateful control program audit."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
FRONT = ROOT / "analysis" / "stateful_control_program_audit_20260622"
TEST_RESULTS = FRONT / "reports" / "test_results"
RESULT_PATH = TEST_RESULTS / "01_stateful_control_program_gate.json"
OUT = FRONT / "reports" / "final_stateful_control_program_audit.md"


def bits(value: float) -> str:
    return f"{value:.3f}"


def main() -> None:
    result = json.loads(RESULT_PATH.read_text())
    if result.get("translation_delta") != "NONE":
        raise SystemExit("translation delta must remain NONE")
    if result.get("case_reopened") or result.get("plaintext_claim"):
        raise SystemExit("audit must not reopen case or make plaintext claims")

    best_name = result["decision"]["best_by_bits"]
    best = result["models"][best_name]

    lines = [
        "# Final Stateful Control Program Audit",
        "",
        "Status: `analysis_only`",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Question",
        "",
        "This audit tests the next constructive route after the unified residual ledger: "
        "can a target-free stateful control program generate or economically encode the "
        "exact `type:length` stream, using only prefix training, book id, book length, "
        "remaining length, and previous emitted control state?",
        "",
        "It does not test translation, plaintext, fan glosses, semantics, or row0 origin. "
        "Row0 remains exogenous and the compression bound is unchanged.",
        "",
        "## Result",
        "",
        f"- Best model: `{best_name}` with features `{'+'.join(best['features'])}`.",
        f"- Best model bits over prefix/suffix cutoffs: `{bits(best['observed_total_model_bits'])}`.",
        f"- Saving vs independent exact type+length declaration: `{bits(best['observed_total_saving_bits'])}` bits.",
        f"- Shuffled-control p95 saving: `{bits(best['random_saving_p95'])}` bits.",
        f"- Fallback rows: `{best['observed_total_fallback_rows']}`.",
        f"- Promoted models: `{result['decision']['promoted_models']}`.",
        f"- Generator-promoted models: `{result['decision']['generator_promoted']}`.",
        "",
        "All tested state models are rejected. The best model, `remaining_prev_bucket`, "
        "is still `1001.211` bits worse than declaring exact op type and length "
        "independently, and it is worse than shuffled-control p95. This means the "
        "observed `previous_op` coupling from the unified ledger is not sufficient to "
        "become an exact control program.",
        "",
        "## Generation Check",
        "",
        "| Cutoff | Test Books | Greedy Exact | Beam20 Exact | Beam20 Nontrivial | Greedy Prefix Ops |",
        "| ---: | ---: | ---: | ---: | ---: | ---: |",
    ]

    for row in best["cutoff_rows"]:
        lines.append(
            f"| `{row['cutoff']}` | `{row['test_books']}` | `{row['greedy_exact_books']}` | "
            f"`{row['beam20_exact_books']}` | `{row['beam20_nontrivial_exact_books']}` | "
            f"`{row['greedy_prefix_ops']}` |"
        )

    lines.extend(
        [
            "",
            "The few Beam20 exact hits occur only in trivial one-operation books and only "
            "under a codec that already fails the cost/control gate. They are therefore "
            "not generation evidence.",
            "",
            "## Decision",
            "",
            "- `stateful_control_program_not_promoted`.",
            "- Exact `type:length` remains an external control stream.",
            "- The route did not move the generator closer except by closing this direct "
            "stateful-program shortcut.",
            "- The current model remains a strong mechanical parser/compressor with "
            "explicit residual streams, not a complete authorial generator.",
            "",
            "## Remaining External Fields",
            "",
            "- exact `type:length` control sequence",
            "- literal innovation tape payload and schedule",
            "- copy-hint rank stream",
            "- seed books `0..9`",
            "- `row0`",
            "",
            "## Next Blocker",
            "",
            "The next route should not be another exact-action Markov/context model. The "
            "control stream likely needs either a different representation of length "
            "innovation, a joint latent state that also explains literal/copy hint "
            "choices, or an external source for the control tape. The direct observable "
            "state program over previous control and remaining length is closed under "
            "this evidence.",
            "",
            "## Reproducible Artifacts",
            "",
            "- [01_stateful_control_program_gate.py](../scripts/01_stateful_control_program_gate.py)",
            "- [01_stateful_control_program_gate.json](test_results/01_stateful_control_program_gate.json)",
            "- [01_stateful_control_program_gate.md](test_results/01_stateful_control_program_gate.md)",
            "- [02_compile_final_stateful_control_program_audit.py](../scripts/02_compile_final_stateful_control_program_audit.py)",
        ]
    )

    OUT.write_text("\n".join(lines) + "\n")
    print(
        json.dumps(
            {
                "classification": result["classification"],
                "best_model": best_name,
                "promoted_models": result["decision"]["promoted_models"],
                "generator_promoted": result["decision"]["generator_promoted"],
                "report": str(OUT.relative_to(ROOT)),
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
