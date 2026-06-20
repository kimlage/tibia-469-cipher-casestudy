from __future__ import annotations

import json
import math
import random
from collections import Counter
from pathlib import Path
from statistics import mean, pstdev


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports" / "test_results"

CURRENT_FORMULA = HERE / "sequential_lz_rice_literal_length_formula_469.json"
OUT_FORMULA = HERE / "sequential_lz_literal_payload_formula_469.json"

LOG2_10 = math.log2(10)
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


def literal_payload_stream(formula: dict) -> str:
    parts = []
    for book in map(str, formula["policy"]["book_order"]):
        for op in formula["book_recipes"][book]["ops"]:
            if op["type"] == "literal":
                parts.append(op["text"])
    return "".join(parts)


def adaptive_dirichlet_bits(stream: str, alpha: int) -> float:
    counts = {digit: 0 for digit in DIGITS}
    total = 0
    bits = 0.0
    for digit in stream:
        probability = (counts[digit] + alpha) / (total + len(DIGITS) * alpha)
        bits += -math.log2(probability)
        counts[digit] += 1
        total += 1
    return bits


def static_entropy_bits(stream: str) -> float:
    counts = Counter(stream)
    total = len(stream)
    return -sum(count * math.log2(count / total) for count in counts.values())


def best_adaptive_model(stream: str, alpha_range: range) -> dict:
    uniform_bits = len(stream) * LOG2_10
    rows = []
    for alpha in alpha_range:
        payload_bits = adaptive_dirichlet_bits(stream, alpha)
        model_bits = gamma_bits(alpha + 1)
        rows.append(
            {
                "model": f"adaptive_dirichlet_alpha_{alpha}",
                "family": "adaptive_dirichlet_integer_alpha",
                "alpha": alpha,
                "payload_bits": payload_bits,
                "model_declaration_bits": model_bits,
                "payload_delta_vs_uniform_bits": payload_bits + model_bits - uniform_bits,
                "decodable": True,
            }
        )
    rows.sort(key=lambda row: row["payload_delta_vs_uniform_bits"])
    return rows[0]


def random_uniform_controls(length: int, alpha_range: range, observed_delta: float, runs: int) -> dict:
    rng = random.Random(469270)
    values = []
    best_alphas = []
    for _run in range(runs):
        stream = "".join(str(rng.randrange(10)) for _ in range(length))
        best = best_adaptive_model(stream, alpha_range)
        values.append(best["payload_delta_vs_uniform_bits"])
        best_alphas.append(best["alpha"])
    return {
        "runs": runs,
        "min_delta_bits": min(values),
        "mean_delta_bits": mean(values),
        "pstdev_delta_bits": pstdev(values) if len(values) > 1 else 0.0,
        "max_delta_bits": max(values),
        "count_le_observed": sum(value <= observed_delta for value in values),
        "best_alpha_histogram": dict(sorted(Counter(best_alphas).items())),
    }


def validate_formula(formula: dict) -> dict:
    emitted = ""
    errors = []
    for book in map(str, formula["policy"]["book_order"]):
        parts = []
        for op in formula["book_recipes"][book]["ops"]:
            if op["type"] == "literal":
                chunk = op["text"]
            elif op["type"] == "copy":
                chunk = emitted[op["source_pos"] : op["source_pos"] + op["length"]]
                if len(chunk) != op["length"]:
                    errors.append({"book": book, "type": "short_copy", "op": op})
            else:
                errors.append({"book": book, "type": "bad_op", "op": op})
                chunk = ""
            parts.append(chunk)
            emitted += chunk
        if len("".join(parts)) != formula["book_recipes"][book]["length"]:
            errors.append({"book": book, "type": "length_mismatch"})
        emitted += "#"
    return {"book_count": len(formula["policy"]["book_order"]), "errors": errors}


