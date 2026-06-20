from __future__ import annotations

import json
import math
from functools import lru_cache
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports" / "test_results"

FORMULA = HERE / "sequential_lz_dp_parse_formula_469.json"
BOOKS_DIGITS = ROOT / "analysis/audit_20260609/books_digits.json"

LOG2_10 = math.log2(10)
INF = float("inf")


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


def build_stream(formula: dict, books: dict[str, str]) -> tuple[list[dict], list[dict], dict]:
    order = [str(book) for book in formula["policy"]["book_order"]]
    min_len = int(formula["policy"]["min_len"])
    emitted = ""
    emitted_len = 0
    copy_rows: list[dict] = []
    literal_runs: list[dict] = []
    copy_id = 0
    literal_id = 0
    literal_bits = 0.0
    book_header_bits = sum(gamma_bits(len(books[book]) + 1) for book in order)
    stream_header_bits = gamma_bits(len(order) + 1)

    for book in order:
        for op in formula["book_recipes"][book]["ops"]:
            if op["type"] == "literal":
                text = op["text"]
                length = int(op["length"])
                literal_runs.append(
                    {
                        "literal_run_id": literal_id,
                        "global_start": emitted_len,
                        "global_end": emitted_len + length,
                        "length": length,
                        "text": text,
                    }
                )
                literal_bits += 1 + gamma_bits(length + 1) + length * LOG2_10
                emitted += text
                emitted_len += length
                literal_id += 1
            elif op["type"] == "copy":
                length = int(op["length"])
                source_pos = int(op["source_pos"])
                chunk = emitted[source_pos : source_pos + length]
                copy_rows.append(
                    {
                        "copy_id": copy_id,
                        "target_global": emitted_len,
                        "source_pos": source_pos,
                        "length": length,
                        "chunk": chunk,
                    }
                )
                emitted += chunk
                emitted_len += length
                copy_id += 1
            else:
                raise ValueError(op)
        emitted += "#"
        emitted_len += 1

    metadata = {
        "order": order,
        "min_len": min_len,
        "fixed_noncopy_bits": stream_header_bits + book_header_bits + literal_bits,
        "literal_runs": len(literal_runs),
        "literal_digits": sum(row["length"] for row in literal_runs),
    }
    return literal_runs, copy_rows, metadata


def copy_len_bits(row: dict, min_len: int) -> int:
    return gamma_bits(row["length"] - min_len + 1)


def best_prior_literal_seed_address(row: dict, literal_runs: list[dict]) -> dict | None:
    available = [
        literal
        for literal in literal_runs
        if literal["global_end"] <= row["target_global"]
    ]
    candidates = []
    for literal in available:
        offset = literal["text"].find(row["chunk"])
        if offset < 0:
            continue
        address_bits = math.log2(max(2, len(available))) + gamma_bits(offset + 1)
        candidates.append(
            {
                "literal_run_id": literal["literal_run_id"],
                "offset": offset,
                "available_literal_runs": len(available),
                "address_bits": address_bits,
                "exact_literal_run_copy": offset == 0 and row["length"] == literal["length"],
            }
        )
    if not candidates:
        return None
    candidates.sort(key=lambda item: (item["address_bits"], item["literal_run_id"], item["offset"]))
    return candidates[0]


