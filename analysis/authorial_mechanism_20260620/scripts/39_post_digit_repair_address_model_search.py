from __future__ import annotations

import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports" / "test_results"

FORMULA = HERE / "sequential_lz_digit_address_literal_repair_formula_469.json"
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


def gamma_bits(value: int) -> int:
    if value <= 0:
        raise ValueError(value)
    return 2 * int(math.floor(math.log2(value))) + 1


def signed_delta_bits(delta: int) -> int:
    return gamma_bits(abs(delta) + 1) + (0 if delta == 0 else 1)


def rice_bits(value: int, k: int) -> int:
    if value <= 0:
        raise ValueError(value)
    offset = value - 1
    return (offset >> k) + 1 + k


def build_rows(formula: dict, books: dict[str, str]) -> tuple[list[dict], list[dict], list[dict]]:
    order = [str(book) for book in formula["policy"]["book_order"]]
    min_len = int(formula["policy"]["min_len"])
    rice_k = int(formula["policy"]["copy_length_model"]["k"])
    emitted_with_separators = ""
    emitted_digits = ""
    spans = []
    literal_rows = []
    copy_rows = []
    copy_id = 0
    literal_id = 0

    for book_index, book in enumerate(order):
        book_digit_start = len(emitted_digits)
        for op in formula["book_recipes"][book]["ops"]:
            if op["type"] == "literal":
                text = op["text"]
                length = int(op["length"])
                literal_rows.append(
                    {
                        "literal_run_id": literal_id,
                        "book": book,
                        "digit_start": len(emitted_digits),
                        "digit_end": len(emitted_digits) + length,
                        "length": length,
                        "text": text,
                    }
                )
                emitted_with_separators += text
                emitted_digits += text
                literal_id += 1
            elif op["type"] == "copy":
                length = int(op["length"])
                source_digit_pos = int(op["source_digit_pos"])
                chunk = emitted_digits[source_digit_pos : source_digit_pos + length]
                source_pos_with_separators = op.get("source_pos_with_separators_audit")
                if source_pos_with_separators is not None:
                    source_pos_with_separators = int(source_pos_with_separators)
                    if emitted_with_separators[source_pos_with_separators : source_pos_with_separators + length] != chunk:
                        raise RuntimeError((book, op))
                copy_rows.append(
                    {
                        "copy_id": copy_id,
                        "target_book": book,
                        "target_book_index": book_index,
                        "target_digit_global": len(emitted_digits),
                        "source_digit_pos": source_digit_pos,
                        "length": length,
                        "chunk": chunk,
                        "length_code_bits": rice_bits(length - min_len + 1, rice_k),
                    }
                )
                emitted_with_separators += chunk
                emitted_digits += chunk
                copy_id += 1
            else:
                raise ValueError(op)
        if emitted_digits[book_digit_start:] != books[book]:
            raise RuntimeError(f"formula does not roundtrip book {book}")
        spans.append(
            {
                "book": book,
                "book_index": book_index,
                "digit_start": book_digit_start,
                "digit_end": len(emitted_digits),
            }
        )
        emitted_with_separators += "#"

    for row in copy_rows:
        source_span = next(
            span
            for span in spans
            if span["digit_start"] <= row["source_digit_pos"] < span["digit_end"]
        )
        row["source_book"] = source_span["book"]
        row["source_book_index"] = source_span["book_index"]
        row["source_offset"] = row["source_digit_pos"] - source_span["digit_start"]
        row["source_book_delta"] = row["target_book_index"] - row["source_book_index"]
        row["back_distance"] = row["target_digit_global"] - row["source_digit_pos"]
        row["same_book"] = row["target_book"] == row["source_book"]

    return spans, literal_rows, copy_rows


def absolute_copy_bits(copy_rows: list[dict]) -> float:
    return sum(
        1 + math.log2(max(2, row["target_digit_global"])) + row["length_code_bits"]
        for row in copy_rows
    )


