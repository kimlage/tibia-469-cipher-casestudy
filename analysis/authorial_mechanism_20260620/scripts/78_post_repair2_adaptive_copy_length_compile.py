from __future__ import annotations

import copy
import importlib.util
import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports" / "test_results"

FORMULA = HERE / "sequential_lz_digit_address_contextual_bounded_copy_length_minaddr_repair2_formula_469.json"
OUT_FORMULA = HERE / "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_minaddr_repair2_formula_469.json"
BOOKS_DIGITS = ROOT / "analysis/audit_20260609/books_digits.json"
SCORER = HERE / "scripts/71_minaddr_local_frontier.py"

CURRENT_TOTAL_KEY = "sequential_lz_digit_address_contextual_bounded_copy_length_minaddr_repair2_bits"
OUT_TOTAL_KEY = "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_minaddr_repair2_bits"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_result(name: str, result: dict, lines: list[str]) -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / f"{name}.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (REPORTS / f"{name}.md").write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def load_scorer_module():
    spec = importlib.util.spec_from_file_location("minaddr_frontier", SCORER)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load scorer module: {SCORER}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def gamma_bits(value: int) -> int:
    if value <= 0:
        raise ValueError(value)
    return 2 * int(math.floor(math.log2(value))) + 1


def collect_copy_length_rows(formula: dict, books: dict[str, str], scorer) -> list[dict]:
    min_len = int(formula["policy"]["min_len"])
    emitted = ""
    rows = []
    copy_id = 0

    for book in map(str, formula["policy"]["book_order"]):
        ops = formula["book_recipes"][book]["ops"]
        book_length = sum(int(op["length"]) for op in ops)
        book_parts = []
        position = 0
        for op_index, op in enumerate(ops):
            length = int(op["length"])
            remaining = book_length - position
            if op["type"] == "literal":
                chunk = op["text"]
            elif op["type"] == "copy":
                source_digit_pos = int(op["source_digit_pos"])
                max_length = min(remaining, len(emitted) - source_digit_pos)
                symbol_count = max_length - min_len + 1
                length_index = length - min_len
                truncated_bits = scorer.truncated_binary_bits(symbol_count, length_index)
                chunk = emitted[source_digit_pos : source_digit_pos + length]
                if len(chunk) != length:
                    raise RuntimeError((book, "short_copy", op_index, op))
                rows.append(
                    {
                        "copy_id": copy_id,
                        "book": book,
                        "op_index": op_index,
                        "target_digit_global": len(emitted),
                        "source_digit_pos": source_digit_pos,
                        "length": length,
                        "max_length": max_length,
                        "symbol_count": symbol_count,
                        "length_index": length_index,
                        "truncated_binary_bits": truncated_bits,
                    }
                )
                copy_id += 1
            else:
                raise ValueError(op)
            emitted += chunk
            book_parts.append(chunk)
            position += length
        if "".join(book_parts) != books[book]:
            raise RuntimeError(f"formula does not roundtrip book {book}")

    return rows


def adaptive_length_bits(rows: list[dict], alpha: int) -> tuple[float, list[dict]]:
    counts: dict[int, int] = {}
    total_bits = 0.0
    audit_rows = []
    for row in rows:
        legal = range(int(row["symbol_count"]))
        legal_observations = sum(counts.get(index, 0) for index in legal)
        denominator = legal_observations + alpha * int(row["symbol_count"])
        numerator = counts.get(int(row["length_index"]), 0) + alpha
        probability = numerator / denominator
        bits = -math.log2(probability)
        total_bits += bits
        audit_rows.append(
            {
                **row,
                "alpha": alpha,
                "adaptive_bits": bits,
                "delta_vs_truncated_bits": bits - float(row["truncated_binary_bits"]),
                "previous_legal_observations": legal_observations,
                "previous_same_length_observations": counts.get(int(row["length_index"]), 0),
            }
        )
        counts[int(row["length_index"])] = counts.get(int(row["length_index"]), 0) + 1
    return total_bits, audit_rows


