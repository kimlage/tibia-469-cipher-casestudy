from __future__ import annotations

import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports" / "test_results"

FORMULA = HERE / "sequential_lz_dp_parse_formula_469.json"
BOOKS_DIGITS = ROOT / "analysis/audit_20260609/books_digits.json"

LOG2_10 = math.log2(10)


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
                length = int(op["length"])
                text = op["text"]
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


def cost_models(literal_runs: list[dict], copy_rows: list[dict], min_len: int) -> tuple[list[dict], dict]:
    absolute_copy_bits = 0.0
    optimistic_copy_bits = 0.0
    conservative_copy_bits = 0.0
    seed_usable = 0
    seed_used_optimistic = 0
    seed_used_conservative = 0
    optimistic_savings = 0.0
    conservative_savings_before_mode = 0.0
    exact_literal_run_copies = 0
    examples = []

    for row in copy_rows:
        length_bits = copy_len_bits(row, min_len)
        absolute_address_bits = math.log2(max(2, row["target_global"]))
        absolute_copy_bits += 1 + absolute_address_bits + length_bits

        seed = best_prior_literal_seed_address(row, literal_runs)
        if seed is not None:
            seed_usable += 1
            if seed["exact_literal_run_copy"]:
                exact_literal_run_copies += 1
            seed_address_bits = seed["address_bits"]
            if seed_address_bits < absolute_address_bits:
                seed_used_optimistic += 1
                optimistic_savings += absolute_address_bits - seed_address_bits
                if len(examples) < 8:
                    examples.append(
                        {
                            "copy_id": row["copy_id"],
                            "length": row["length"],
                            "absolute_address_bits": absolute_address_bits,
                            "seed_address_bits": seed_address_bits,
                            "literal_run_id": seed["literal_run_id"],
                            "literal_offset": seed["offset"],
                            "exact_literal_run_copy": seed["exact_literal_run_copy"],
                        }
                    )

            # A decodable mixed ledger must say whether this copy uses the
            # absolute stream address or literal-seed address.
            conservative_absolute = 1 + absolute_address_bits
            conservative_seed = 1 + seed_address_bits
            if conservative_seed < conservative_absolute:
                seed_used_conservative += 1
                conservative_savings_before_mode += absolute_address_bits - seed_address_bits
                conservative_copy_bits += 1 + conservative_seed + length_bits
            else:
                conservative_copy_bits += 1 + conservative_absolute + length_bits
        else:
            conservative_copy_bits += 1 + 1 + absolute_address_bits + length_bits

        if seed is not None and seed["address_bits"] < absolute_address_bits:
            optimistic_copy_bits += 1 + seed["address_bits"] + length_bits
        else:
            optimistic_copy_bits += 1 + absolute_address_bits + length_bits

    model_rows = [
        {
            "model": "absolute_flat_source_pos",
            "copy_bits": absolute_copy_bits,
            "requires_source_mode_bits": False,
            "decodable_mixed_address_ledger": True,
        },
        {
            "model": "literal_seed_address_optimistic_no_mode",
            "copy_bits": optimistic_copy_bits,
            "requires_source_mode_bits": True,
            "decodable_mixed_address_ledger": False,
        },
        {
            "model": "literal_seed_address_conservative_mode_per_copy",
            "copy_bits": conservative_copy_bits,
            "requires_source_mode_bits": True,
            "decodable_mixed_address_ledger": True,
        },
    ]
    stats = {
        "copy_items": len(copy_rows),
        "literal_runs": len(literal_runs),
        "seed_usable_copy_items": seed_usable,
        "seed_used_optimistic_copy_items": seed_used_optimistic,
        "seed_used_conservative_copy_items": seed_used_conservative,
        "exact_literal_run_copy_items": exact_literal_run_copies,
        "optimistic_address_savings_bits": optimistic_savings,
        "conservative_address_savings_before_mode_bits": conservative_savings_before_mode,
        "examples": examples,
    }
    return model_rows, stats


