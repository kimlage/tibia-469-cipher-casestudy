#!/usr/bin/env python3
"""Compile final shared innovation tape audit report."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
FRONT = ROOT / "analysis" / "shared_innovation_tape_audit_20260622"
TEST_RESULTS = FRONT / "reports" / "test_results"
RESULT_PATH = TEST_RESULTS / "01_shared_literal_length_tape_gate.json"
OUT = FRONT / "reports" / "final_shared_innovation_tape_audit.md"


def bits(value: float) -> str:
    return f"{value:.3f}"


def main() -> None:
    result = json.loads(RESULT_PATH.read_text())
    if result.get("translation_delta") != "NONE":
        raise SystemExit("translation delta must remain NONE")
    if result.get("case_reopened") or result.get("plaintext_claim"):
        raise SystemExit("audit must not reopen case or make plaintext claims")

    summary = result["summary"]
    lines = [
        "# Final Shared Innovation Tape Audit",
        "",
        "Status: `analysis_only`",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Question",
        "",
        "The length factor audit left a fine within-bucket residual tape external. This "
        "audit asks whether the already-paid literal innovation tape can also drive "
        "those length residuals, using one literal-tape digit per operation plus a "
        "small prefix-selected arithmetic policy.",
        "",
        "The test is mechanical only. It does not test plaintext, translation, fan "
        "glosses, semantics, or row0 origin.",
        "",
        "## Result",
        "",
        f"- Literal tape digits: `{result['inputs']['literal_tape_digits']}`.",
        f"- Length residual events: `{result['inputs']['residual_events']}`.",
        f"- Policies tested: `{result['inputs']['policies_tested']}`.",
        f"- Observed uniform residual bits over suffix tests: `{bits(summary['observed_total_uniform_bits'])}`.",
        f"- Observed correction bits after literal-tape prediction: `{bits(summary['observed_total_correction_bits'])}`.",
        f"- Saving vs uniform residual: `{bits(summary['observed_saving_vs_uniform_bits'])}` bits.",
        f"- Shuffled same-multiset tape p95 saving: `{bits(summary['random_saving_p95'])}` bits.",
        f"- Hits: `{summary['observed_total_hits']}/{summary['observed_total_rows']}`.",
        f"- Selected policies: `{summary['selected_policy_counts']}`.",
        "",
        "The literal tape is not strong enough to replace the length residual tape: "
        "the observed policy is still `36.755` bits worse than uniform residual "
        "declaration. It is, however, less bad than shuffled same-multiset tapes "
        "after identical prefix selection (`-36.755` vs p95 `-56.770`), so it is "
        "retained only as a weak shared-innovation clue.",
        "",
        "## Decision",
        "",
        "- `WEAK_SHARED_INNOVATION_TAPE`.",
        "- The literal innovation tape is not promoted as a shared length-residual "
        "driver.",
        "- The within-bucket length residual tape remains external.",
        "- `row0`, translation, plaintext, and the compression bound remain unchanged.",
        "",
        "## Remaining External Fields",
        "",
        "- `type:length_bucket` control stream",
        "- within-bucket length residual innovation tape",
        "- literal innovation tape payload and schedule",
        "- copy-hint rank stream",
        "- seed books `0..9`",
        "- `row0`",
        "",
        "## Reproducible Artifacts",
        "",
        "- [01_shared_literal_length_tape_gate.py](../scripts/01_shared_literal_length_tape_gate.py)",
        "- [01_shared_literal_length_tape_gate.json](test_results/01_shared_literal_length_tape_gate.json)",
        "- [01_shared_literal_length_tape_gate.md](test_results/01_shared_literal_length_tape_gate.md)",
        "- [02_compile_final_shared_innovation_tape_audit.py](../scripts/02_compile_final_shared_innovation_tape_audit.py)",
    ]
    OUT.write_text("\n".join(lines) + "\n")
    print(
        json.dumps(
            {
                "classification": result["classification"],
                "observed_saving": summary["observed_saving_vs_uniform_bits"],
                "random_p95": summary["random_saving_p95"],
                "report": str(OUT.relative_to(ROOT)),
                "status": result["decision"]["status"],
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
