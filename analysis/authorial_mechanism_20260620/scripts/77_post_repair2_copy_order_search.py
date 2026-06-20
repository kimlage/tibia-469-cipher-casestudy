from __future__ import annotations

import importlib.util
import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports" / "test_results"

FORMULA = HERE / "sequential_lz_digit_address_contextual_bounded_copy_length_minaddr_repair2_formula_469.json"
BOOKS_DIGITS = ROOT / "analysis/audit_20260609/books_digits.json"
SCORER = HERE / "scripts/71_minaddr_local_frontier.py"

CURRENT_TOTAL_KEY = "sequential_lz_digit_address_contextual_bounded_copy_length_minaddr_repair2_bits"


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


def collect_copy_rows(formula: dict, books: dict[str, str], scorer) -> list[dict]:
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
                emitted_len = len(emitted)
                source_first_address_count = max(1, emitted_len - min_len + 1)
                source_first_address_bits = math.log2(max(2, source_first_address_count))
                source_first_max_length = min(remaining, emitted_len - source_digit_pos)
                source_first_symbol_count = source_first_max_length - min_len + 1
                length_index = length - min_len
                source_first_length_bits = scorer.truncated_binary_bits(source_first_symbol_count, length_index)

                length_first_max_length = min(remaining, emitted_len)
                length_first_symbol_count = length_first_max_length - min_len + 1
                length_first_length_bits = scorer.truncated_binary_bits(length_first_symbol_count, length_index)
                length_first_address_count = max(1, emitted_len - length + 1)
                length_first_address_bits = math.log2(max(2, length_first_address_count))

                source_first_bits = source_first_address_bits + source_first_length_bits
                length_first_bits = length_first_length_bits + length_first_address_bits
                chunk = emitted[source_digit_pos : source_digit_pos + length]
                if len(chunk) != length:
                    raise RuntimeError((book, "short_copy", op_index, op))
                rows.append(
                    {
                        "copy_id": copy_id,
                        "book": book,
                        "op_index": op_index,
                        "target_digit_global": emitted_len,
                        "source_digit_pos": source_digit_pos,
                        "length": length,
                        "source_first_bits": source_first_bits,
                        "length_first_bits": length_first_bits,
                        "length_first_delta_bits": length_first_bits - source_first_bits,
                        "source_first_address_count": source_first_address_count,
                        "length_first_address_count": length_first_address_count,
                        "source_first_length_symbol_count": source_first_symbol_count,
                        "length_first_length_symbol_count": length_first_symbol_count,
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


def optimize_sparse_length_first_runs(copy_rows: list[dict]) -> dict:
    savings = [max(0.0, -row["length_first_delta_bits"]) for row in copy_rows]
    possible = [saving > 0 for saving in savings]
    intervals = []
    n = len(copy_rows)
    for start in range(n):
        if not possible[start]:
            continue
        total = 0.0
        for end in range(start, n):
            if not possible[end]:
                break
            total += savings[end]
            intervals.append((start, end, total, end - start + 1))

    states: dict[int, tuple[float, list[tuple[int, int, float, int]]]] = {-1: (0.0, [])}
    best = None
    for run_count in range(1, sum(possible) + 1):
        new_states = {}
        for previous_end, (cost, path) in states.items():
            for start, end, saving, length in intervals:
                if start <= previous_end:
                    continue
                add = gamma_bits(start - previous_end) + gamma_bits(length + 1) - saving
                value = cost + add
                if value < new_states.get(end, (float("inf"), []))[0]:
                    new_states[end] = (value, path + [(start, end, saving, length)])
        if not new_states:
            break
        cost, path = min(new_states.values(), key=lambda item: item[0])
        net_extra = gamma_bits(run_count + 1) + cost
        candidate = {
            "net_extra_bits": net_extra,
            "length_first_run_count": run_count,
            "length_first_copy_count": sum(item[3] for item in path),
            "selected_savings_bits": sum(item[2] for item in path),
            "runs": [
                {
                    "start_copy_id": start,
                    "end_copy_id": end,
                    "saving_bits": saving,
                    "copy_count": length,
                }
                for start, end, saving, length in path
            ],
        }
        if best is None or candidate["net_extra_bits"] < best["net_extra_bits"]:
            best = candidate
        states = new_states

    return best or {
        "net_extra_bits": float("inf"),
        "length_first_run_count": 0,
        "length_first_copy_count": 0,
        "selected_savings_bits": 0.0,
        "runs": [],
    }


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

    copy_rows = collect_copy_rows(formula, books, scorer)
    source_first_copy_bits = sum(row["source_first_bits"] for row in copy_rows)
    length_first_copy_bits = sum(row["length_first_bits"] for row in copy_rows)
    if abs(source_first_copy_bits - current_score["copy_bits"]) > 1e-6:
        raise RuntimeError((source_first_copy_bits, current_score["copy_bits"]))

    fixed_noncopy_bits = current_score["total_bits"] - current_score["copy_bits"]
    optimistic_savings = sum(max(0.0, -row["length_first_delta_bits"]) for row in copy_rows)
    optimistic_switch_count = sum(1 for row in copy_rows if row["length_first_delta_bits"] < 0)
    sparse = optimize_sparse_length_first_runs(copy_rows)

    models = [
        {
            "model": "source_first_then_length_active",
            "copy_bits": source_first_copy_bits,
            "decodable": True,
            "length_first_copy_count": 0,
        },
        {
            "model": "length_first_then_source",
            "copy_bits": length_first_copy_bits,
            "decodable": True,
            "length_first_copy_count": len(copy_rows),
        },
        {
            "model": "best_copy_order_optimistic_no_mode",
            "copy_bits": source_first_copy_bits - optimistic_savings,
            "decodable": False,
            "length_first_copy_count": optimistic_switch_count,
        },
        {
            "model": "copy_order_mode_per_copy",
            "copy_bits": source_first_copy_bits - optimistic_savings + len(copy_rows),
            "decodable": True,
            "length_first_copy_count": optimistic_switch_count,
        },
        {
            "model": "copy_order_sparse_run_list_length_first_required",
            "copy_bits": source_first_copy_bits + sparse["net_extra_bits"],
            "decodable": True,
            "length_first_copy_count": sparse["length_first_copy_count"],
            "details": sparse,
        },
    ]
    rows = []
    for row in models:
        total_bits = fixed_noncopy_bits + row["copy_bits"]
        rows.append({**row, "total_bits": total_bits, "delta_vs_current_bits": total_bits - current_bits})
    rows.sort(key=lambda row: row["total_bits"])

    best_decodable = next(row for row in rows if row["decodable"])
    best_any = rows[0]
    if best_decodable["model"] != "source_first_then_length_active" and best_decodable["total_bits"] < current_bits - 1e-9:
        classification = "post_repair2_copy_order_candidate"
    elif best_any["total_bits"] < current_bits - 1e-9 and not best_any["decodable"]:
        classification = "post_repair2_copy_order_optimistic_only_not_promoted"
    else:
        classification = "post_repair2_copy_order_source_first_retained"

    best_savings = sorted(copy_rows, key=lambda row: row["length_first_delta_bits"])[:20]
    worst_costs = sorted(copy_rows, key=lambda row: row["length_first_delta_bits"], reverse=True)[:20]
    result = {
        "schema": "post_repair2_copy_order_search.v1",
        "test": "77_post_repair2_copy_order_search",
        "classification": classification,
        "translation_delta": "NONE",
        "source_formula": str(FORMULA.relative_to(ROOT)),
        "current_formula_bits": current_bits,
        "current_score_audit": current_score,
        "copy_items": len(copy_rows),
        "fixed_noncopy_bits": fixed_noncopy_bits,
        "models": rows,
        "copy_order_rows": copy_rows,
        "best_length_first_savings": best_savings,
        "worst_length_first_costs": worst_costs,
        "promotion_rule": (
            "promote only if a decodable copy coding order beats source-first address "
            "then length under full post-repair2 rescoring"
        ),
        "boundary": formula["boundary"],
    }

    lines = [
        "# Post-Repair2 Copy Order Search",
        "",
        f"Verdict: `{classification}`. Translation delta: `NONE`.",
        "",
        "This audit retests the within-copy coding order after the active",
        "post-repair2 formula. The recipe, payload model, item-type model, forced",
        "rules, and book-length ledger are fixed. It compares the active",
        "source-address-then-length order against length-then-source alternatives.",
        "",
        "## Copy Order Models",
        "",
        "| Model | Copy bits | Total bits | Delta vs current | Decodable | Length-first copies |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            f"| `{row['model']}` | `{row['copy_bits']:.3f}` | `{row['total_bits']:.3f}` | "
            f"`{row['delta_vs_current_bits']:.3f}` | `{row['decodable']}` | "
            f"`{row['length_first_copy_count']}` |"
        )
    lines.extend(
        [
            "",
            "## Length-First Shape",
            "",
            f"- Copy items: `{len(copy_rows)}`",
            f"- Pure length-first delta: `{length_first_copy_bits - source_first_copy_bits:.3f}` bits",
            f"- Optimistic no-mode savings: `{optimistic_savings:.3f}` bits across `{optimistic_switch_count}` copies",
            f"- Best sparse decodable net delta: `{sparse['net_extra_bits']:.3f}` bits",
            f"- Best sparse length-first copies: `{sparse['length_first_copy_count']}`",
            "",
            "## Best Length-First Savings",
            "",
            "| Rank | Book | Op | Length | Source-first bits | Length-first bits | Delta |",
            "|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for rank, row in enumerate(best_savings[:10], start=1):
        lines.append(
            f"| `{rank}` | `{row['book']}` | `{row['op_index']}` | `{row['length']}` | "
            f"`{row['source_first_bits']:.3f}` | `{row['length_first_bits']:.3f}` | "
            f"`{row['length_first_delta_bits']:.3f}` |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "Pure length-first coding is worse overall. Selecting the cheaper order per",
            "copy would be cheaper only if mode bits were free, so it is an optimistic",
            "lower bound. The tested decodable mode ledgers do not beat the active",
            "source-first order.",
            "",
            "## Boundary",
            "",
            "This is a mechanical copy-cost audit only. It does not alter row0,",
            "introduce plaintext, or make an authorial-intent claim.",
        ]
    )
    write_result("77_post_repair2_copy_order_search", result, lines)


if __name__ == "__main__":
    main()