def copy_options(literal_runs: list[dict], copy_rows: list[dict], min_len: int) -> tuple[list[dict], dict]:
    options = []
    absolute_copy_bits = 0.0
    optimistic_copy_bits = 0.0
    per_copy_mode_bits = 0.0
    seed_usable = 0
    exact_literal_run_copies = 0
    positive_seed_uses = 0
    positive_seed_savings = 0.0

    for row in copy_rows:
        length_bits = copy_len_bits(row, min_len)
        absolute_address_bits = math.log2(max(2, row["target_global"]))
        absolute_bits = 1 + absolute_address_bits + length_bits
        absolute_copy_bits += absolute_bits

        seed = best_prior_literal_seed_address(row, literal_runs)
        if seed is None:
            option = {
                **row,
                "absolute_address_bits": absolute_address_bits,
                "length_bits": length_bits,
                "absolute_copy_bits": absolute_bits,
                "seed_possible": False,
                "seed_address_bits": None,
                "seed_saving_bits": 0.0,
                "exact_literal_run_copy": False,
            }
            optimistic_copy_bits += absolute_bits
            per_copy_mode_bits += absolute_bits + 1
            options.append(option)
            continue

        seed_usable += 1
        if seed["exact_literal_run_copy"]:
            exact_literal_run_copies += 1
        seed_address_bits = seed["address_bits"]
        seed_saving_bits = absolute_address_bits - seed_address_bits
        if seed_saving_bits > 0:
            positive_seed_uses += 1
            positive_seed_savings += seed_saving_bits

        seed_bits = 1 + seed_address_bits + length_bits
        optimistic_copy_bits += min(absolute_bits, seed_bits)
        per_copy_mode_bits += 1 + min(
            absolute_address_bits,
            seed_address_bits,
        ) + length_bits + 1

        options.append(
            {
                **row,
                "absolute_address_bits": absolute_address_bits,
                "length_bits": length_bits,
                "absolute_copy_bits": absolute_bits,
                "seed_possible": True,
                "seed_address_bits": seed_address_bits,
                "seed_saving_bits": seed_saving_bits,
                "exact_literal_run_copy": seed["exact_literal_run_copy"],
                "literal_run_id": seed["literal_run_id"],
                "literal_offset": seed["offset"],
            }
        )

    stats = {
        "copy_items": len(copy_rows),
        "seed_usable_copy_items": seed_usable,
        "positive_seed_saving_copy_items": positive_seed_uses,
        "positive_seed_savings_bits": positive_seed_savings,
        "exact_literal_run_copy_items": exact_literal_run_copies,
        "absolute_copy_bits": absolute_copy_bits,
        "optimistic_copy_bits": optimistic_copy_bits,
        "per_copy_mode_bits": per_copy_mode_bits,
    }
    return options, stats


def summarize_mode_runs(path: list[tuple[int, int, int]], options: list[dict]) -> dict:
    gross_mode_bits = 1 + sum(gamma_bits(end - start + 1) for start, end, _mode in path)
    seed_runs = [row for row in path if row[2] == 1]
    seed_copy_count = sum(end - start for start, end, _mode in seed_runs)
    selected_savings = sum(
        options[index]["seed_saving_bits"]
        for start, end, _mode in seed_runs
        for index in range(start, end)
    )
    return {
        "gross_mode_bits": gross_mode_bits,
        "seed_copy_count": seed_copy_count,
        "seed_run_count": len(seed_runs),
        "mode_run_count": len(path),
        "selected_seed_savings_bits": selected_savings,
        "mode_runs": [
            {
                "copy_start": start,
                "copy_end_exclusive": end,
                "mode": "literal_seed" if mode else "absolute_source_pos",
                "length": end - start,
            }
            for start, end, mode in path
        ],
    }


def optimize_rle_mode(options: list[dict], require_seed: bool) -> dict:
    n = len(options)
    prefix_savings = [0.0]
    prefix_seed_possible = [0]
    for option in options:
        prefix_savings.append(prefix_savings[-1] + option["seed_saving_bits"])
        prefix_seed_possible.append(prefix_seed_possible[-1] + (1 if option["seed_possible"] else 0))

    @lru_cache(maxsize=None)
    def solve(index: int, mode: int, used_seed: bool) -> tuple[float, tuple[tuple[int, int, int], ...]]:
        if index >= n:
            if require_seed and not used_seed:
                return INF, ()
            return 0.0, ()

        best_cost = INF
        best_path: tuple[tuple[int, int, int], ...] = ()
        for end in range(index + 1, n + 1):
            length = end - index
            if mode == 1:
                possible_count = prefix_seed_possible[end] - prefix_seed_possible[index]
                if possible_count != length:
                    break
                payload_cost = -(prefix_savings[end] - prefix_savings[index])
                next_used = True
            else:
                payload_cost = 0.0
                next_used = used_seed

            tail_cost, tail_path = solve(end, 1 - mode, next_used)
            cost = gamma_bits(length + 1) + payload_cost + tail_cost
            if cost < best_cost:
                best_cost = cost
                best_path = ((index, end, mode),) + tail_path

        return best_cost, best_path

    best = {"net_extra_bits": INF, "path": (), "initial_mode": None}
    for initial_mode in (0, 1):
        cost, path = solve(0, initial_mode, False)
        cost += 1  # initial source-mode bit
        if cost < best["net_extra_bits"]:
            best = {"net_extra_bits": cost, "path": path, "initial_mode": initial_mode}

    if best["net_extra_bits"] == INF:
        return {
            "net_extra_bits": INF,
            "initial_mode": None,
            "gross_mode_bits": INF,
            "seed_copy_count": 0,
            "seed_run_count": 0,
            "mode_run_count": 0,
            "selected_seed_savings_bits": 0.0,
            "mode_runs": [],
        }

    summary = summarize_mode_runs(list(best["path"]), options)
    return {
        "net_extra_bits": best["net_extra_bits"],
        "initial_mode": "literal_seed" if best["initial_mode"] else "absolute_source_pos",
        **summary,
    }


