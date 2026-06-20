from __future__ import annotations

import json
import math
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports" / "test_results"

FORMULA = HERE / "sequential_lz_literal_copy_repair_formula_469.json"
DIGITS = [str(i) for i in range(10)]


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_result(name: str, result: dict, lines: list[str]) -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / f"{name}.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (REPORTS / f"{name}.md").write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def gamma_bits(value: int) -> int:
    if value <= 0:
        raise ValueError(value)
    return 2 * int(math.floor(math.log2(value))) + 1


def adaptive_payload_bits(stream: str, alpha: int) -> float:
    counts = {digit: 0 for digit in DIGITS}
    total = 0
    bits = 0.0
    for digit in stream:
        probability = (counts[digit] + alpha) / (total + len(DIGITS) * alpha)
        bits += -math.log2(probability)
        counts[digit] += 1
        total += 1
    return bits


def literal_payload_stream(formula: dict) -> str:
    return "".join(
        op["text"]
        for book in map(str, formula["policy"]["book_order"])
        for op in formula["book_recipes"][book]["ops"]
        if op["type"] == "literal"
    )


def main() -> None:
    formula = load_json(FORMULA)
    current_bits = formula["mdl_estimate_rough"]["sequential_lz_literal_copy_repair_bits"]
    current_alpha = int(formula["policy"]["literal_payload_model"]["alpha"])
    stream = literal_payload_stream(formula)
    rows = []
    for alpha in range(1, 129):
        payload_bits = adaptive_payload_bits(stream, alpha)
        declaration_bits = gamma_bits(alpha + 1)
        rows.append(
            {
                "alpha": alpha,
                "payload_bits": payload_bits,
                "model_declaration_bits": declaration_bits,
                "payload_plus_model_bits": payload_bits + declaration_bits,
                "delta_vs_current_alpha_bits": payload_bits
                + declaration_bits
                - (adaptive_payload_bits(stream, current_alpha) + gamma_bits(current_alpha + 1)),
            }
        )
    rows.sort(key=lambda row: row["payload_plus_model_bits"])
    best = rows[0]
    classification = (
        "post_repair_payload_alpha_retains_14"
        if best["alpha"] == current_alpha
        else "post_repair_payload_alpha_candidate"
    )

    result = {
        "schema": "post_repair_payload_alpha_sweep.v1",
        "test": "30_post_repair_payload_alpha_sweep",
        "classification": classification,
        "translation_delta": "NONE",
        "source_formula": str(FORMULA.relative_to(ROOT)),
        "current_formula_bits": current_bits,
        "current_alpha": current_alpha,
        "literal_digits": len(stream),
        "literal_digit_histogram": dict(sorted(Counter(stream).items())),
        "best_alpha": best,
        "models": rows,
        "boundary": formula["boundary"],
    }

    lines = [
        "# Post-Repair Payload Alpha Sweep",
        "",
        f"Verdict: `{classification}`. Translation delta: `NONE`.",
        "",
        "This audit retests the adaptive literal-payload `alpha` parameter after",
        "the one-step literal-to-copy repair changed the literal payload stream.",
        "The recipe, copy model, literal-run length model, and address model are",
        "fixed; only the declared integer alpha is swept.",
        "",
        "## Best Alpha Values",
        "",
        "| Rank | Alpha | Payload bits | Model bits | Payload+model bits | Delta vs current alpha |",
        "|---:|---:|---:|---:|---:|---:|",
    ]
    for rank, row in enumerate(rows[:16], start=1):
        lines.append(
            f"| `{rank}` | `{row['alpha']}` | `{row['payload_bits']:.1f}` | "
            f"`{row['model_declaration_bits']}` | `{row['payload_plus_model_bits']:.1f}` | "
            f"`{row['delta_vs_current_alpha_bits']:.1f}` |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            f"The current formula uses `alpha={current_alpha}`. The best swept value",
            f"is `alpha={best['alpha']}` with payload-plus-model cost",
            f"`{best['payload_plus_model_bits']:.1f}` bits. No formula is",
            "promoted if the current alpha remains best.",
            "",
            "## Boundary",
            "",
            "This is a mechanical parameter audit only. It does not alter row0,",
            "introduce plaintext, or make an authorial-intent claim.",
        ]
    )
    write_result("30_post_repair_payload_alpha_sweep", result, lines)


if __name__ == "__main__":
    main()