def standard_address_models(copy_rows: list[dict]) -> list[dict]:
    models = [
        {
            "model": "absolute_digit_source_pos",
            "copy_bits": absolute_copy_bits(copy_rows),
            "decodable": True,
        },
        {
            "model": "digit_back_distance_gamma",
            "copy_bits": sum(1 + gamma_bits(row["back_distance"]) + row["length_code_bits"] for row in copy_rows),
            "decodable": True,
        },
        {
            "model": "book_delta_digit_offset_gamma",
            "copy_bits": sum(
                1
                + gamma_bits(row["source_book_delta"] + 1)
                + gamma_bits(row["source_offset"] + 1)
                + row["length_code_bits"]
                for row in copy_rows
            ),
            "decodable": True,
        },
    ]

    for model_name, field in [
        ("source_digit_pos_delta_gamma", "source_digit_pos"),
        ("digit_back_distance_delta_gamma", "back_distance"),
    ]:
        total = 0.0
        previous = None
        for row in copy_rows:
            value = row[field]
            if previous is None:
                address_bits = gamma_bits(value + 1) if field == "source_digit_pos" else gamma_bits(value)
            else:
                address_bits = signed_delta_bits(value - previous)
            total += 1 + address_bits + row["length_code_bits"]
            previous = value
        models.append({"model": model_name, "copy_bits": total, "decodable": True})

    previous_delta = None
    previous_offset = None
    total = 0.0
    for row in copy_rows:
        book_delta = row["source_book_delta"]
        source_offset = row["source_offset"]
        if previous_delta is None:
            address_bits = gamma_bits(book_delta + 1) + gamma_bits(source_offset + 1)
        else:
            address_bits = signed_delta_bits(book_delta - previous_delta) + signed_delta_bits(
                source_offset - previous_offset
            )
        total += 1 + address_bits + row["length_code_bits"]
        previous_delta = book_delta
        previous_offset = source_offset
    models.append({"model": "book_delta_digit_offset_delta_gamma", "copy_bits": total, "decodable": True})

    mixed = sum(
        1
        + 1
        + (
            gamma_bits(row["back_distance"])
            if row["same_book"]
            else gamma_bits(row["source_book_delta"] + 1) + gamma_bits(row["source_offset"] + 1)
        )
        + row["length_code_bits"]
        for row in copy_rows
    )
    models.append({"model": "mixed_same_book_digit_distance_else_book_offset", "copy_bits": mixed, "decodable": True})
    return models


def best_seed_address(row: dict, literal_rows: list[dict]) -> dict | None:
    available = [literal for literal in literal_rows if literal["digit_end"] <= row["target_digit_global"]]
    candidates = []
    for literal in available:
        offset = literal["text"].find(row["chunk"])
        if offset < 0:
            continue
        candidates.append(
            {
                "address_bits": math.log2(max(2, len(available))) + gamma_bits(offset + 1),
                "literal_run_id": literal["literal_run_id"],
                "offset": offset,
            }
        )
    if not candidates:
        return None
    return min(candidates, key=lambda item: (item["address_bits"], item["literal_run_id"], item["offset"]))


def optimize_sparse_seed_runs(seed_possible: list[bool], seed_savings: list[float]) -> dict:
    intervals = []
    n = len(seed_possible)
    for start in range(n):
        if not seed_possible[start]:
            continue
        savings = 0.0
        for end in range(start, n):
            if not seed_possible[end]:
                break
            savings += seed_savings[end]
            intervals.append((start, end, savings, end - start + 1))

    states: dict[int, tuple[float, list[tuple[int, int, float, int]]]] = {-1: (0.0, [])}
    best = None
    for run_count in range(1, sum(seed_possible) + 1):
        new_states = {}
        for previous_end, (cost, path) in states.items():
            for start, end, savings, length in intervals:
                if start <= previous_end:
                    continue
                add = gamma_bits(start - previous_end) + gamma_bits(length + 1) - savings
                value = cost + add
                if value < new_states.get(end, (float("inf"), []))[0]:
                    new_states[end] = (value, path + [(start, end, savings, length)])
        if not new_states:
            break
        cost, path = min(new_states.values(), key=lambda item: item[0])
        net_extra = gamma_bits(run_count + 1) + cost
        candidate = {
            "net_extra_bits": net_extra,
            "seed_run_count": run_count,
            "seed_copy_count": sum(item[3] for item in path),
            "selected_seed_savings_bits": sum(item[2] for item in path),
        }
        if best is None or candidate["net_extra_bits"] < best["net_extra_bits"]:
            best = candidate
        states = new_states

    return best or {
        "net_extra_bits": float("inf"),
        "seed_run_count": 0,
        "seed_copy_count": 0,
        "selected_seed_savings_bits": 0.0,
    }


def literal_seed_models(copy_rows: list[dict], literal_rows: list[dict], absolute_bits: float) -> tuple[list[dict], dict]:
    optimistic = 0.0
    conservative = 0.0
    usable = 0
    used = 0
    savings = 0.0
    seed_possible = []
    seed_savings = []

    for row in copy_rows:
        absolute_address = math.log2(max(2, row["target_digit_global"]))
        seed = best_seed_address(row, literal_rows)
        if seed is None:
            optimistic += 1 + absolute_address + row["length_code_bits"]
            conservative += 1 + 1 + absolute_address + row["length_code_bits"]
            seed_possible.append(False)
            seed_savings.append(0.0)
            continue

        usable += 1
        saving = absolute_address - seed["address_bits"]
        seed_possible.append(True)
        seed_savings.append(saving)
        if saving > 0:
            used += 1
            savings += saving
            optimistic += 1 + seed["address_bits"] + row["length_code_bits"]
        else:
            optimistic += 1 + absolute_address + row["length_code_bits"]
        conservative += 1 + min(1 + absolute_address, 1 + seed["address_bits"]) + row["length_code_bits"]

    sparse = optimize_sparse_seed_runs(seed_possible, seed_savings)
    return (
        [
            {
                "model": "literal_seed_address_optimistic_no_mode",
                "copy_bits": optimistic,
                "decodable": False,
                "seed_copy_count": used,
            },
            {
                "model": "literal_seed_address_conservative_mode_per_copy",
                "copy_bits": conservative,
                "decodable": True,
                "seed_copy_count": used,
            },
            {
                "model": "literal_seed_sparse_run_list_seed_required",
                "copy_bits": absolute_bits + sparse["net_extra_bits"],
                "decodable": True,
                "seed_copy_count": sparse["seed_copy_count"],
                "details": sparse,
            },
        ],
        {
            "seed_usable_copy_items": usable,
            "seed_positive_saving_copy_items": used,
            "optimistic_seed_savings_bits": savings,
            "best_sparse_seed_extra_bits": sparse["net_extra_bits"],
            "best_sparse_seed_copy_count": sparse["seed_copy_count"],
            "best_sparse_seed_run_count": sparse["seed_run_count"],
        },
    )


