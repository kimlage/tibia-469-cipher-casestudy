from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports" / "test_results"

LITERAL_ENCODER_SCRIPT = HERE / "scripts" / "25_literal_run_length_code_reparse.py"
CURRENT_FORMULA = HERE / "sequential_lz_rice_literal_length_formula_469.json"
OUT_FORMULA = HERE / "sequential_lz_joint_length_formula_469.json"
BOOKS_DIGITS = ROOT / "analysis/audit_20260609/books_digits.json"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_result(name: str, result: dict, lines: list[str]) -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / f"{name}.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (REPORTS / f"{name}.md").write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def load_literal_encoder_module():
    spec = importlib.util.spec_from_file_location("literal_run_length_code_reparse_25", LITERAL_ENCODER_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {LITERAL_ENCODER_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def make_models() -> list[dict]:
    return [
        {"family": "gamma"},
        {"family": "delta"},
        *({"family": "rice", "k": k} for k in range(0, 9)),
    ]


def maybe_emit_formula(best_encoded: dict, current_formula: dict, current_bits: float) -> None:
    out = {
        "schema": "sequential_lz_joint_length_formula.v1",
        "classification": "controlled_joint_length_code_improvement",
        "translation_delta": "NONE",
        "source_baseline_formula": str(CURRENT_FORMULA.relative_to(ROOT)),
        "scope": "70 raw digit books in numeric order",
        "policy": {
            "book_order": best_encoded["book_order"],
            "copy_source": "previously_emitted_digits_in_prior_books_or_current_book_prefix",
            "parse": "dynamic_programming_min_cost_under_joint_copy_and_literal_length_codes",
            "min_len": best_encoded["min_len"],
            "copy_length_model": best_encoded["copy_length_model"],
            "literal_run_length_model": best_encoded["literal_length_model"],
            "cost_model": "gamma(book_count)+gamma(book_lengths)+copy_length_model_declaration+literal_length_model_declaration+literal_run_ops+absolute_source_copy_ops",
        },
        "book_recipes": best_encoded["recipes"],
        "mdl_estimate_rough": {
            "sequential_lz_joint_length_bits": best_encoded["total_bits"],
            "previous_sequential_lz_rice_literal_length_bits": current_bits,
            "gain_vs_previous_rice_literal_length_bits": current_bits - best_encoded["total_bits"],
            "model_declaration_bits": best_encoded["model_declaration_bits"],
            "copy_model_declaration_bits": best_encoded["copy_model_declaration_bits"],
            "literal_model_declaration_bits": best_encoded["literal_model_declaration_bits"],
            "literal_bits": best_encoded["literal_bits"],
            "copy_bits": best_encoded["copy_bits"],
            "copy_length_code_bits": best_encoded["copy_length_code_bits"],
            "literal_length_code_bits": best_encoded["literal_length_code_bits"],
            "copy_address_bits": best_encoded["address_bits"],
            "literal_digits": best_encoded["literal_digits"],
            "literal_runs": best_encoded["literal_runs"],
            "copy_items": best_encoded["copy_items"],
            "copied_digits": best_encoded["copied_digits"],
        },
        "copy_length_value_histogram": best_encoded["copy_length_value_histogram"],
        "literal_length_value_histogram": best_encoded["literal_length_value_histogram"],
        "validation": best_encoded["validation"],
        "boundary": current_formula["boundary"],
    }
    OUT_FORMULA.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    literal_encoder = load_literal_encoder_module()
    encoder = literal_encoder.load_encoder_module()
    current_formula = load_json(CURRENT_FORMULA)
    books = {str(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    order = [str(book) for book in current_formula["policy"]["book_order"]]
    current_bits = current_formula["mdl_estimate_rough"]["sequential_lz_rice_literal_length_bits"]
    current_min_len = int(current_formula["policy"]["min_len"])
    current_copy_model = current_formula["policy"]["copy_length_model"]
    current_literal_model = current_formula["policy"]["literal_run_length_model"]
    current_copy_name = encoder.model_name(current_copy_model)
    current_literal_name = encoder.model_name(current_literal_model)

    min_len_range = list(range(3, 8))
    copy_models = make_models()
    literal_models = make_models()
    rows = []
    encoded_by_key = {}
    for min_len in min_len_range:
        for copy_model in copy_models:
            for literal_model in literal_models:
                encoded = literal_encoder.encode_books(
                    books,
                    order,
                    min_len,
                    copy_model,
                    literal_model,
                    encoder,
                )
                key = (
                    min_len,
                    encoded["copy_length_model_name"],
                    encoded["literal_length_model_name"],
                )
                encoded_by_key[key] = encoded
                rows.append(
                    {
                        "min_len": min_len,
                        "copy_length_model": encoded["copy_length_model_name"],
                        "literal_length_model": encoded["literal_length_model_name"],
                        "model_declaration_bits": encoded["model_declaration_bits"],
                        "total_bits": encoded["total_bits"],
                        "delta_vs_current_bits": encoded["total_bits"] - current_bits,
                        "copy_items": encoded["copy_items"],
                        "copied_digits": encoded["copied_digits"],
                        "literal_runs": encoded["literal_runs"],
                        "literal_digits": encoded["literal_digits"],
                        "copy_length_code_bits": encoded["copy_length_code_bits"],
                        "literal_length_code_bits": encoded["literal_length_code_bits"],
                        "books_roundtrip_ok": encoded["validation"]["books_roundtrip_ok"],
                        "errors": encoded["validation"]["errors"],
                    }
                )

    rows.sort(key=lambda row: row["total_bits"])
    best = rows[0]
    current_row = next(
        row
        for row in rows
        if row["min_len"] == current_min_len
        and row["copy_length_model"] == current_copy_name
        and row["literal_length_model"] == current_literal_name
    )
    best_encoded = encoded_by_key[
        (best["min_len"], best["copy_length_model"], best["literal_length_model"])
    ]

    promoted = (
        best["books_roundtrip_ok"] == len(order)
        and best["total_bits"] < current_bits
        and (
            best["min_len"] != current_min_len
            or best["copy_length_model"] != current_copy_name
            or best["literal_length_model"] != current_literal_name
        )
    )
    classification = (
        "controlled_joint_length_code_improvement"
        if promoted
        else "joint_length_grid_retains_rice_k4_literal_rice_k3_min_len_5"
    )
    if promoted:
        maybe_emit_formula(best_encoded, current_formula, current_bits)

    result = {
        "schema": "joint_length_code_grid_sweep.v1",
        "test": "26_joint_length_code_grid_sweep",
        "classification": classification,
        "translation_delta": "NONE",
        "source_formula": str(CURRENT_FORMULA.relative_to(ROOT)),
        "output_formula": str(OUT_FORMULA.relative_to(ROOT)) if promoted else None,
        "current_formula_bits": current_bits,
        "current_model": current_row,
        "best_model": best,
        "min_len_range": min_len_range,
        "copy_models": [encoder.model_name(model) for model in copy_models],
        "literal_models": [encoder.model_name(model) for model in literal_models],
        "models": rows,
        "boundary": current_formula["boundary"],
    }

    lines = [
        "# Joint Length Code Grid Sweep",
        "",
        f"Verdict: `{classification}`. Translation delta: `NONE`.",
        "",
        "This audit tests the interaction between copy-length and literal-run",
        "length codes under the same sequential LZ dynamic parse. It covers",
        "`min_len=3..7`, gamma/delta, and Rice `k=0..8` for both length",
        "families while keeping numeric book order and absolute source",
        "addresses fixed.",
        "",
        "## Best Joint Models",
        "",
        "| Rank | min_len | Copy length | Literal length | Model bits | Total bits | Delta vs current | Copy items | Literal runs | Literal digits | Roundtrip |",
        "|---:|---:|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for rank, row in enumerate(rows[:20], start=1):
        lines.append(
            f"| `{rank}` | `{row['min_len']}` | `{row['copy_length_model']}` | "
            f"`{row['literal_length_model']}` | `{row['model_declaration_bits']}` | "
            f"`{row['total_bits']:.1f}` | `{row['delta_vs_current_bits']:.1f}` | "
            f"`{row['copy_items']}` | `{row['literal_runs']}` | "
            f"`{row['literal_digits']}` | `{row['books_roundtrip_ok']}/70` |"
        )

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            f"The current formula uses `{current_copy_name}` copy lengths,",
            f"`{current_literal_name}` literal-run lengths, and",
            f"`min_len={current_min_len}` at `{current_bits:.1f}` bits.",
            f"The best joint-grid model is `{best['copy_length_model']}` /",
            f"`{best['literal_length_model']}` with `min_len={best['min_len']}`",
            f"at `{best['total_bits']:.1f}` bits, delta",
            f"`{best['delta_vs_current_bits']:.1f}`.",
            "",
            "## Boundary",
            "",
            "This is a mechanical length-code interaction audit only. It does not",
            "alter row0, introduce plaintext, or make an authorial-intent claim.",
        ]
    )
    write_result("26_joint_length_code_grid_sweep", result, lines)


if __name__ == "__main__":
    main()
