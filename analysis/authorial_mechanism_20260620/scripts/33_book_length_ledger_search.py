from __future__ import annotations

import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports" / "test_results"

FORMULA = HERE / "sequential_lz_literal_copy_repair_formula_469.json"
OUT_FORMULA = HERE / "sequential_lz_length_ledger_formula_469.json"
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


def rice_bits(value: int, k: int) -> int:
    if value <= 0:
        raise ValueError(value)
    offset = value - 1
    return (offset >> k) + 1 + k


def signed_rice_bits(delta: int, k: int) -> int:
    return rice_bits(abs(delta) + 1, k) + (0 if delta == 0 else 1)


def render_formula(formula: dict, books: dict[str, str]) -> dict:
    emitted = ""
    errors = []
    for book in map(str, formula["policy"]["book_order"]):
        parts = []
        for op in formula["book_recipes"][book]["ops"]:
            if op["type"] == "literal":
                chunk = op["text"]
                if len(chunk) != int(op["length"]):
                    errors.append({"book": book, "type": "literal_length_mismatch", "op": op})
            elif op["type"] == "copy":
                source_pos = int(op["source_pos"])
                length = int(op["length"])
                chunk = emitted[source_pos : source_pos + length]
                if len(chunk) != length:
                    errors.append({"book": book, "type": "short_copy", "op": op})
            else:
                chunk = ""
                errors.append({"book": book, "type": "bad_op", "op": op})
            parts.append(chunk)
            emitted += chunk
        if "".join(parts) != books[book]:
            errors.append({"book": book, "type": "book_mismatch"})
        emitted += "#"
    return {
        "book_count": len(formula["policy"]["book_order"]),
        "books_roundtrip_ok": 0 if errors else len(formula["policy"]["book_order"]),
        "errors": errors,
    }


def current_length_bits(lengths: list[int]) -> int:
    return sum(gamma_bits(length + 1) for length in lengths)


def signed_rice_length_bits(lengths: list[int], anchor: int, k: int) -> int:
    return gamma_bits(anchor + 1) + gamma_bits(k + 1) + sum(
        signed_rice_bits(length - anchor, k) for length in lengths
    )


def delta_gamma_length_bits(lengths: list[int]) -> int:
    total = gamma_bits(lengths[0] + 1)
    for previous, current in zip(lengths, lengths[1:]):
        delta = current - previous
        total += gamma_bits(abs(delta) + 1) + (0 if delta == 0 else 1)
    return total


def offset_rice_length_bits(lengths: list[int], minimum: int, k: int) -> int:
    return gamma_bits(minimum + 1) + gamma_bits(k + 1) + sum(
        rice_bits(length - minimum + 1, k) for length in lengths
    )


