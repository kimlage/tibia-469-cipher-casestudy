#!/usr/bin/env python3
"""Mechanism/origin model audit for the 469 book layer.

This script does not try to translate 469. It consolidates the verified
mechanical facts into an explicit production model:

1. a 2-digit numeric index into a mostly mirror-symmetric 10x10 table;
2. a 14-symbol internal alphabet with homophone classes;
3. digit-string modules copied/spliced into the 70 books;
4. zero-omission/rendering and unglossed external numeric anchors.

Inputs are committed audit artifacts so the script does not depend on the large
regenerable SQLite database.
"""

from __future__ import annotations

import json
import math
import random
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]

BOOKS_DIGITS = ROOT / "analysis" / "audit_20260609" / "books_digits.json"
OCC_STREAMS = (
    ROOT / "analysis" / "audit_20260609" / "homophone_channel" / "occ_streams.json"
)
RESIDUAL_CORPUS = ROOT / "analysis" / "audit_20260609" / "residual_corpus.json"
DEEP_VERIFICATION = (
    ROOT / "analysis" / "lore_audit_20260618" / "deep_verification_results.json"
)

RESULTS_JSON = HERE / "mechanism_model_results.json"
REPORT_MD = HERE / "mechanism_model_report.md"
GRID_MD = HERE / "code_symbol_grid.md"

RANDOM_SEED = 46920260618
MODULE_MIN_LENGTHS = (20, 10)


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def numeric_key(value: str) -> tuple[int, int | str]:
    try:
        return (0, int(value))
    except ValueError:
        return (1, value)


def all_codes() -> list[str]:
    return [f"{i}{j}" for i in range(10) for j in range(10)]


def reconstruct_streams(occ_streams: dict) -> dict:
    events_by_book: dict[str, list[dict]] = defaultdict(list)
    code_to_symbol: dict[str, str] = {}
    code_counts: Counter[str] = Counter()

    for symbol, rows in occ_streams["occ"].items():
        for row in rows:
            code = row["code"]
            event = {
                "book": str(row["book"]),
                "pos": int(row["pos"]),
                "code": code,
                "symbol": symbol,
                "novel": bool(row.get("novel", False)),
                "xuniq": bool(row.get("xuniq", False)),
            }
            events_by_book[event["book"]].append(event)
            previous = code_to_symbol.get(code)
            if previous is not None and previous != symbol:
                raise ValueError(f"ambiguous code {code}: {previous} vs {symbol}")
            code_to_symbol[code] = symbol
            code_counts[code] += 1

    books = {}
    for book, events in sorted(events_by_book.items(), key=lambda item: numeric_key(item[0])):
        events.sort(key=lambda item: item["pos"])
        positions = [event["pos"] for event in events]
        if positions != list(range(len(events))):
            raise ValueError(f"book {book}: non-contiguous positions")
        books[book] = {
            "codes": [event["code"] for event in events],
            "symbols": "".join(event["symbol"] for event in events),
            "events": events,
        }

    return {
        "books": books,
        "code_to_symbol": code_to_symbol,
        "code_counts": code_counts,
    }


def symbol_grid(code_to_symbol: dict[str, str]) -> list[list[str]]:
    grid = []
    for i in range(10):
        row = []
        for j in range(10):
            row.append(code_to_symbol.get(f"{i}{j}", "."))
        grid.append(row)
    return grid


