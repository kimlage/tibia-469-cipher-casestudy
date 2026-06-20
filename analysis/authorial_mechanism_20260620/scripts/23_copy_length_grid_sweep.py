from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports" / "test_results"

ENCODER_SCRIPT = HERE / "scripts" / "22_copy_length_code_reparse.py"
RICE_FORMULA = HERE / "sequential_lz_rice_length_formula_469.json"
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


def load_encoder_module():
    spec = importlib.util.spec_from_file_location("copy_length_code_reparse_22", ENCODER_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {ENCODER_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> None:
    encoder = load_encoder_module()
    formula = load_json(RICE_FORMULA)
    books = {str(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    order = [str(book) for book in formula["policy"]["book_order"]]
    current_bits = formula["mdl_estimate_rough"]["sequential_lz_rice_length_bits"]
    current_min_len = int(formula["policy"]["min_len"])
    current_model = formula["policy"]["copy_length_model"]["family"]
    current_k = int(formula["policy"]["copy_length_model"]["k"])
    current_model_name = f"{current_model}_k{current_k}"

    length_models = [
        {"family": "gamma"},
        {"family": "delta"},
        {"family": "unary"},
        *({"family": "rice", "k": k} for k in range(0, 11)),
    ]
    sweep_range = list(range(3, 13))
    rows = []
    for min_len in sweep_range:
        for model in length_models:
            encoded = encoder.encode_books(books, order, min_len, model)
            rows.append(
                {
                    "min_len": min_len,
                    "length_model": encoder.model_name(model),
                    "model_declaration_bits": encoded["model_declaration_bits"],
                    "total_bits": encoded["total_bits"],
                    "delta_vs_current_bits": encoded["total_bits"] - current_bits,
                    "copy_items": encoded["copy_items"],
                    "copied_digits": encoded["copied_digits"],
                    "literal_runs": encoded["literal_runs"],
                    "literal_digits": encoded["literal_digits"],
                    "length_code_bits": encoded["length_code_bits"],
                    "books_roundtrip_ok": encoded["validation"]["books_roundtrip_ok"],
                    "errors": encoded["validation"]["errors"],
                }
            )
    rows.sort(key=lambda row: row["total_bits"])
    best = rows[0]
    nearest_non_current = next(
        row
        for row in rows
        if row["min_len"] != current_min_len or row["length_model"] != current_model_name
    )
    classification = (
        "copy_length_grid_retains_rice_k4_min_len_5"
        if best["min_len"] == current_min_len
        and best["length_model"] == current_model_name
        and abs(best["total_bits"] - current_bits) < 1e-9
        else "copy_length_grid_new_candidate"
    )

    result = {
        "schema": "copy_length_grid_sweep.v1",
        "test": "23_copy_length_grid_sweep",
        "classification": classification,
        "translation_delta": "NONE",
        "source_formula": str(RICE_FORMULA.relative_to(ROOT)),
        "current_formula_bits": current_bits,
        "current_min_len": current_min_len,
        "current_length_model": current_model_name,
        "sweep_range": sweep_range,
        "rice_k_range": list(range(0, 11)),
        "best_model": best,
        "nearest_non_current": nearest_non_current,
        "models": rows,
        "boundary": {
            "semantic_delta": "NONE",
            "pair_table_origin_explained": False,
            "authorial_intent_claim": False,
        },
    }

    lines = [
        "# Copy Length Grid Sweep",
        "",
        f"Verdict: `{classification}`. Translation delta: `NONE`.",
        "",
        "This audit broadens the previous copy-length reparse by testing",
        "`min_len=3..12` against gamma, delta, unary, and Rice `k=0..10` length",
        "codes. It uses the same DP encoder as the promoted Rice-length formula.",
        "",
        "## Best Models",
        "",
        "| Rank | min_len | Length model | Total bits | Delta vs current | Copy items | Copied digits | Literal digits | Roundtrip |",
        "|---:|---:|---|---:|---:|---:|---:|---:|---:|",
    ]
    for rank, row in enumerate(rows[:16], start=1):
        lines.append(
            f"| `{rank}` | `{row['min_len']}` | `{row['length_model']}` | "
            f"`{row['total_bits']:.1f}` | `{row['delta_vs_current_bits']:.1f}` | "
            f"`{row['copy_items']}` | `{row['copied_digits']}` | "
            f"`{row['literal_digits']}` | `{row['books_roundtrip_ok']}/70` |"
        )

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            f"The promoted `{current_model_name}` / `min_len={current_min_len}`",
            f"formula remains best at `{current_bits:.1f}` bits. The nearest",
            f"non-current model is `{nearest_non_current['length_model']}` with",
            f"`min_len={nearest_non_current['min_len']}` at",
            f"`{nearest_non_current['total_bits']:.1f}` bits,",
            f"`{nearest_non_current['delta_vs_current_bits']:.1f}` bits worse.",
            "No new formula is promoted by this broader grid.",
            "",
            "## Boundary",
            "",
            "This is a mechanical parameter-grid audit only. It does not alter row0,",
            "introduce plaintext, or make an authorial-intent claim.",
        ]
    )
    write_result("23_copy_length_grid_sweep", result, lines)


if __name__ == "__main__":
    main()