def seed_intervals(options: list[dict]) -> list[dict]:
    intervals = []
    n = len(options)
    for start in range(n):
        if not options[start]["seed_possible"]:
            continue
        savings = 0.0
        for end in range(start, n):
            if not options[end]["seed_possible"]:
                break
            savings += options[end]["seed_saving_bits"]
            intervals.append(
                {
                    "start": start,
                    "end_inclusive": end,
                    "end_exclusive": end + 1,
                    "length": end - start + 1,
                    "seed_savings_bits": savings,
                }
            )
    return intervals


def optimize_sparse_seed_runs(options: list[dict]) -> dict:
    intervals = seed_intervals(options)
    states: dict[int, tuple[float, list[dict]]] = {-1: (0.0, [])}
    best: dict | None = None
    best_by_run_count = []
    max_runs = sum(1 for option in options if option["seed_possible"])

    for run_count in range(1, max_runs + 1):
        new_states: dict[int, tuple[float, list[dict]]] = {}
        for previous_end, (cost, path) in states.items():
            for interval in intervals:
                if interval["start"] <= previous_end:
                    continue
                gap = interval["start"] - previous_end
                interval_cost = (
                    gamma_bits(gap)
                    + gamma_bits(interval["length"] + 1)
                    - interval["seed_savings_bits"]
                )
                total = cost + interval_cost
                end = interval["end_inclusive"]
                if total < new_states.get(end, (INF, []))[0]:
                    new_states[end] = (total, path + [interval])

        if not new_states:
            break

        run_cost, run_path = min(new_states.values(), key=lambda item: item[0])
        net_extra = gamma_bits(run_count + 1) + run_cost
        best_by_run_count.append(
            {
                "seed_run_count": run_count,
                "net_extra_bits": net_extra,
                "seed_copy_count": sum(row["length"] for row in run_path),
                "selected_seed_savings_bits": sum(row["seed_savings_bits"] for row in run_path),
            }
        )
        if best is None or net_extra < best["net_extra_bits"]:
            best = {
                "net_extra_bits": net_extra,
                "seed_run_count": run_count,
                "seed_copy_count": sum(row["length"] for row in run_path),
                "selected_seed_savings_bits": sum(row["seed_savings_bits"] for row in run_path),
                "gross_mode_bits": net_extra + sum(row["seed_savings_bits"] for row in run_path),
                "seed_runs": run_path,
            }

        states = new_states

    if best is None:
        return {
            "net_extra_bits": INF,
            "seed_run_count": 0,
            "seed_copy_count": 0,
            "selected_seed_savings_bits": 0.0,
            "gross_mode_bits": INF,
            "seed_runs": [],
            "best_by_run_count": [],
        }
    best["best_by_run_count"] = best_by_run_count[:12]
    return best