def main() -> None:
    scorer = load_scorer_module()
    formula = load_json(FORMULA)
    books = {str(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    current_bits = float(formula["mdl_estimate_rough"][CURRENT_TOTAL_KEY])
    current_score = scorer.score_formula(formula, books)
    if current_score["validation"]["errors"]:
        raise RuntimeError(current_score["validation"])
    if abs(current_score["total_bits"] - current_bits) > 1e-6:
        raise RuntimeError((current_score["total_bits"], current_bits))

    rows = collect_copy_length_rows(formula, books, scorer)
    current_length_bits = sum(row["truncated_binary_bits"] for row in rows)
    if abs(current_length_bits - current_score["copy_length_code_bits"]) > 1e-6:
        raise RuntimeError((current_length_bits, current_score["copy_length_code_bits"]))

    current_model_declaration_bits = int(formula["mdl_estimate_rough"]["copy_model_declaration_bits"])
    model_rows = []
    audit_by_alpha = {}
    for alpha in range(1, 33):
        length_bits, audit_rows = adaptive_length_bits(rows, alpha)
        declaration_bits = current_model_declaration_bits + gamma_bits(alpha + 1)
        total_bits = (
            current_bits
            - current_length_bits
            + length_bits
            + declaration_bits
            - current_model_declaration_bits
        )
        model_rows.append(
            {
                "alpha": alpha,
                "adaptive_copy_length_bits": length_bits,
                "model_declaration_bits": declaration_bits,
                "total_bits": total_bits,
                "delta_vs_current_bits": total_bits - current_bits,
                "component_delta_bits": length_bits - current_length_bits,
            }
        )
        audit_by_alpha[alpha] = audit_rows

    model_rows.sort(key=lambda row: row["total_bits"])
    best = model_rows[0]
    promoted = best["total_bits"] < current_bits - 1e-9
    classification = (
        "controlled_post_repair2_adaptive_copy_length_improvement"
        if promoted
        else "post_repair2_adaptive_copy_length_not_promoted"
    )

    best_audit_rows = audit_by_alpha[int(best["alpha"])]
    top_savings = sorted(best_audit_rows, key=lambda row: row["delta_vs_truncated_bits"])[:20]
    top_costs = sorted(best_audit_rows, key=lambda row: row["delta_vs_truncated_bits"], reverse=True)[:20]

    if promoted:
        out = copy.deepcopy(formula)
        out["schema"] = "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_minaddr_repair2_formula.v1"
        out["classification"] = classification
        out["source_baseline_formula"] = str(FORMULA.relative_to(ROOT))
        out["policy"]["copy_length_model"] = {
            "alpha": int(best["alpha"]),
            "family": "adaptive_bounded_length_index_after_source_address",
            "legal_symbol_count": "max_length - min_len + 1 after source address is decoded",
            "model_declaration_bits": int(best["model_declaration_bits"]),
            "replaces": formula["policy"]["copy_length_model"],
            "smoothing": "global prior over copy length index restricted to currently legal indices",
        }
        out["policy"]["cost_model"] = (
            out["policy"]["cost_model"]
            + "+adaptive_bounded_copy_length_index_after_source_address"
        )
        out["mdl_estimate_rough"] = {
            **out["mdl_estimate_rough"],
            OUT_TOTAL_KEY: best["total_bits"],
            "previous_sequential_lz_digit_address_contextual_bounded_copy_length_minaddr_repair2_bits": current_bits,
            "gain_vs_previous_post_repair2_bits": current_bits - best["total_bits"],
            "previous_copy_length_code_bits": current_length_bits,
            "bounded_adaptive_copy_length_bits": best["adaptive_copy_length_bits"],
            "copy_length_code_bits": best["adaptive_copy_length_bits"],
            "copy_model_declaration_bits": int(best["model_declaration_bits"]),
            "copy_bits": current_score["copy_address_bits"] + best["adaptive_copy_length_bits"],
            "copy_address_bits": current_score["copy_address_bits"],
            "fixed_bits": float(formula["mdl_estimate_rough"]["fixed_bits"])
            - current_model_declaration_bits
            + int(best["model_declaration_bits"]),
        }
        out["validation"] = {
            **out["validation"],
            "bounded_adaptive_copy_length_roundtrip_audit": current_score["validation"],
            "bounded_adaptive_copy_length_copy_items": len(rows),
        }
        OUT_FORMULA.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    result = {
        "schema": "post_repair2_adaptive_copy_length_compile.v1",
        "test": "78_post_repair2_adaptive_copy_length_compile",
        "classification": classification,
        "translation_delta": "NONE",
        "source_formula": str(FORMULA.relative_to(ROOT)),
        "output_formula": str(OUT_FORMULA.relative_to(ROOT)) if promoted else None,
        "current_formula_bits": current_bits,
        "current_score_audit": current_score,
        "current_copy_length_code_bits": current_length_bits,
        "current_copy_model_declaration_bits": current_model_declaration_bits,
        "best_model": best,
        "models": model_rows,
        "copy_length_rows": rows,
        "best_alpha_audit_rows": best_audit_rows,
        "top_savings": top_savings,
        "top_costs": top_costs,
        "promotion_rule": (
            "promote only if an adaptive bounded copy-length ledger beats truncated "
            "binary after charged alpha declaration bits while preserving 70/70 roundtrip"
        ),
        "boundary": formula["boundary"],
    }

    lines = [
        "# Post-Repair2 Adaptive Copy-Length Compile",
        "",
        f"Verdict: `{classification}`. Translation delta: `NONE`.",
        "",
        "This audit retests the copy-length ledger after the active post-repair2",
        "formula. The recipe, copy-source addresses, payload model, item-type",
        "model, forced rules, and book-length ledger are fixed. The candidate",
        "replaces truncated binary over the legal length range with an adaptive",
        "global model over the length index, restricted to currently legal indices.",
        "",
        "## Best Alpha Models",
        "",
        "| Rank | Alpha | Length bits | Model bits | Total bits | Delta vs current | Component delta |",
        "|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for rank, row in enumerate(model_rows[:12], start=1):
        lines.append(
            f"| `{rank}` | `{row['alpha']}` | `{row['adaptive_copy_length_bits']:.3f}` | "
            f"`{row['model_declaration_bits']}` | `{row['total_bits']:.3f}` | "
            f"`{row['delta_vs_current_bits']:.3f}` | `{row['component_delta_bits']:.3f}` |"
        )
    lines.extend(
        [
            "",
            "## Result",
            "",
            f"- Current formula bits: `{current_bits:.3f}`",
            f"- Best adaptive formula bits: `{best['total_bits']:.3f}`",
            f"- Gain: `{current_bits - best['total_bits']:.3f}` bits",
            f"- Current copy-length bits: `{current_length_bits:.3f}`",
            f"- Best adaptive copy-length bits: `{best['adaptive_copy_length_bits']:.3f}`",
            f"- Best alpha: `{best['alpha']}`",
            f"- Copy items: `{len(rows)}`",
            "",
            "## Top Adaptive Savings",
            "",
            "| Rank | Book | Op | Length | Legal symbols | Truncated bits | Adaptive bits | Delta |",
            "|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for rank, row in enumerate(top_savings[:12], start=1):
        lines.append(
            f"| `{rank}` | `{row['book']}` | `{row['op_index']}` | `{row['length']}` | "
            f"`{row['symbol_count']}` | `{row['truncated_binary_bits']:.3f}` | "
            f"`{row['adaptive_bits']:.3f}` | `{row['delta_vs_truncated_bits']:.3f}` |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "The improvement is a copy-length coding refinement only. It is decodable",
            "because the decoder knows prior length-index counts and the current",
            "legal length range after the source address has been decoded. It does",
            "not introduce plaintext, row0 meaning, or authorial intent.",
        ]
    )
    if promoted:
        lines.extend(
            [
                "",
                "## Promoted Formula",
                "",
                f"- [`{OUT_FORMULA.name}`](../../{OUT_FORMULA.name})",
            ]
        )
    write_result("78_post_repair2_adaptive_copy_length_compile", result, lines)


if __name__ == "__main__":
    main()