def main() -> None:
    formula = load_json(FORMULA)
    books = {str(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    order = [str(book) for book in formula["policy"]["book_order"]]
    lengths = [len(books[book]) for book in order]
    validation = render_formula(formula, books)
    if validation["errors"]:
        raise RuntimeError(validation["errors"])

    current_bits = formula["mdl_estimate_rough"]["sequential_lz_literal_copy_repair_bits"]
    current_book_length_bits = current_length_bits(lengths)
    fixed_without_book_lengths = formula["mdl_estimate_rough"]["fixed_bits"] - current_book_length_bits
    nonfixed_bits = current_bits - formula["mdl_estimate_rough"]["fixed_bits"]

    rows = [
        {
            "model": "gamma_length_plus_1_current",
            "book_length_bits": current_book_length_bits,
            "parameters": {},
            "decodable": True,
        },
        {
            "model": "delta_from_previous_signed_gamma",
            "book_length_bits": delta_gamma_length_bits(lengths),
            "parameters": {},
            "decodable": True,
        },
    ]

    minimum = min(lengths)
    for k in range(0, 13):
        rows.append(
            {
                "model": "rice_offset_from_min_length",
                "book_length_bits": offset_rice_length_bits(lengths, minimum, k),
                "parameters": {"minimum": minimum, "k": k},
                "decodable": True,
            }
        )

    for anchor in range(1, max(lengths) + 1):
        for k in range(0, 13):
            rows.append(
                {
                    "model": "signed_rice_residual_from_anchor",
                    "book_length_bits": signed_rice_length_bits(lengths, anchor, k),
                    "parameters": {"anchor": anchor, "k": k},
                    "decodable": True,
                }
            )

    for row in rows:
        row["total_bits"] = nonfixed_bits + fixed_without_book_lengths + row["book_length_bits"]
        row["delta_vs_current_bits"] = row["total_bits"] - current_bits
    rows.sort(key=lambda row: row["total_bits"])
    best = rows[0]

    promoted = best["total_bits"] < current_bits and best["decodable"]
    classification = "controlled_book_length_ledger_improvement" if promoted else "book_length_ledger_not_promoted"

    if promoted:
        out = json.loads(json.dumps(formula))
        out["schema"] = "sequential_lz_length_ledger_formula.v1"
        out["classification"] = classification
        out["source_baseline_formula"] = str(FORMULA.relative_to(ROOT))
        out["policy"]["book_length_model"] = {
            "family": best["model"],
            **best["parameters"],
            "declaration_bits_included": True,
        }
        out["mdl_estimate_rough"] = {
            **formula["mdl_estimate_rough"],
            "sequential_lz_length_ledger_bits": best["total_bits"],
            "previous_sequential_lz_literal_copy_repair_bits": current_bits,
            "gain_vs_previous_literal_copy_repair_bits": current_bits - best["total_bits"],
            "fixed_bits": fixed_without_book_lengths + best["book_length_bits"],
            "book_length_bits": best["book_length_bits"],
            "previous_book_length_bits": current_book_length_bits,
            "book_length_gain_bits": current_book_length_bits - best["book_length_bits"],
        }
        out["validation"]["book_length_ledger_roundtrip_audit"] = validation
        OUT_FORMULA.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    result = {
        "schema": "book_length_ledger_search.v1",
        "test": "33_book_length_ledger_search",
        "classification": classification,
        "translation_delta": "NONE",
        "source_formula": str(FORMULA.relative_to(ROOT)),
        "output_formula": str(OUT_FORMULA.relative_to(ROOT)) if promoted else None,
        "current_formula_bits": current_bits,
        "current_book_length_bits": current_book_length_bits,
        "fixed_without_book_lengths": fixed_without_book_lengths,
        "length_count": len(lengths),
        "length_min": min(lengths),
        "length_max": max(lengths),
        "length_unique": len(set(lengths)),
        "best_model": best,
        "top_models": rows[:20],
        "validation": validation,
        "boundary": formula["boundary"],
    }

    lines = [
        "# Book Length Ledger Search",
        "",
        f"Verdict: `{classification}`. Translation delta: `NONE`.",
        "",
        "This audit keeps the repaired sequential LZ recipe fixed and retests only",
        "the ledger used to describe the 70 book lengths. The current formula",
        "charges each book length with `gamma(length+1)`. Candidate ledgers are",
        "decodable and charge their declared parameters.",
        "",
        "## Search Summary",
        "",
        "| Metric | Value |",
        "|---|---:|",
        f"| Current formula bits | `{current_bits:.1f}` |",
        f"| Current book-length bits | `{current_book_length_bits:.1f}` |",
        f"| Best book-length bits | `{best['book_length_bits']:.1f}` |",
        f"| Best total bits | `{best['total_bits']:.1f}` |",
        f"| Delta vs current | `{best['delta_vs_current_bits']:.1f}` |",
        f"| Book count | `{len(lengths)}` |",
        f"| Length range | `{min(lengths)}..{max(lengths)}` |",
        f"| Unique lengths | `{len(set(lengths))}` |",
        "",
        "## Top Models",
        "",
        "| Rank | Model | Parameters | Book-length bits | Total bits | Delta |",
        "|---:|---|---|---:|---:|---:|",
    ]
    for index, row in enumerate(rows[:10], start=1):
        lines.append(
            f"| `{index}` | `{row['model']}` | `{json.dumps(row['parameters'], sort_keys=True)}` | "
            f"`{row['book_length_bits']:.1f}` | `{row['total_bits']:.1f}` | "
            f"`{row['delta_vs_current_bits']:.1f}` |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "The book lengths are clustered enough that a signed Rice residual ledger",
            "around a declared anchor is much cheaper than independent gamma-coded",
            "lengths. This is a cost-ledger improvement, not evidence of plaintext",
            "or a row0 pair-table origin.",
            "",
            "## Boundary",
            "",
            "This changes only the mechanical generation cost accounting and the",
            "declared book-length ledger. It does not alter the emitted books, row0,",
            "or the semantic verdict.",
        ]
    )
    write_result("33_book_length_ledger_search", result, lines)


if __name__ == "__main__":
    main()