def main() -> None:
    formula = load_json(FORMULA)
    books = {str(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    _spans, literal_rows, copy_rows = build_rows(formula, books)
    current_bits = formula["mdl_estimate_rough"]["sequential_lz_digit_address_literal_repair_bits"]
    current_copy_bits = formula["mdl_estimate_rough"]["copy_bits"]
    absolute_bits = absolute_copy_bits(copy_rows)
    if abs(absolute_bits - current_copy_bits) > 1e-6:
        raise RuntimeError((absolute_bits, current_copy_bits))
    fixed_noncopy_bits = current_bits - current_copy_bits
    standard = standard_address_models(copy_rows)
    seed_models, seed_stats = literal_seed_models(copy_rows, literal_rows, absolute_bits)

    rows = []
    for row in [*standard, *seed_models]:
        total_bits = fixed_noncopy_bits + row["copy_bits"]
        rows.append({**row, "total_bits": total_bits, "delta_vs_current_bits": total_bits - current_bits})
    rows.sort(key=lambda row: row["total_bits"])

    best_decodable = next(row for row in rows if row["decodable"])
    best_any = rows[0]
    if best_decodable["model"] != "absolute_digit_source_pos" and best_decodable["total_bits"] < current_bits:
        classification = "post_digit_repair_address_model_candidate"
    elif best_any["total_bits"] < current_bits and not best_any["decodable"]:
        classification = "post_digit_repair_address_optimistic_only_not_promoted"
    else:
        classification = "post_digit_repair_address_absolute_retained"

    result = {
        "schema": "post_digit_repair_address_model_search.v1",
        "test": "39_post_digit_repair_address_model_search",
        "classification": classification,
        "translation_delta": "NONE",
        "source_formula": str(FORMULA.relative_to(ROOT)),
        "current_formula_bits": current_bits,
        "fixed_noncopy_bits": fixed_noncopy_bits,
        "copy_items": len(copy_rows),
        "same_book_copy_items": sum(1 for row in copy_rows if row["same_book"]),
        "models": rows,
        "seed_stats": seed_stats,
        "boundary": formula["boundary"],
    }

    lines = [
        "# Post-Digit-Repair Address Model Search",
        "",
        f"Verdict: `{classification}`. Translation delta: `NONE`.",
        "",
        "This audit retests copy-source address ledgers after the latest",
        "digit-address literal-to-copy repair. The recipe is fixed; only the",
        "copy source-address ledger changes.",
        "",
        "## Address Models",
        "",
        "| Model | Copy bits | Total bits | Delta vs current | Decodable | Seed copies |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            f"| `{row['model']}` | `{row['copy_bits']:.1f}` | `{row['total_bits']:.1f}` | "
            f"`{row['delta_vs_current_bits']:.1f}` | `{row['decodable']}` | "
            f"`{row.get('seed_copy_count', 0)}` |"
        )
    lines.extend(
        [
            "",
            "## Seed Address Shape",
            "",
            "| Metric | Value |",
            "|---|---:|",
            f"| Copy items | `{len(copy_rows)}` |",
            f"| Same-book copy items | `{sum(1 for row in copy_rows if row['same_book'])}` |",
            f"| Copy items with any prior literal-seed address | `{seed_stats['seed_usable_copy_items']}` |",
            f"| Copy items with positive optimistic seed saving | `{seed_stats['seed_positive_saving_copy_items']}` |",
            f"| Optimistic seed address savings | `{seed_stats['optimistic_seed_savings_bits']:.1f}` bits |",
            f"| Best sparse seed extra cost | `{seed_stats['best_sparse_seed_extra_bits']:.1f}` bits |",
            "",
            "## Interpretation",
            "",
            "Absolute digit-only `source_digit_pos` remains the best decodable ledger",
            "if no decodable row beats it. Any non-decodable literal-seed lower",
            "bound is recorded as an optimistic clue only.",
            "",
            "## Boundary",
            "",
            "This is a mechanical address-cost audit only. It does not alter row0,",
            "introduce plaintext, or make an authorial-intent claim.",
        ]
    )
    write_result("39_post_digit_repair_address_model_search", result, lines)


if __name__ == "__main__":
    main()