def main() -> None:
    formula = load_json(FORMULA)
    books = {str(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    literal_runs, copy_rows, metadata = build_stream(formula, books)
    current_bits = formula["mdl_estimate_rough"]["sequential_lz_dp_parse_bits"]
    models, stats = cost_models(literal_runs, copy_rows, metadata["min_len"])

    rows = []
    for model in models:
        total_bits = metadata["fixed_noncopy_bits"] + model["copy_bits"]
        rows.append(
            {
                **model,
                "total_bits": total_bits,
                "delta_vs_current_bits": total_bits - current_bits,
            }
        )
    rows.sort(key=lambda row: row["total_bits"])

    conservative = next(row for row in rows if row["model"] == "literal_seed_address_conservative_mode_per_copy")
    optimistic = next(row for row in rows if row["model"] == "literal_seed_address_optimistic_no_mode")
    if conservative["total_bits"] < current_bits:
        classification = "literal_seed_address_model_promoted"
    elif optimistic["total_bits"] < current_bits:
        classification = "literal_seed_address_optimistic_only_not_promoted"
    else:
        classification = "literal_seed_address_not_promoted"

    result = {
        "schema": "literal_seed_address_model_search.v1",
        "test": "17_literal_seed_address_model_search",
        "classification": classification,
        "translation_delta": "NONE",
        "source_formula": str(FORMULA.relative_to(ROOT)),
        "current_formula_bits": current_bits,
        "fixed_noncopy_bits": metadata["fixed_noncopy_bits"],
        "models": rows,
        "stats": stats,
        "boundary": {
            "semantic_delta": "NONE",
            "pair_table_origin_explained": False,
            "authorial_intent_claim": False,
        },
    }

    lines = [
        "# Literal Seed Address Model Search",
        "",
        f"Verdict: `{classification}`. Translation delta: `NONE`.",
        "",
        "This audit tests whether copy operations in the DP LZ formula can source",
        "from prior literal seed runs using `literal_run_id + offset`, rather than",
        "the current absolute `source_pos` in the emitted stream.",
        "",
        "## Address Models",
        "",
        "| Model | Copy bits | Total bits | Delta vs current | Decodable mixed ledger |",
        "|---|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            f"| `{row['model']}` | `{row['copy_bits']:.1f}` | `{row['total_bits']:.1f}` | "
            f"`{row['delta_vs_current_bits']:.1f}` | `{row['decodable_mixed_address_ledger']}` |"
        )

    lines.extend(
        [
            "",
            "## Seed Opportunity",
            "",
            "| Metric | Value |",
            "|---|---:|",
            f"| Copy items | `{stats['copy_items']}` |",
            f"| Literal runs | `{stats['literal_runs']}` |",
            f"| Copy items addressable from a prior literal seed | `{stats['seed_usable_copy_items']}` |",
            f"| Optimistic seed-address uses | `{stats['seed_used_optimistic_copy_items']}` |",
            f"| Conservative seed-address uses | `{stats['seed_used_conservative_copy_items']}` |",
            f"| Exact whole literal-run copies | `{stats['exact_literal_run_copy_items']}` |",
            f"| Optimistic address savings | `{stats['optimistic_address_savings_bits']:.1f}` bits |",
            "",
            "## Interpretation",
            "",
            "A literal-seed address looks cheaper only in the optimistic ledger that",
            "does not pay to distinguish absolute stream addresses from literal-seed",
            "addresses. Once a source-mode bit is charged for a decodable mixed",
            "ledger, the model is worse than the current absolute `source_pos`",
            "formula. Therefore this seed-address model is not promoted.",
            "",
            "## Boundary",
            "",
            "This is a mechanical address-cost audit only. It does not alter the book",
            "strings, explain row0, or introduce plaintext.",
        ]
    )
    write_result("17_literal_seed_address_model_search", result, lines)


if __name__ == "__main__":
    main()