def reverse_pair_stats(code_to_symbol: dict[str, str]) -> dict:
    present_codes = sorted(code_to_symbol)
    nonpal_present = [code for code in present_codes if code[0] != code[1]]
    reverse_available = [code for code in nonpal_present if code[::-1] in code_to_symbol]
    reverse_same = [
        code
        for code in reverse_available
        if code_to_symbol[code] == code_to_symbol[code[::-1]]
    ]
    reverse_conflicts = [
        {
            "code": code,
            "symbol": code_to_symbol[code],
            "reverse": code[::-1],
            "reverse_symbol": code_to_symbol[code[::-1]],
        }
        for code in reverse_available
        if code_to_symbol[code] != code_to_symbol[code[::-1]]
    ]
    reverse_missing = [code for code in nonpal_present if code[::-1] not in code_to_symbol]

    pair_classes = {}
    for i in range(10):
        for j in range(i, 10):
            codes = [f"{i}{j}"] if i == j else [f"{i}{j}", f"{j}{i}"]
            present = [code for code in codes if code in code_to_symbol]
            symbols = sorted({code_to_symbol[code] for code in present})
            pair_classes[f"{i}{j}"] = {
                "codes": present,
                "symbols": symbols,
                "pure": len(symbols) <= 1,
            }

    impure = {
        pair: value
        for pair, value in pair_classes.items()
        if len(value["symbols"]) > 1
    }

    return {
        "present_codes": len(present_codes),
        "missing_codes": sorted(set(all_codes()) - set(present_codes)),
        "nonpal_present_codes": len(nonpal_present),
        "reverse_available_codes": len(reverse_available),
        "reverse_same_codes": len(reverse_same),
        "reverse_conflict_codes": reverse_conflicts,
        "reverse_missing_codes": reverse_missing,
        "unordered_pair_classes": len(pair_classes),
        "pure_pair_classes": sum(1 for value in pair_classes.values() if value["pure"]),
        "impure_pair_classes": impure,
        "pair_classes_by_symbol": pair_classes_by_symbol(pair_classes),
    }


def pair_classes_by_symbol(pair_classes: dict) -> dict[str, list[str]]:
    by_symbol: dict[str, list[str]] = defaultdict(list)
    for pair, value in pair_classes.items():
        if len(value["symbols"]) == 1:
            by_symbol[value["symbols"][0]].append(pair)
        elif len(value["symbols"]) > 1:
            by_symbol["/".join(value["symbols"])].append(pair)
        else:
            by_symbol["ABSENT"].append(pair)
    return {symbol: pairs for symbol, pairs in sorted(by_symbol.items())}


def feature_values(code: str) -> dict[str, int | str]:
    a, b = int(code[0]), int(code[1])
    lo, hi = sorted((a, b))
    return {
        "unordered_pair": f"{lo}{hi}",
        "digit_sum": a + b,
        "digit_absdiff": abs(a - b),
        "digit_min": lo,
        "digit_max": hi,
        "digit_product": a * b,
        "sum_mod_3": (a + b) % 3,
        "sum_mod_5": (a + b) % 5,
        "product_mod_5": (a * b) % 5,
        "parity_pair": f"{a % 2}{b % 2}",
        "row": a,
        "column": b,
    }


def majority_accuracy(code_to_symbol: dict[str, str], features: Iterable[str]) -> list[dict]:
    rows = []
    for feature in features:
        buckets: dict[object, Counter[str]] = defaultdict(Counter)
        for code, symbol in code_to_symbol.items():
            buckets[feature_values(code)[feature]][symbol] += 1
        correct = 0
        for counts in buckets.values():
            correct += counts.most_common(1)[0][1]
        rows.append(
            {
                "feature": feature,
                "buckets": len(buckets),
                "majority_accuracy": correct / len(code_to_symbol),
                "errors": len(code_to_symbol) - correct,
            }
        )
    return sorted(rows, key=lambda item: (-item["majority_accuracy"], item["errors"]))


def code_frequency_stats(code_to_symbol: dict[str, str], code_counts: Counter[str]) -> dict:
    total = sum(code_counts.values())
    expected = total / 100.0
    row_sums = {
        str(i): sum(code_counts.get(f"{i}{j}", 0) for j in range(10)) for i in range(10)
    }
    col_sums = {
        str(j): sum(code_counts.get(f"{i}{j}", 0) for i in range(10)) for j in range(10)
    }
    rare_codes = sorted(
        [
            {
                "code": code,
                "symbol": code_to_symbol.get(code),
                "count": code_counts.get(code, 0),
            }
            for code in all_codes()
            if code_counts.get(code, 0) <= 2
        ],
        key=lambda item: (item["count"], item["code"]),
    )
    hot_codes = sorted(
        [
            {
                "code": code,
                "symbol": code_to_symbol.get(code),
                "count": count,
                "z_uniform_cell": (count - expected) / math.sqrt(expected),
            }
            for code, count in code_counts.items()
            if count > expected + 8 * math.sqrt(expected)
        ],
        key=lambda item: (-item["count"], item["code"]),
    )
    return {
        "total_code_tokens": total,
        "expected_per_100_cell": expected,
        "row_sums": row_sums,
        "column_sums": col_sums,
        "rare_codes_count_le_2": rare_codes,
        "hot_codes_z_ge_8": hot_codes,
    }