def main() -> None:
    formula = load_json(CURRENT_FORMULA)
    current_bits = formula["mdl_estimate_rough"]["sequential_lz_rice_literal_length_bits"]
    stream = literal_payload_stream(formula)
    literal_digits = len(stream)
    uniform_payload_bits = literal_digits * LOG2_10
    alpha_range = range(1, 65)
    best_adaptive = best_adaptive_model(stream, alpha_range)
    adaptive_total_bits = current_bits + best_adaptive["payload_delta_vs_uniform_bits"]

    entropy_bits = static_entropy_bits(stream)
    counts = Counter(stream)
    static_counts_model_bits = gamma_bits(literal_digits + 1) + sum(
        gamma_bits(counts.get(digit, 0) + 1) for digit in DIGITS
    )
    models = [
        {
            "model": "uniform_decimal_payload",
            "payload_bits": uniform_payload_bits,
            "model_declaration_bits": 0,
            "payload_delta_vs_uniform_bits": 0.0,
            "total_bits": current_bits,
            "decodable": True,
        },
        {
            **best_adaptive,
            "total_bits": adaptive_total_bits,
        },
        {
            "model": "static_literal_histogram_oracle_no_table",
            "payload_bits": entropy_bits,
            "model_declaration_bits": 0,
            "payload_delta_vs_uniform_bits": entropy_bits - uniform_payload_bits,
            "total_bits": current_bits + entropy_bits - uniform_payload_bits,
            "decodable": False,
        },
        {
            "model": "static_literal_histogram_with_counts",
            "payload_bits": entropy_bits,
            "model_declaration_bits": static_counts_model_bits,
            "payload_delta_vs_uniform_bits": entropy_bits + static_counts_model_bits - uniform_payload_bits,
            "total_bits": current_bits + entropy_bits + static_counts_model_bits - uniform_payload_bits,
            "decodable": True,
        },
    ]
    models.sort(key=lambda row: row["total_bits"])
    controls = {
        "random_uniform_literal_payloads": random_uniform_controls(
            literal_digits,
            alpha_range,
            best_adaptive["payload_delta_vs_uniform_bits"],
            runs=200,
        )
    }
    promoted = (
        best_adaptive["payload_delta_vs_uniform_bits"] < 0
        and controls["random_uniform_literal_payloads"]["count_le_observed"] == 0
    )
    classification = (
        "controlled_literal_payload_adaptive_improvement"
        if promoted
        else "literal_payload_model_not_promoted"
    )

    if promoted:
        out = {
            "schema": "sequential_lz_literal_payload_formula.v1",
            "classification": classification,
            "translation_delta": "NONE",
            "source_baseline_formula": str(CURRENT_FORMULA.relative_to(ROOT)),
            "scope": "70 raw digit books in numeric order",
            "policy": {
                **formula["policy"],
                "literal_payload_model": {
                    "family": "adaptive_dirichlet_integer_alpha",
                    "alpha": best_adaptive["alpha"],
                    "alphabet": DIGITS,
                    "model_declaration_bits": best_adaptive["model_declaration_bits"],
                },
            },
            "book_recipes": formula["book_recipes"],
            "mdl_estimate_rough": {
                **formula["mdl_estimate_rough"],
                "sequential_lz_literal_payload_bits": adaptive_total_bits,
                "previous_sequential_lz_rice_literal_length_bits": current_bits,
                "gain_vs_previous_rice_literal_length_bits": current_bits - adaptive_total_bits,
                "uniform_literal_payload_bits": uniform_payload_bits,
                "adaptive_literal_payload_bits": best_adaptive["payload_bits"],
                "literal_payload_model_declaration_bits": best_adaptive["model_declaration_bits"],
            },
            "literal_payload_digit_histogram": dict(sorted(counts.items())),
            "validation": {
                **formula["validation"],
                "literal_payload_roundtrip_audit": validate_formula(formula),
            },
            "boundary": formula["boundary"],
        }
        OUT_FORMULA.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    result = {
        "schema": "literal_payload_model_search.v1",
        "test": "27_literal_payload_model_search",
        "classification": classification,
        "translation_delta": "NONE",
        "source_formula": str(CURRENT_FORMULA.relative_to(ROOT)),
        "output_formula": str(OUT_FORMULA.relative_to(ROOT)) if promoted else None,
        "current_formula_bits": current_bits,
        "literal_digits": literal_digits,
        "literal_digit_histogram": dict(sorted(counts.items())),
        "best_decodable_model": best_adaptive,
        "models": models,
        "controls": controls,
        "boundary": formula["boundary"],
    }

    lines = [
        "# Literal Payload Model Search",
        "",
        f"Verdict: `{classification}`. Translation delta: `NONE`.",
        "",
        "This audit keeps the current sequential LZ recipe fixed and tests the",
        "payload cost of literal digits. Length coding, source addresses, book",
        "order, and copy operations are unchanged; only the code for literal",
        "payload digits is varied.",
        "",
        "## Payload Models",
        "",
        "| Model | Payload bits | Model bits | Total bits | Delta vs current | Decodable |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in models:
        lines.append(
            f"| `{row['model']}` | `{row['payload_bits']:.1f}` | "
            f"`{row['model_declaration_bits']}` | `{row['total_bits']:.1f}` | "
            f"`{row['total_bits'] - current_bits:.1f}` | `{row['decodable']}` |"
        )

    control = controls["random_uniform_literal_payloads"]
    lines.extend(
        [
            "",
            "## Controls",
            "",
            "| Control | Runs | Min delta | Mean delta | Count <= observed |",
            "|---|---:|---:|---:|---:|",
            f"| `random_uniform_literal_payloads` | `{control['runs']}` | "
            f"`{control['min_delta_bits']:.1f}` | `{control['mean_delta_bits']:.1f}` | "
            f"`{control['count_le_observed']}` |",
            "",
            "## Interpretation",
            "",
            f"The best decodable payload model is adaptive Dirichlet with",
            f"`alpha={best_adaptive['alpha']}`. After charging",
            f"`{best_adaptive['model_declaration_bits']}` bits to declare alpha,",
            f"it improves the current formula by",
            f"`{-best_adaptive['payload_delta_vs_uniform_bits']:.1f}` bits.",
            "The static histogram oracle is cheaper but not promoted because it",
            "omits a decodable table; the charged static table is worse.",
            "",
            "## Boundary",
            "",
            "This is a mechanical literal-payload coding audit only. It does not",
            "alter row0, introduce plaintext, or make an authorial-intent claim.",
        ]
    )
    write_result("27_literal_payload_model_search", result, lines)


if __name__ == "__main__":
    main()
