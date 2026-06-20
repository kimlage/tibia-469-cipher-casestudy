from __future__ import annotations

import csv
import importlib.util
import json
import random
from pathlib import Path
from statistics import mean, pstdev


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports" / "test_results"

BOOKS_DIGITS = ROOT / "analysis/audit_20260609/books_digits.json"
DP_FORMULA = HERE / "sequential_lz_dp_parse_formula_469.json"
DP_SCRIPT = HERE / "scripts" / "13_sequential_lz_dp_parse_compile.py"
TOPOLOGY_MANIFEST = ROOT / "analysis/physical_topology_20260620/tables/hellgate_public_bookcase_manifest.csv"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_result(name: str, result: dict, lines: list[str]) -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / f"{name}.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (REPORTS / f"{name}.md").write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def load_dp_module():
    spec = importlib.util.spec_from_file_location("seq13_dp", DP_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def numeric_key(value: str) -> tuple[int, int | str]:
    try:
        return (0, int(value))
    except ValueError:
        return (1, value)


def read_manifest() -> list[dict]:
    with TOPOLOGY_MANIFEST.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    return sorted(rows, key=lambda row: int(row["hg_public_entry"]))


def unique_append(order: list[str], book: str) -> None:
    if book and book not in order:
        order.append(book)


def append_missing_numeric(order: list[str], all_books: list[str]) -> list[str]:
    out = list(order)
    for book in all_books:
        unique_append(out, book)
    return out


def order_public_resolved_then_numeric(rows: list[dict], all_books: list[str]) -> list[str]:
    order: list[str] = []
    for row in rows:
        if row["local_match_status"] == "resolved_unique":
            unique_append(order, row["local_bookid"])
    return append_missing_numeric(order, all_books)


def order_public_resolved_reverse_then_numeric(rows: list[dict], all_books: list[str]) -> list[str]:
    order: list[str] = []
    for row in reversed(rows):
        if row["local_match_status"] == "resolved_unique":
            unique_append(order, row["local_bookid"])
    return append_missing_numeric(order, all_books)


def order_bookcase_public_entry_then_numeric(rows: list[dict], all_books: list[str]) -> list[str]:
    order: list[str] = []
    for row in sorted(rows, key=lambda item: (int(item["bookcase_public"]), int(item["hg_public_entry"]))):
        if row["local_match_status"] == "resolved_unique":
            unique_append(order, row["local_bookid"])
    return append_missing_numeric(order, all_books)


def order_bookcase_numeric_within_then_missing(rows: list[dict], all_books: list[str]) -> list[str]:
    grouped: dict[str, set[str]] = {}
    for row in rows:
        if row["local_match_status"] == "resolved_unique":
            grouped.setdefault(row["bookcase_public"], set()).add(row["local_bookid"])
    order: list[str] = []
    for bookcase in sorted(grouped, key=lambda value: int(value)):
        for book in sorted(grouped[bookcase], key=numeric_key):
            unique_append(order, book)
    return append_missing_numeric(order, all_books)


def order_public_candidates_then_numeric(rows: list[dict], all_books: list[str], pick: str) -> list[str]:
    order: list[str] = []
    for row in rows:
        if row["local_match_status"] == "resolved_unique":
            unique_append(order, row["local_bookid"])
            continue
        candidates = [item for item in row["candidate_local_bookids"].split("|") if item]
        if pick == "last":
            candidates = list(reversed(candidates))
        for candidate in candidates:
            if candidate not in order:
                order.append(candidate)
                break
    return append_missing_numeric(order, all_books)


def evaluate_order(dp_module, books: dict[str, str], order: list[str], min_len: int) -> dict:
    encoded = dp_module.encode_books_dp(books, order, min_len)
    return {
        "total_bits": encoded["total_bits"],
        "literal_digits": encoded["literal_digits"],
        "literal_runs": encoded["literal_runs"],
        "copy_items": encoded["copy_items"],
        "copied_digits": encoded["copied_digits"],
        "books_roundtrip_ok": encoded["books_roundtrip_ok"],
        "errors": encoded["errors"],
    }


def summarize(values: list[float], observed: float) -> dict:
    return {
        "runs": len(values),
        "mean": mean(values),
        "sd": pstdev(values),
        "min": min(values),
        "max": max(values),
        "p_bits_le_observed": (sum(value <= observed for value in values) + 1) / (len(values) + 1),
    }


def run_random_order_controls(
    dp_module,
    books: dict[str, str],
    all_books: list[str],
    min_len: int,
    observed_bits: float,
    runs: int = 100,
) -> dict:
    values = []
    for seed in range(runs):
        rng = random.Random(4691600 + seed)
        order = all_books[:]
        rng.shuffle(order)
        values.append(evaluate_order(dp_module, books, order, min_len)["total_bits"])
    return summarize(values, observed_bits)


def main() -> None:
    dp_module = load_dp_module()
    formula = load_json(DP_FORMULA)
    books = {str(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    all_books = sorted(books, key=numeric_key)
    rows = read_manifest()
    min_len = int(formula["policy"]["min_len"])
    numeric_bits = formula["mdl_estimate_rough"]["sequential_lz_dp_parse_bits"]

    candidate_orders = {
        "numeric_order": all_books,
        "hellgate_public_resolved_then_numeric_missing": order_public_resolved_then_numeric(rows, all_books),
        "hellgate_public_resolved_reverse_then_numeric_missing": order_public_resolved_reverse_then_numeric(rows, all_books),
        "hellgate_bookcase_public_entry_then_numeric_missing": order_bookcase_public_entry_then_numeric(rows, all_books),
        "hellgate_bookcase_numeric_within_then_missing": order_bookcase_numeric_within_then_missing(rows, all_books),
        "hellgate_public_candidates_first_then_numeric_missing": order_public_candidates_then_numeric(rows, all_books, "first"),
        "hellgate_public_candidates_last_then_numeric_missing": order_public_candidates_then_numeric(rows, all_books, "last"),
    }

    order_rows = []
    for name, order in candidate_orders.items():
        metrics = evaluate_order(dp_module, books, order, min_len)
        order_rows.append(
            {
                "order": name,
                "total_bits": metrics["total_bits"],
                "delta_vs_numeric_bits": metrics["total_bits"] - numeric_bits,
                "literal_digits": metrics["literal_digits"],
                "literal_runs": metrics["literal_runs"],
                "copy_items": metrics["copy_items"],
                "copied_digits": metrics["copied_digits"],
                "books_roundtrip_ok": metrics["books_roundtrip_ok"],
                "errors": metrics["errors"],
                "order_prefix": order[:12],
                "order_full": order,
            }
        )
    order_rows.sort(key=lambda row: row["total_bits"])
    best = order_rows[0]
    random_order_control = run_random_order_controls(dp_module, books, all_books, min_len, best["total_bits"])

    resolved_unique_books = [row["local_bookid"] for row in rows if row["local_match_status"] == "resolved_unique"]
    manifest_stats = {
        "manifest_rows": len(rows),
        "resolved_unique_rows": len(resolved_unique_books),
        "resolved_unique_books": len(set(resolved_unique_books)),
        "ambiguous_rows": sum(1 for row in rows if row["local_match_status"] == "ambiguous"),
        "duplicate_resolved_book_rows": len(resolved_unique_books) - len(set(resolved_unique_books)),
    }

    if best["order"] == "numeric_order":
        classification = "structured_physical_order_not_better_than_numeric"
    elif best["delta_vs_numeric_bits"] >= 0:
        classification = "structured_physical_order_not_better_than_numeric"
    else:
        classification = "structured_physical_order_candidate_not_promoted_due_manifest_ambiguity"

    result = {
        "schema": "structured_physical_order_lz_test.v1",
        "test": "16_structured_physical_order_lz_test",
        "classification": classification,
        "translation_delta": "NONE",
        "source_formula": str(DP_FORMULA.relative_to(ROOT)),
        "topology_manifest": str(TOPOLOGY_MANIFEST.relative_to(ROOT)),
        "manifest_stats": manifest_stats,
        "min_len": min_len,
        "numeric_bits": numeric_bits,
        "best_order": best,
        "orders": order_rows,
        "random_order_control": random_order_control,
        "boundary": {
            "semantic_delta": "NONE",
            "authorial_order_claim": False,
            "fine_topology_available": False,
            "pair_table_origin_explained": False,
        },
    }

    lines = [
        "# Structured Physical Order LZ Test",
        "",
        f"Verdict: `{classification}`. Translation delta: `NONE`.",
        "",
        "This audit tests whether the partial public Hellgate bookcase/order seed",
        "can be used as a zero-search-cost book order for the DP sequential LZ",
        "generator. The source is explicitly public overview/bookcase order, not",
        "exact tile, slot, orientation, or authorial read order.",
        "",
        "## Manifest Coverage",
        "",
        "| Metric | Value |",
        "|---|---:|",
    ]
    for key, value in manifest_stats.items():
        lines.append(f"| `{key}` | `{value}` |")

    lines.extend(
        [
            "",
            "## Candidate Orders",
            "",
            "| Order | Bits | Delta vs numeric | Copied digits | Literal digits | Roundtrip |",
            "|---|---:|---:|---:|---:|---:|",
        ]
    )
    for row in order_rows:
        lines.append(
            f"| `{row['order']}` | `{row['total_bits']:.1f}` | "
            f"`{row['delta_vs_numeric_bits']:.1f}` | `{row['copied_digits']}` | "
            f"`{row['literal_digits']}` | `{row['books_roundtrip_ok']}/70` |"
        )

    lines.extend(
        [
            "",
            "## Random Order Control",
            "",
            "| Runs | Mean bits | Min bits | Max bits | p(bits <= best structured) |",
            "|---:|---:|---:|---:|---:|",
            f"| `{random_order_control['runs']}` | `{random_order_control['mean']:.1f}` | "
            f"`{random_order_control['min']:.1f}` | `{random_order_control['max']:.1f}` | "
            f"`{random_order_control['p_bits_le_observed']:.4f}` |",
            "",
            "## Interpretation",
            "",
            "Structured public orders are useful diagnostics, but the committed public",
            "manifest still has ambiguous entries, duplicate resolved rows, and no fine",
            "tile/slot/orientation/read-order layer. Therefore a better structured",
            "order, if any, is not promoted as authorial order in this cycle.",
            "",
            "## Boundary",
            "",
            "This is a mechanical order-cost audit only. It does not introduce plaintext,",
            "semantic claims, or a row0 pair-table formula.",
        ]
    )
    write_result("16_structured_physical_order_lz_test", result, lines)


if __name__ == "__main__":
    main()