def find_containment_pairs(strings: dict[str, str]) -> list[dict]:
    pairs = []
    ids = sorted(strings, key=numeric_key)
    for a in ids:
        for b in ids:
            if a == b:
                continue
            if strings[a] in strings[b]:
                pairs.append(
                    {
                        "inside_book": a,
                        "container_book": b,
                        "inside_len": len(strings[a]),
                        "container_len": len(strings[b]),
                    }
                )
    return pairs


def tile_modules(strings: dict[str, str], min_length: int) -> tuple[list[dict], dict[str, bytearray]]:
    coverage = {book: bytearray(len(strings[book])) for book in strings}
    modules = []
    cap = max(len(text) for text in strings.values())

    def uncovered_segments():
        segments = []
        for book in strings:
            text = strings[book]
            mask = coverage[book]
            index = 0
            while index < len(text):
                if not mask[index]:
                    end = index
                    while end < len(text) and not mask[end]:
                        end += 1
                    segments.append((book, index, text[index:end]))
                    index = end
                else:
                    index += 1
        return segments

    def repeat_at(length: int, segments: list[tuple[str, int, str]]):
        positions: dict[str, list[tuple[str, int]]] = {}
        for book, offset, text in segments:
            for index in range(len(text) - length + 1):
                positions.setdefault(text[index : index + length], []).append(
                    (book, offset + index)
                )
        best = None
        for key, occurrences in positions.items():
            if len(occurrences) < 2:
                continue
            books = {book for book, _ in occurrences}
            same_book_nonoverlap = (
                max(pos for _, pos in occurrences) - min(pos for _, pos in occurrences)
                >= length
            )
            if len(books) >= 2 or same_book_nonoverlap:
                if best is None or len(occurrences) > len(positions[best]):
                    best = key
        return best, positions

    while True:
        segments = uncovered_segments()
        if not segments:
            break
        high = min(cap, max(len(segment[2]) for segment in segments))
        if high < min_length:
            break
        best_length = None
        low = min_length
        while low <= high:
            mid = (low + high) // 2
            key, _ = repeat_at(mid, segments)
            if key is None:
                high = mid - 1
            else:
                best_length = mid
                low = mid + 1
        if best_length is None:
            break
        key, positions = repeat_at(best_length, segments)
        occurrences = sorted(positions[key])
        claimed = []
        last_by_book = {}
        for book, pos in occurrences:
            if book in last_by_book and pos < last_by_book[book] + best_length:
                continue
            claimed.append((book, pos))
            last_by_book[book] = pos
        if len(claimed) < 2:
            cap = best_length - 1
            continue
        module_id = f"M{len(modules):02d}"
        modules.append(
            {
                "id": module_id,
                "text": key,
                "length": len(key),
                "occurrences": [
                    {"book": book, "offset": pos} for book, pos in claimed
                ],
                "use_count": len(claimed),
                "book_count": len({book for book, _ in claimed}),
            }
        )
        for book, pos in claimed:
            for index in range(pos, pos + best_length):
                coverage[book][index] = 1
        cap = best_length

    return modules, coverage


def module_summary(strings: dict[str, str], min_length: int) -> dict:
    modules, coverage = tile_modules(strings, min_length)
    total_digits = sum(len(text) for text in strings.values())
    inventory_digits = sum(module["length"] for module in modules)
    covered = sum(sum(mask) for mask in coverage.values())
    novel = total_digits - covered
    top_modules = sorted(
        modules,
        key=lambda item: (-(item["length"] * item["use_count"]), item["id"]),
    )[:12]
    composition = {}
    for book in sorted(strings, key=numeric_key):
        items = []
        occurrences = []
        for module in modules:
            for occ in module["occurrences"]:
                if occ["book"] == book:
                    occurrences.append((occ["offset"], module["id"], module["length"]))
        occurrences.sort()
        pos = 0
        for offset, module_id, length in occurrences:
            if offset > pos:
                items.append({"type": "literal", "length": offset - pos})
            items.append({"type": "module", "id": module_id, "length": length})
            pos = offset + length
        if pos < len(strings[book]):
            items.append({"type": "literal", "length": len(strings[book]) - pos})
        composition[book] = items
    return {
        "min_length": min_length,
        "module_count": len(modules),
        "inventory_digits": inventory_digits,
        "occurrence_count": sum(module["use_count"] for module in modules),
        "covered_digits": covered,
        "covered_fraction": covered / total_digits,
        "novel_digits": novel,
        "unique_content_digits": inventory_digits + novel,
        "compression_ratio": total_digits / (inventory_digits + novel),
        "fully_covered_books": sum(1 for book, mask in coverage.items() if all(mask)),
        "top_modules": [
            {
                "id": module["id"],
                "length": module["length"],
                "use_count": module["use_count"],
                "book_count": module["book_count"],
                "books": sorted(
                    {occ["book"] for occ in module["occurrences"]}, key=numeric_key
                ),
                "prefix": module["text"][:48],
            }
            for module in top_modules
        ],
        "composition_sample": {
            book: composition[book]
            for book in sorted(composition, key=numeric_key)[:15]
        },
    }