def main() -> None:
    formula = load_json(FORMULA)
    books = {str(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    literal_runs, copy_rows, metadata = build_stream(formula, books)
    options, stats = copy_options(literal_runs, copy_rows, metadata["min_len"])
    current_bits = formula["mdl_estimate_rough"]["sequential_lz_dp_parse_bits"]
    fixed_noncopy_bits = metadata["fixed_noncopy_bits"]

    rle_optional = optimize_rle_mode(options, require_seed=False)
    rle_seed_required = optimize_rle_mode(options, require_seed=True)
    sparse_seed_required = optimize_sparse_seed_runs(options)

    base_copy_bits = stats["absolute_copy_bits"]
    models = [
        {
            "model": "absolute_flat_source_pos",
            "copy_bits": base_copy_bits,
            "total_bits": fixed_noncopy_bits + base_copy_bits,
            "delta_vs_current_bits": fixed_noncopy_bits + base_copy_bits - current_bits,
            "decodable_mixed_address_ledger": True,
            "seed_copy_count": 0,
            "net_mode_extra_bits": 0.0,
        },
        {
            "model": "literal_seed_address_optimistic_no_mode",
            "copy_bits": stats["optimistic_copy_bits"],
            "total_bits": fixed_noncopy_bits + stats["optimistic_copy_bits"],
            "delta_vs_current_bits": fixed_noncopy_bits + stats["optimistic_copy_bits"] - current_bits,
            "decodable_mixed_address_ledger": False,
            "seed_copy_count": stats["positive_seed_saving_copy_items"],
            "net_mode_extra_bits": 0.0,
        },
        {
            "model": "literal_seed_address_conservative_mode_per_copy",
            "copy_bits": stats["per_copy_mode_bits"],
            "total_bits": fixed_noncopy_bits + stats["per_copy_mode_bits"],
            "delta_vs_current_bits": fixed_noncopy_bits + stats["per_copy_mode_bits"] - current_bits,
            "decodable_mixed_address_ledger": True,
            "seed_copy_count": sum(
                1 for option in options if option["seed_possible"] and option["seed_saving_bits"] > 0
            ),
            "net_mode_extra_bits": len(options) - sum(
                option["seed_saving_bits"]
                for option in options
                if option["seed_possible"] and option["seed_saving_bits"] > 0
            ),
        },
        {
            "model": "literal_seed_grouped_rle_mode_optional_seed",
            "copy_bits": base_copy_bits + rle_optional["net_extra_bits"],
            "total_bits": fixed_noncopy_bits + base_copy_bits + rle_optional["net_extra_bits"],
            "delta_vs_current_bits": fixed_noncopy_bits + base_copy_bits + rle_optional["net_extra_bits"] - current_bits,
            "decodable_mixed_address_ledger": True,
            "seed_copy_count": rle_optional["seed_copy_count"],
            "net_mode_extra_bits": rle_optional["net_extra_bits"],
            "details": rle_optional,
        },
        {
            "model": "literal_seed_grouped_rle_mode_seed_required",
            "copy_bits": base_copy_bits + rle_seed_required["net_extra_bits"],
            "total_bits": fixed_noncopy_bits + base_copy_bits + rle_seed_required["net_extra_bits"],
            "delta_vs_current_bits": fixed_noncopy_bits + base_copy_bits + rle_seed_required["net_extra_bits"] - current_bits,
            "decodable_mixed_address_ledger": True,
            "seed_copy_count": rle_seed_required["seed_copy_count"],
            "net_mode_extra_bits": rle_seed_required["net_extra_bits"],
            "details": rle_seed_required,
        },
        {
            "model": "literal_seed_sparse_run_list_seed_required",
            "copy_bits": base_copy_bits + sparse_seed_required["net_extra_bits"],
            "total_bits": fixed_noncopy_bits + base_copy_bits + sparse_seed_required["net_extra_bits"],
            "delta_vs_current_bits": fixed_noncopy_bits + base_copy_bits + sparse_seed_required["net_extra_bits"] - current_bits,
            "decodable_mixed_address_ledger": True,
            "seed_copy_count": sparse_seed_required["seed_copy_count"],
            "net_mode_extra_bits": sparse_seed_required["net_extra_bits"],
            "details": sparse_seed_required,
        },
    ]
    models.sort(key=lambda row: row["total_bits"])

    decodable_seed_models = [
        row
        for row in models
        if row["decodable_mixed_address_ledger"] and row["seed_copy_count"] > 0
    ]
    best_decodable_seed = min(decodable_seed_models, key=lambda row: row["total_bits"])
    best_optimistic = next(row for row in models if row["model"] == "literal_seed_address_optimistic_no_mode")
    if best_decodable_seed["total_bits"] < current_bits:
        classification = "literal_seed_grouped_mode_promoted"
    elif best_optimistic["total_bits"] < current_bits:
        classification = "literal_seed_grouped_mode_optimistic_only_not_promoted"
    else:
        classification = "literal_seed_grouped_mode_not_promoted"

    result = {
        "schema": "literal_seed_grouped_mode_search.v1",
        "test": "18_literal_seed_grouped_mode_search",
        "classification": classification,
        "translation_delta": "NONE",
        "source_formula": str(FORMULA.relative_to(ROOT)),
        "current_formula_bits": current_bits,
        "fixed_noncopy_bits": fixed_noncopy_bits,
        "models": models,
        "stats": {
            **metadata,
            **stats,
            "best_decodable_seed_model": best_decodable_seed["model"],
        },
        "boundary": {
            "semantic_delta": "NONE",
            "pair_table_origin_explained": False,
            "authorial_intent_claim": False,
        },
    }

    lines = [
        "# Literal Seed Grouped-Mode Search",
        "",
        f"Verdict: `{classification}`. Translation delta: `NONE`.",
        "",
        "This audit tests the next refinement after the literal-seed address",
        "search: maybe source-mode bits should be paid by grouped masks or sparse",
        "seed runs, rather than once per copy operation.",
        "",
        "## Address Models",
        "",
        "| Model | Copy bits | Total bits | Delta vs current | Seed copies | Decodable mixed ledger |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in models:
        lines.append(
            f"| `{row['model']}` | `{row['copy_bits']:.1f}` | `{row['total_bits']:.1f}` | "
            f"`{row['delta_vs_current_bits']:.1f}` | `{row['seed_copy_count']}` | "
            f"`{row['decodable_mixed_address_ledger']}` |"
        )

    lines.extend(
        [
            "",
            "## Best Grouped Ledgers",
            "",
            "| Ledger | Net extra vs absolute | Gross mode bits | Seed savings used | Seed copies | Seed runs |",
            "|---|---:|---:|---:|---:|---:|",
            (
                "| RLE mode mask, seed required | "
                f"`{rle_seed_required['net_extra_bits']:.1f}` | "
                f"`{rle_seed_required['gross_mode_bits']:.1f}` | "
                f"`{rle_seed_required['selected_seed_savings_bits']:.1f}` | "
                f"`{rle_seed_required['seed_copy_count']}` | "
                f"`{rle_seed_required['seed_run_count']}` |"
            ),
            (
                "| Sparse seed-run list, seed required | "
                f"`{sparse_seed_required['net_extra_bits']:.1f}` | "
                f"`{sparse_seed_required['gross_mode_bits']:.1f}` | "
                f"`{sparse_seed_required['selected_seed_savings_bits']:.1f}` | "
                f"`{sparse_seed_required['seed_copy_count']}` | "
                f"`{sparse_seed_required['seed_run_count']}` |"
            ),
            "",
            "## Interpretation",
            "",
            "Grouped source-mode ledgers reduce the cost of the earlier per-copy",
            "mode model, but they still do not beat the current absolute",
            "`source_pos` formula. The best seed-using decodable ledger is the",
            "sparse seed-run list, which remains above the baseline. If seed use is",
            "optional, the RLE ledger simply chooses zero seed copies and pays only",
            "mask overhead, which is not a promoted seed-address formula.",
            "",
            "## Boundary",
            "",
            "This is a mechanical address-cost audit only. It does not alter the book",
            "strings, explain row0, or introduce plaintext.",
        ]
    )
    write_result("18_literal_seed_grouped_mode_search", result, lines)


if __name__ == "__main__":
    main()
