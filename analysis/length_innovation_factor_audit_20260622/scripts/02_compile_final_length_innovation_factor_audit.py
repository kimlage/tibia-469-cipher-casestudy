#!/usr/bin/env python3
"""Compile final report for the length innovation factor audit."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
FRONT = ROOT / "analysis" / "length_innovation_factor_audit_20260622"
TEST_RESULTS = FRONT / "reports" / "test_results"
RESULT_PATH = TEST_RESULTS / "01_length_innovation_factor_gate.json"
OUT = FRONT / "reports" / "final_length_innovation_factor_audit.md"


def bits(value: float) -> str:
    return f"{value:.3f}"


def main() -> None:
    result = json.loads(RESULT_PATH.read_text())
    if result.get("translation_delta") != "NONE":
        raise SystemExit("translation delta must remain NONE")
    if result.get("case_reopened") or result.get("plaintext_claim"):
        raise SystemExit("audit must not reopen case or make plaintext claims")

    summary = result["summary"]
    decision = result["decision"]
    best_name = decision["best_residual_feature"]
    best = result["feature_results"][best_name]

    lines = [
        "# Final Length Innovation Factor Audit",
        "",
        "Status: `analysis_only`",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Question",
        "",
        "After the exact `type:length` state program failed, this audit asks whether the "
        "length dependency has the wrong representation. It factors each exact length "
        "into a coarse `type:length_bucket` stream plus a within-bucket residual "
        "innovation tape.",
        "",
        "This is a mechanical representation audit only. It does not test plaintext, "
        "translation, fan glosses, semantics, or row0 origin.",
        "",
        "## Factorization Result",
        "",
        f"- Rows: `{summary['rows']}`.",
        f"- Independent `op_type + exact_length`: `{bits(summary['independent_type_exact_length_bits'])}` bits.",
        f"- `type:length_bucket` stream: `{bits(summary['type_bucket_stream_bits'])}` bits.",
        f"- Uniform within-bucket residual tape: `{bits(summary['residual_uniform_bits'])}` bits.",
        f"- Factorized total: `{bits(summary['factorized_type_bucket_residual_bits'])}` bits.",
        f"- Saving from factorization: `{bits(summary['factorized_saving_bits'])}` bits.",
        "",
        "The factorization is useful because it reduces the declared exact-length "
        "dependency after paying the coarse stream. It is not a generator because it "
        "still pays the residual tape.",
        "",
        "## Residual Codec Result",
        "",
        f"- Best residual feature: `{best_name}`.",
        f"- Best residual bits over prefix/suffix cutoffs: `{bits(best['observed_model_bits'])}`.",
        f"- Saving vs uniform residual: `{bits(best['observed_saving_bits'])}` bits.",
        f"- Shuffled-control p95 saving: `{bits(best['random_saving_p95'])}` bits.",
        f"- Top1 residual hits: `{best['observed_top1_hits']}/{best['observed_total_rows']}`.",
        f"- Promoted residual features: `{decision['promoted_residual_features']}`.",
        "",
        "No residual codec is promoted. The best feature, `type_bucket`, is only weak "
        "relative to bad same-bucket residual controls and remains worse than uniform "
        "within-bucket residual declaration.",
        "",
        "## Decision",
        "",
        "- `length_innovation_factorization_clue_residual_external`.",
        "- Exact length should now be tracked as two dependencies: coarse "
        "`type:length_bucket` control and a fine within-bucket residual tape.",
        "- The fine residual tape is the unresolved length-innovation blocker.",
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
        "- [01_length_innovation_factor_gate.py](../scripts/01_length_innovation_factor_gate.py)",
        "- [01_length_innovation_factor_gate.json](test_results/01_length_innovation_factor_gate.json)",
        "- [01_length_innovation_factor_gate.md](test_results/01_length_innovation_factor_gate.md)",
        "- [02_compile_final_length_innovation_factor_audit.py](../scripts/02_compile_final_length_innovation_factor_audit.py)",
    ]
    OUT.write_text("\n".join(lines) + "\n")
    print(
        json.dumps(
            {
                "classification": result["classification"],
                "factorized_saving_bits": summary["factorized_saving_bits"],
                "best_residual_feature": best_name,
                "promoted_residual_features": decision["promoted_residual_features"],
                "report": str(OUT.relative_to(ROOT)),
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