def random_module_controls(strings: dict[str, str], min_length: int, trials: int = 100) -> dict:
    """Shuffle each book's digits and rerun module tiling to calibrate coverage."""
    rng = random.Random(RANDOM_SEED + min_length)
    coverages = []
    module_counts = []
    ids = sorted(strings, key=numeric_key)
    for _ in range(trials):
        shuffled = {}
        for book in ids:
            chars = list(strings[book])
            rng.shuffle(chars)
            shuffled[book] = "".join(chars)
        summary = module_summary(shuffled, min_length)
        coverages.append(summary["covered_fraction"])
        module_counts.append(summary["module_count"])
    return {
        "trials": trials,
        "covered_fraction": summarize_floats(coverages),
        "module_count": summarize_numbers(module_counts),
    }


def summarize_numbers(values: list[int]) -> dict:
    values = sorted(values)
    return {
        "min": values[0],
        "median": values[len(values) // 2],
        "max": values[-1],
    }


def summarize_floats(values: list[float]) -> dict:
    values = sorted(values)
    return {
        "min": values[0],
        "median": values[len(values) // 2],
        "max": values[-1],
    }


def symbol_class_summary(occ_streams: dict, code_counts: Counter[str]) -> list[dict]:
    rows = []
    for symbol, codes in sorted(occ_streams["class_sizes"].items()):
        counts = [code_counts.get(code, 0) for code in codes]
        total = sum(counts)
        entropy = 0.0
        for count in counts:
            if count:
                p = count / total
                entropy -= p * math.log2(p)
        rows.append(
            {
                "symbol": symbol,
                "class_size": len(codes),
                "codes": codes,
                "occurrences": total,
                "empirical_entropy_bits": entropy,
                "uniform_entropy_bits": math.log2(len(codes)) if len(codes) > 1 else 0.0,
                "top_code": max(zip(codes, counts), key=lambda item: item[1])[0],
            }
        )
    return rows


def residual_summary(residual: dict) -> dict:
    segments = residual["segments"]
    by_length = sorted(segments, key=lambda item: -item["len"])[:20]
    char_counts = Counter()
    for segment in segments:
        char_counts.update(segment["text"])
    return {
        "method": residual["method"],
        "novel_symbols": residual["novel_symbols"],
        "segment_count": len(segments),
        "top_segments": by_length,
        "symbol_counts": dict(sorted(char_counts.items())),
    }


def external_anchor_summary(deep: dict) -> dict:
    wanted = {
        "secret_library_exact",
        "honeminas_primary_vectors",
        "formula_common_or_short",
    }
    out = {}
    for group, rows in deep["needle_groups"].items():
        if group in wanted:
            out[group] = [
                {
                    "needle": row["needle"],
                    "total_hits": row["total_hits"],
                    "books_with_hit": row["books_with_hit"],
                    "interpretation": row["interpretation"],
                }
                for row in rows
            ]
    return out


def build_results() -> dict:
    books_digits = {str(k): str(v) for k, v in load_json(BOOKS_DIGITS).items()}
    occ_streams = load_json(OCC_STREAMS)
    residual = load_json(RESIDUAL_CORPUS)
    deep = load_json(DEEP_VERIFICATION)

    streams = reconstruct_streams(occ_streams)
    books = streams["books"]
    code_to_symbol = streams["code_to_symbol"]
    code_counts = streams["code_counts"]

    total_symbols = sum(len(book["symbols"]) for book in books.values())
    total_digits = sum(len(value) for value in books_digits.values())

    if len(books_digits) != 70:
        raise ValueError("expected 70 raw digit books")
    if len(books) != 70:
        raise ValueError("expected 70 reconstructed symbol books")
    if total_symbols != 5729:
        raise ValueError(f"expected 5729 symbols, got {total_symbols}")

    modules = {
        str(min_length): module_summary(books_digits, min_length)
        for min_length in MODULE_MIN_LENGTHS
    }
    controls = {
        str(min_length): random_module_controls(books_digits, min_length, trials=50)
        for min_length in MODULE_MIN_LENGTHS
    }

    features = [
        "unordered_pair",
        "digit_sum",
        "digit_absdiff",
        "digit_min",
        "digit_max",
        "digit_product",
        "sum_mod_3",
        "sum_mod_5",
        "product_mod_5",
        "parity_pair",
        "row",
        "column",
    ]

    return {
        "schema": "mechanism_origin_model.v1",
        "created_at": "2026-06-18",
        "inputs": {
            "books_digits": str(BOOKS_DIGITS.relative_to(ROOT)),
            "occ_streams": str(OCC_STREAMS.relative_to(ROOT)),
            "residual_corpus": str(RESIDUAL_CORPUS.relative_to(ROOT)),
            "deep_verification": str(DEEP_VERIFICATION.relative_to(ROOT)),
        },
        "corpus": {
            "book_count": len(books),
            "total_raw_digits": total_digits,
            "total_symbols": total_symbols,
            "total_code_tokens": sum(code_counts.values()),
            "symbol_alphabet": "".join(sorted({s for s in code_to_symbol.values()})),
        },
        "verdict": {
            "translation_delta": "NONE",
            "new_plaintext": False,
            "model": "indexed_pair_table_plus_fixed_chunk_assembly",
            "strongest_explanation": "handmade_mirror_symmetric_10x10_homophone_table_then_preencoded_digit_modules_spliced_into_books",
        },
        "homophone_classes": symbol_class_summary(occ_streams, code_counts),
        "code_grid": symbol_grid(code_to_symbol),
        "pair_geometry": reverse_pair_stats(code_to_symbol),
        "feature_majority_accuracy": majority_accuracy(code_to_symbol, features),
        "code_frequency": code_frequency_stats(code_to_symbol, code_counts),
        "containment_pairs": find_containment_pairs(books_digits),
        "module_model": modules,
        "module_shuffle_controls": controls,
        "residual": residual_summary(residual),
        "external_anchor_checks": external_anchor_summary(deep),
        "known_phrase_layer": [
            {"codes": ["653"], "word": "look", "status": "in_db_internal_anchor"},
            {"codes": ["768"], "word": "at", "status": "in_db_internal_anchor"},
            {"codes": ["764"], "word": "you", "status": "in_db_internal_anchor"},
            {"codes": ["659"], "word": "let", "status": "in_db_internal_anchor"},
            {"codes": ["978"], "word": "me", "status": "in_db_internal_anchor"},
            {"codes": ["54"], "word": "see", "status": "in_db_internal_anchor"},
            {"codes": ["3478", "3466"], "word": "be", "status": "doc_level_reconstruction"},
            {"codes": ["67", "0"], "word": "a", "status": "doc_level_reconstruction"},
            {"codes": ["90871"], "word": "wit", "status": "doc_level_reconstruction"},
            {"codes": ["97664"], "word": "than", "status": "doc_level_reconstruction"},
            {"codes": ["345"], "word": "fool", "status": "doc_level_reconstruction"},
        ],
        "prior_verified_metrics": {
            "generative_mdl": {
                "source": "analysis/audit_20260609/dedup_canonical/c2_out.txt",
                "module_code_bits": 24627.8,
                "best_competing_learned_bits": 29757.1,
                "best_competing_mixa1_bits": 34777.3,
                "module_margin_vs_learned_bits": 5129.3,
                "module_margin_vs_mixa1_bits": 10149.5,
                "lz77_bits": 10678.9,
            },
            "homophone_channel": {
                "source": "analysis/audit_20260609/homophone_channel/step2.out",
                "multi_class_tokens": 5609,
                "novel_multi_class_tokens": 1116,
                "xuniq_multi_class_tokens": 451,
                "best_all_top1_accuracy": 0.7893,
                "best_novel_top1_accuracy": 0.6658,
                "best_xuniq_top1_accuracy": 0.4745,
                "per_occurrence_capacity_bits": 0,
            },
        },
    }


def format_pct(value: float) -> str:
    return f"{100 * value:.1f}%"


def write_grid(results: dict) -> None:
    lines = [
        "# 469 code-symbol grid",
        "",
        "Rows are first digit; columns are second digit. `.` marks the one absent cell.",
        "",
        "| row\\col | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 |",
        "|---:|---|---|---|---|---|---|---|---|---|---|",
    ]
    for index, row in enumerate(results["code_grid"]):
        lines.append("| {} | {} |".format(index, " | ".join(row)))
    lines.append("")
    GRID_MD.write_text("\n".join(lines), encoding="utf-8")


def write_report(results: dict) -> None:
    pair = results["pair_geometry"]
    modules20 = results["module_model"]["20"]
    modules10 = results["module_model"]["10"]
    controls20 = results["module_shuffle_controls"]["20"]
    freq = results["code_frequency"]
    residual = results["residual"]

    lines = [
        "# Mechanism/origin model addendum (2026-06-18)",
        "",
        "Generated by `01_mechanism_model.py`. This is an analysis of how the",
        "70-book layer appears to have been made; it does not attempt to",
        "translate the books.",
        "",
        "## Verdict",
        "",
        "The best current production model is:",
        "",
        "```text",
        "handmade 10x10 numeric index table",
        "-> mostly mirror-symmetric unordered-pair symbol lookup",
        "-> fixed homophone classes over a 14-symbol internal alphabet",
        "-> pre-encoded digit chunks / modules",
        "-> copied and spliced book assembly",
        "-> leading-zero omission render pass",
        "```",
        "",
        "This explains the real structure better than any plaintext model tested.",
        "It still produces no accepted book translation and no new word meaning.",
        "",
        "## Corpus and known layers",
        "",
        f"- Books: {results['corpus']['book_count']}",
        f"- Raw digits: {results['corpus']['total_raw_digits']}",
        f"- Reconstructed symbols: {results['corpus']['total_symbols']}",
        f"- Code tokens: {results['corpus']['total_code_tokens']}",
        f"- Symbol alphabet: `{results['corpus']['symbol_alphabet']}`",
        "",
        "Layer separation remains binding:",
        "",
        "- Phrase/NPC layer: small variable-length word-code with validation-only meanings.",
        "- Book layer: fixed 2-digit homophone table over 14 symbols, non-linguistic.",
        "",
        "Known phrase-layer entries preserved for comparison:",
        "",
        "| Codes | Word | Status |",
        "|---|---|---|",
    ]
    for item in results["known_phrase_layer"]:
        lines.append(
            "| `{}` | `{}` | `{}` |".format(
                "`, `".join(item["codes"]), item["word"], item["status"]
            )
        )

    lines.extend(
        [
            "",
            "## 1. Numeric index / pair table",
            "",
            f"- Present 2-digit cells: {pair['present_codes']}/100.",
            f"- Missing cell: `{', '.join(pair['missing_codes'])}`.",
            f"- Non-palindromic present codes: {pair['nonpal_present_codes']}.",
            f"- Reverse available for: {pair['reverse_available_codes']} codes.",
            f"- Same symbol under reversal when available: {pair['reverse_same_codes']}/{pair['reverse_available_codes']}.",
            f"- Unordered pair classes: {pair['unordered_pair_classes']}; pure classes: {pair['pure_pair_classes']}/{pair['unordered_pair_classes']}.",
            "",
        ]
    )

    if pair["reverse_conflict_codes"]:
        lines.append("Reverse conflicts:")
        lines.append("")
        lines.append("| Code | Symbol | Reverse | Reverse symbol |")
        lines.append("|---:|---|---:|---|")
        for row in pair["reverse_conflict_codes"]:
            lines.append(
                "| `{code}` | `{symbol}` | `{reverse}` | `{reverse_symbol}` |".format(
                    **row
                )
            )
        lines.append("")

    if pair["reverse_missing_codes"]:
        lines.append(
            "Reverse-missing present code(s): "
            + ", ".join(f"`{code}`" for code in pair["reverse_missing_codes"])
            + "."
        )
        lines.append("")

    lines.extend(
        [
            "The code table is therefore best described as an unordered-pair or",
            "mirror lookup, not as a normal substitution cipher and not as a simple",
            "digit-sum formula.",
            "",
            "Code-symbol grid: [code_symbol_grid.md](code_symbol_grid.md).",
            "",
            "### Simple feature checks",
            "",
            "A genuine simple arithmetic generator would make features such as digit",
            "sum, difference, row, or column nearly determine the symbol. They do not.",
            "",
            "| Feature | Buckets | Majority accuracy | Errors |",
            "|---|---:|---:|---:|",
        ]
    )
    for row in results["feature_majority_accuracy"]:
        lines.append(
            "| `{feature}` | {buckets} | {acc:.3f} | {errors} |".format(
                feature=row["feature"],
                buckets=row["buckets"],
                acc=row["majority_accuracy"],
                errors=row["errors"],
            )
        )

    lines.extend(
        [
            "",
            "## 2. Homophone classes",
            "",
            "The internal alphabet is small, but most symbols have many numeric cells.",
            "This is a homophone table, not a one-code-per-letter alphabet.",
            "",
            "| Symbol | Codes | Occurrences | Entropy / uniform entropy | Top code |",
            "|---|---:|---:|---:|---:|",
        ]
    )
    for row in results["homophone_classes"]:
        lines.append(
            "| `{symbol}` | {class_size} | {occurrences} | {entropy:.2f}/{uniform:.2f} | `{top_code}` |".format(
                symbol=row["symbol"],
                class_size=row["class_size"],
                occurrences=row["occurrences"],
                entropy=row["empirical_entropy_bits"],
                uniform=row["uniform_entropy_bits"],
                top_code=row["top_code"],
            )
        )

    hot = ", ".join(
        f"`{row['code']}`={row['count']}" for row in freq["hot_codes_z_ge_8"][:8]
    )
    rare = ", ".join(
        f"`{row['code']}`={row['count']}" for row in freq["rare_codes_count_le_2"]
    )
    lines.extend(
        [
            "",
            "Frequency fingerprints:",
            "",
            f"- Expected under a flat 100-cell table: {freq['expected_per_100_cell']:.1f} hits per cell.",
            f"- Hot cells: {hot}.",
            f"- Missing/rare cells (count <= 2): {rare}.",
            "",
            "The rare/dead-cell pattern is a construction fingerprint. It helps",
            "explain the table; it does not create a plaintext channel.",
            "",
            "## 3. Module/chunk assembly",
            "",
            "The 70 raw digit strings are heavily copied and spliced.",
            "",
            "| Model | Modules | Coverage | Novel digits | Inventory digits | Unique content | Compression | Fully covered books |",
            "|---|---:|---:|---:|---:|---:|---:|---:|",
            "| minL=20 | {m20} | {c20} | {n20} | {i20} | {u20} | {r20:.2f}x | {f20} |".format(
                m20=modules20["module_count"],
                c20=format_pct(modules20["covered_fraction"]),
                n20=modules20["novel_digits"],
                i20=modules20["inventory_digits"],
                u20=modules20["unique_content_digits"],
                r20=modules20["compression_ratio"],
                f20=modules20["fully_covered_books"],
            ),
            "| minL=10 | {m10} | {c10} | {n10} | {i10} | {u10} | {r10:.2f}x | {f10} |".format(
                m10=modules10["module_count"],
                c10=format_pct(modules10["covered_fraction"]),
                n10=modules10["novel_digits"],
                i10=modules10["inventory_digits"],
                u10=modules10["unique_content_digits"],
                r10=modules10["compression_ratio"],
                f10=modules10["fully_covered_books"],
            ),
            "",
            "Shuffle control for minL=20, shuffling digits inside each book before",
            "module extraction:",
            "",
            "- Real coverage: {real}; shuffled median: {med:.1f}% (range {mn:.1f}% to {mx:.1f}%).".format(
                real=format_pct(modules20["covered_fraction"]),
                med=100 * controls20["covered_fraction"]["median"],
                mn=100 * controls20["covered_fraction"]["min"],
                mx=100 * controls20["covered_fraction"]["max"],
            ),
            "",
            f"Exact raw containment pairs: {len(results['containment_pairs'])}.",
            "",
            "Top repeated modules:",
            "",
            "| Module | Len | Uses | Books | Prefix |",
            "|---|---:|---:|---:|---|",
        ]
    )
    for module in modules20["top_modules"]:
        lines.append(
            "| `{id}` | {length} | {use_count} | {book_count} | `{prefix}` |".format(
                **module
            )
        )

    lines.extend(
        [
            "",
            "The previous MDL audit gives the decisive quantitative comparison:",
            "",
            "- two-part module code: 24,627.8 bits;",
            "- strongest learned tokenizer benchmark: 29,757.1 bits;",
            "- MIXA1 benchmark: 34,777.3 bits;",
            "- LZ77-style upper bound: 10,678.9 bits.",
            "",
            "So the corpus is cheaper to describe as module inventory plus assembly",
            "than as any tested message-bearing tokenization.",
            "",
            "## 4. Residual / what is not copied",
            "",
            f"- Residual method: {residual['method']}.",
            f"- Novel symbols: {residual['novel_symbols']}.",
            f"- Residual segments: {residual['segment_count']}.",
            "",
            "Longest residual segments:",
            "",
            "| Book | Offset | Len | Text |",
            "|---:|---:|---:|---|",
        ]
    )
    for segment in residual["top_segments"][:12]:
        text = segment["text"][:80]
        lines.append(
            "| `{book}` | {offset} | {len} | `{text}` |".format(
                book=segment["book"],
                offset=segment["offset"],
                len=segment["len"],
                text=text,
            )
        )

    lines.extend(
        [
            "",
            "These residuals are useful for describing joins/filler. Prior language",
            "tests show they are still not natural language.",
            "",
            "## 5. External anchors and lore fit",
            "",
            "Deep verification found:",
            "",
        ]
    )

    for group, rows in results["external_anchor_checks"].items():
        lines.append(f"### {group}")
        lines.append("")
        lines.append("| Needle | Hits | Books | Interpretation |")
        lines.append("|---:|---:|---:|---|")
        for row in rows:
            lines.append(
                "| `{needle}` | {total_hits} | {books_with_hit} | {interpretation} |".format(
                    **row
                )
            )
        lines.append("")

    lines.extend(
        [
            "Mechanism-lore alignment:",
            "",
            "- `Beware of the Bonelords` frames the native tongue as blink-code plus",
            "  mathematics, and says the written books contain numbers.",
            "- `You Cannot Even Imagine` explicitly uses an assembly framing for the",
            "  Bonelord language.",
            "- `The Honeminas Formula` frames Magic Web/gate coordinates with paired",
            "  numeric vectors.",
            "- `74032 45331` is confirmed as an external unglossed Secret Library",
            "  numeric book, but is absent from the 70-book raw corpus.",
            "",
            "## What this lets us say about the language",
            "",
            "Accepted facts:",
            "",
            "- 469 is not one unified deciphered language in the public evidence.",
            "- The phrase layer has a small validation-only word-code.",
            "- The book layer is a numeric script over a 14-symbol internal alphabet.",
            "- Its 2-digit cells are homophones grouped mostly by unordered digit pairs.",
            "- The books were assembled from pre-encoded chunks, not freshly encrypted",
            "  sentence by sentence.",
            "- No current source supplies official number-to-meaning ground truth.",
            "",
            "Best origin hypothesis:",
            "",
            "The author likely built a symmetric numeric table first, encoded or",
            "generated a stock of pseudo-text chunks through that table, and then",
            "assembled the books by copying/splicing those chunks. The lore's",
            "calculator/formula/gate/mirror vocabulary fits that construction story",
            "better than it fits a hidden natural-language plaintext story.",
            "",
            "## Productive next tests",
            "",
            "These can advance origin/mechanism only; they should not be reported as",
            "translation progress unless external ground truth appears.",
            "",
            "1. Fit explicit symmetric-table construction hypotheses to the 10x10 grid",
            "   and penalize model complexity.",
            "2. Treat future official 469 strings as generator-classification cases:",
            "   do they share row0 cells, modules, omission rules, or only the broad",
            "   numeric style?",
            "3. Maintain a source watchlist for official book glosses, symbol tables,",
            "   or First Dragon-style memoir material.",
            "4. Keep Gate Keeper/Paradox/Serpentine-style material as negative controls",
            "   against motif overfitting.",
            "",
        ]
    )

    REPORT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    results = build_results()
    RESULTS_JSON.write_text(
        json.dumps(results, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_grid(results)
    write_report(results)
    print(f"wrote {RESULTS_JSON.relative_to(HERE)}")
    print(f"wrote {GRID_MD.relative_to(HERE)}")
    print(f"wrote {REPORT_MD.relative_to(HERE)}")
    print(
        "verdict model={model} translation_delta={translation_delta}".format(
            model=results["verdict"]["model"],
            translation_delta=results["verdict"]["translation_delta"],
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
