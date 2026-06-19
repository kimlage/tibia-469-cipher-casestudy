#!/usr/bin/env python3
"""Compile the mechanical 469 generation formula and inconsistency register.

This script turns the mechanism model into a lossless, reviewable formula:

  B_k = concat(item_1, ..., item_n)
  item = module_ref(M_i) | literal_digit_string
  M_i = repeated raw-digit module extracted by the canonical MDL tiler

It also records known numeric/reporting inconsistencies and resolves which
number is canonical for the mechanism/origin addendum.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]

BOOKS_DIGITS = ROOT / "analysis" / "audit_20260609" / "books_digits.json"
OCC_STREAMS = (
    ROOT / "analysis" / "audit_20260609" / "homophone_channel" / "occ_streams.json"
)
M1_OUT = ROOT / "analysis" / "audit_20260609" / "m1_out.txt"
C2_OUT = ROOT / "analysis" / "audit_20260609" / "dedup_canonical" / "c2_out.txt"
C1_OUT = ROOT / "analysis" / "audit_20260609" / "dedup_canonical" / "c1_out.txt"
SOURCE_REPORT = ROOT / "analysis" / "lore_audit_20260618" / "source_report_pt.md"
SOURCE_REGISTRY = ROOT / "analysis" / "lore_audit_20260618" / "00_source_registry.yaml"

FORMULA_JSON = HERE / "mechanical_formula_469.json"
REPORT_MD = HERE / "mechanical_formula_report.md"

MODULE_MIN_LENGTH = 20


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


def reconstruct_code_table(occ_streams: dict) -> tuple[dict[str, str], Counter[str]]:
    code_to_symbol = {}
    code_counts: Counter[str] = Counter()
    for symbol, rows in occ_streams["occ"].items():
        for row in rows:
            code = row["code"]
            previous = code_to_symbol.get(code)
            if previous is not None and previous != symbol:
                raise ValueError(f"ambiguous code {code}: {previous} vs {symbol}")
            code_to_symbol[code] = symbol
            code_counts[code] += 1
    return code_to_symbol, code_counts


def invert_code_table(code_to_symbol: dict[str, str]) -> dict[str, list[str]]:
    symbol_to_codes: dict[str, list[str]] = defaultdict(list)
    for code, symbol in sorted(code_to_symbol.items()):
        symbol_to_codes[symbol].append(code)
    return {symbol: codes for symbol, codes in sorted(symbol_to_codes.items())}


def build_pair_table(code_to_symbol: dict[str, str]) -> dict:
    pair_table = {}
    for i in range(10):
        for j in range(i, 10):
            pair = f"{i}{j}"
            codes = [f"{i}{j}"] if i == j else [f"{i}{j}", f"{j}{i}"]
            present = [code for code in codes if code in code_to_symbol]
            symbols = sorted({code_to_symbol[code] for code in present})
            pair_table[pair] = {
                "codes": present,
                "symbols": symbols,
                "symbol_if_pure": symbols[0] if len(symbols) == 1 else None,
                "status": "pure" if len(symbols) <= 1 else "conflict",
            }
    return pair_table


def tile_modules(strings: dict[str, str], min_length: int) -> tuple[list[dict], dict[str, bytearray]]:
    coverage = {book: bytearray(len(strings[book])) for book in strings}
    modules = []
    cap = max(len(text) for text in strings.values())

    def segments():
        segs = []
        for book in strings:
            text, mask = strings[book], coverage[book]
            index = 0
            while index < len(text):
                if not mask[index]:
                    end = index
                    while end < len(text) and not mask[end]:
                        end += 1
                    segs.append((book, index, text[index:end]))
                    index = end
                else:
                    index += 1
        return segs

    def repeat_at(length: int, segs: list[tuple[str, int, str]]):
        occurrences_by_text = {}
        for book, offset, text in segs:
            for index in range(len(text) - length + 1):
                key = text[index : index + length]
                occurrences_by_text.setdefault(key, []).append((book, offset + index))
        best = None
        for key, occs in occurrences_by_text.items():
            if len(occs) < 2:
                continue
            books = {book for book, _ in occs}
            nonoverlap_same_book = (
                max(pos for _, pos in occs) - min(pos for _, pos in occs) >= length
            )
            if len(books) >= 2 or nonoverlap_same_book:
                if best is None or len(occs) > len(occurrences_by_text[best]):
                    best = key
        return best, occurrences_by_text

    while True:
        segs = segments()
        if not segs:
            break
        high = min(cap, max(len(seg[2]) for seg in segs))
        if high < min_length:
            break
        best_length = None
        low = min_length
        while low <= high:
            mid = (low + high) // 2
            key, _ = repeat_at(mid, segs)
            if key is None:
                high = mid - 1
            else:
                best_length = mid
                low = mid + 1
        if best_length is None:
            break

        key, occurrences_by_text = repeat_at(best_length, segs)
        occurrences = sorted(occurrences_by_text[key])
        claimed = []
        last_by_book = {}
        for book, offset in occurrences:
            if book in last_by_book and offset < last_by_book[book] + best_length:
                continue
            claimed.append((book, offset))
            last_by_book[book] = offset
        if len(claimed) < 2:
            cap = best_length - 1
            continue

        module_id = f"M{len(modules):02d}"
        modules.append(
            {
                "id": module_id,
                "text": key,
                "length": len(key),
                "sha256": hashlib.sha256(key.encode("ascii")).hexdigest(),
                "occurrences": [
                    {"book": book, "offset": offset} for book, offset in claimed
                ],
            }
        )
        for book, offset in claimed:
            for index in range(offset, offset + best_length):
                coverage[book][index] = 1
        cap = best_length
    return modules, coverage


def build_recipes(books_digits: dict[str, str], modules: list[dict]) -> dict[str, list[dict]]:
    occurrences_by_book: dict[str, list[tuple[int, str, int]]] = defaultdict(list)
    for module in modules:
        for occ in module["occurrences"]:
            occurrences_by_book[occ["book"]].append(
                (occ["offset"], module["id"], module["length"])
            )

    recipes = {}
    for book in sorted(books_digits, key=numeric_key):
        text = books_digits[book]
        items = []
        pos = 0
        for offset, module_id, length in sorted(occurrences_by_book[book]):
            if offset > pos:
                literal = text[pos:offset]
                items.append(
                    {
                        "type": "literal",
                        "text": literal,
                        "length": len(literal),
                        "sha256": hashlib.sha256(literal.encode("ascii")).hexdigest(),
                    }
                )
            items.append({"type": "module", "id": module_id, "length": length})
            pos = offset + length
        if pos < len(text):
            literal = text[pos:]
            items.append(
                {
                    "type": "literal",
                    "text": literal,
                    "length": len(literal),
                    "sha256": hashlib.sha256(literal.encode("ascii")).hexdigest(),
                }
            )
        recipes[book] = items
    return recipes


def reconstruct_book(recipe: list[dict], modules_by_id: dict[str, dict]) -> str:
    parts = []
    for item in recipe:
        if item["type"] == "module":
            parts.append(modules_by_id[item["id"]]["text"])
        elif item["type"] == "literal":
            parts.append(item["text"])
        else:
            raise ValueError(f"unknown item type {item['type']}")
    return "".join(parts)


def validate_formula(books_digits: dict[str, str], modules: list[dict], recipes: dict[str, list[dict]]) -> dict:
    modules_by_id = {module["id"]: module for module in modules}
    failures = []
    for book, expected in books_digits.items():
        actual = reconstruct_book(recipes[book], modules_by_id)
        if actual != expected:
            failures.append(book)
    literal_digits = sum(
        item["length"]
        for items in recipes.values()
        for item in items
        if item["type"] == "literal"
    )
    module_items = sum(
        1 for items in recipes.values() for item in items if item["type"] == "module"
    )
    literal_items = sum(
        1 for items in recipes.values() for item in items if item["type"] == "literal"
    )
    item_count = module_items + literal_items
    total_digits = sum(len(text) for text in books_digits.values())
    inventory_digits = sum(module["length"] for module in modules)
    return {
        "roundtrip_ok": not failures,
        "roundtrip_failures": failures,
        "module_count": len(modules),
        "inventory_digits": inventory_digits,
        "module_items": module_items,
        "literal_items": literal_items,
        "item_count": item_count,
        "literal_digits": literal_digits,
        "covered_digits": total_digits - literal_digits,
        "covered_fraction": (total_digits - literal_digits) / total_digits,
        "unique_content_digits": inventory_digits + literal_digits,
        "fully_literal_free_books": sum(
            1
            for items in recipes.values()
            if all(item["type"] == "module" for item in items)
        ),
    }


def parse_first(pattern: str, text: str, cast=float):
    match = re.search(pattern, text, re.MULTILINE | re.DOTALL)
    if not match:
        return None
    value = match.group(1).replace(",", "")
    return cast(value)


def build_inconsistency_register(validation: dict, code_to_symbol: dict[str, str]) -> list[dict]:
    m1_text = M1_OUT.read_text(encoding="utf-8")
    c2_text = C2_OUT.read_text(encoding="utf-8")
    c1_text = C1_OUT.read_text(encoding="utf-8")
    source_text = SOURCE_REPORT.read_text(encoding="utf-8")
    registry_text = SOURCE_REGISTRY.read_text(encoding="utf-8")

    reverse_available = [
        code
        for code in code_to_symbol
        if code[0] != code[1] and code[::-1] in code_to_symbol
    ]
    reverse_same = [
        code for code in reverse_available if code_to_symbol[code] == code_to_symbol[code[::-1]]
    ]
    nonpal_present = [code for code in code_to_symbol if code[0] != code[1]]
    reverse_missing = [
        code for code in nonpal_present if code[::-1] not in code_to_symbol
    ]
    reverse_missing_text = ", ".join(f"`{code}`" for code in reverse_missing)

    m1_inventory = parse_first(r"minL=20: modules=62 inventory_digits=(\d+)", m1_text, int)
    m1_covered = parse_first(r"minL=20: modules=62 .*? covered=(\d+)", m1_text, int)
    m1_novel = parse_first(r"minL=20: modules=62 .*? novel_residual=(\d+)", m1_text, int)
    m1_full = parse_first(r"minL=20: modules=62 .*? books_fully_covered=(\d+)", m1_text, int)
    c2_inventory = parse_first(r"modules M=62 inventory_digits=(\d+)", c2_text, int)
    c2_literal = parse_first(r"literal content \((\d+) digits", c2_text, int)
    c2_bits = parse_first(r"TOTAL\s+=\s+([\d.]+) bits", c2_text, float)

    entries = [
        {
            "id": "reverse_denominator_86_89_vs_86_88",
            "status": "resolved",
            "observed_forms": [
                "86/89 non-palindromic codes in narrative shorthand",
                "86/88 reverse-available pairs in dedup canonical table",
            ],
            "resolution": (
                f"{len(nonpal_present)} non-palindromic present codes exist; "
                f"{len(reverse_available)} have their reverse present; "
                f"{len(reverse_same)} of those preserve symbol; "
                f"reverse-missing={reverse_missing_text}."
            ),
            "canonical": "Use 86/88 for tested reverse-available preservation; mention 89 only as the broader non-palindromic present denominator.",
        },
        {
            "id": "module_m1_exploratory_vs_c2_mdl",
            "status": "resolved",
            "observed_forms": [
                f"m1_out minL20 inventory={m1_inventory} covered={m1_covered} novel={m1_novel} fully={m1_full}",
                f"c2_out MDL inventory={c2_inventory} literal_digits={c2_literal} total_bits={c2_bits}",
                f"compiled formula inventory={validation['inventory_digits']} literal_digits={validation['literal_digits']}",
            ],
            "resolution": "The MDL closure is canonical for the formula; m1 is retained as exploratory module-probe output.",
            "canonical": "Use c2/compiled-formula numbers: 62 modules, 4464 inventory digits, 2083 literal digits, 24,627.8 bits.",
        },
        {
            "id": "secret_library_pending_vs_confirmed",
            "status": "resolved",
            "observed_forms": [
                "archived source_report_pt.md says PENDING_PRIMARY_CONFIRMATION",
                "00_source_registry.yaml says CONFIRMED_UNGLOSSED_EXTERNAL_NUMERIC_BOOK",
            ],
            "resolution": (
                "The source report is preserved as supplied; the later registry and "
                "deep verification supersede it after TibiaWiki BR confirmation."
            ),
            "canonical": "Confirmed external unglossed numeric book; no translation value.",
            "evidence_check": {
                "source_report_mentions_pending": "PENDING_PRIMARY_CONFIRMATION" in source_text,
                "registry_mentions_confirmed": "CONFIRMED_UNGLOSSED_EXTERNAL_NUMERIC_BOOK" in registry_text,
            },
        },
        {
            "id": "honeminas_primary_vs_secondary_vectors",
            "status": "resolved",
            "observed_forms": [
                "primary Honeminas formula vectors: 43153 and 34784",
                "secondary s2ward note reported 43151 and 34783",
            ],
            "resolution": "Use primary formula text for source claims; keep secondary pair extraction as imprecise.",
            "canonical": "43153/34784 as source vectors; zero exact hits in the 70-book corpus.",
        },
        {
            "id": "phrase_codebook_internal_vs_official_ground_truth",
            "status": "resolved_policy",
            "observed_forms": [
                "phrase codebook has internally accepted entries",
                "Outcome Ledger requires CipSoft-attested number<->plaintext for semantic promotion",
            ],
            "resolution": "Phrase entries remain validation-only; no book translation or external GT metric moves.",
            "canonical": "Do not call phrase entries official ground truth unless CipSoft publishes/attests them.",
        },
        {
            "id": "formula_generator_scope",
            "status": "resolved_policy",
            "observed_forms": [
                "mechanical formula can generate consistent 469-like numeric strings",
                "mechanical formula cannot generate meanings or accepted translations",
            ],
            "resolution": "Expose generator as mechanical script/formula only.",
            "canonical": "Formula produces numeric layer mechanics, not semantic language.",
        },
    ]

    if c1_text:
        entries[0]["canonical_audit_line"] = parse_first(
            r"reverse is also in map:.*?(\d+); map to SAME", c1_text, int
        )

    return entries


def encode_symbols(symbols: str, symbol_to_codes: dict[str, list[str]], policy: str = "top", counts: Counter[str] | None = None) -> str:
    """Mechanical encoder for arbitrary internal-symbol strings.

    This is not a semantic translator. It only maps known internal symbols to
    numeric homophones using a deterministic policy.
    """
    parts = []
    cycle_index: Counter[str] = Counter()
    for symbol in symbols:
        if symbol.isspace():
            continue
        if symbol not in symbol_to_codes:
            raise ValueError(f"unknown internal symbol {symbol!r}")
        codes = symbol_to_codes[symbol]
        if policy == "first":
            code = codes[0]
        elif policy == "cycle":
            code = codes[cycle_index[symbol] % len(codes)]
            cycle_index[symbol] += 1
        elif policy == "top":
            if counts is None:
                code = codes[0]
            else:
                code = max(codes, key=lambda item: (counts[item], item))
        else:
            raise ValueError(f"unknown policy {policy!r}")
        parts.append(code)
    return "".join(parts)


def build_formula() -> dict:
    books_digits = {str(k): str(v) for k, v in load_json(BOOKS_DIGITS).items()}
    occ_streams = load_json(OCC_STREAMS)
    code_to_symbol, code_counts = reconstruct_code_table(occ_streams)
    symbol_to_codes = invert_code_table(code_to_symbol)
    modules, _coverage = tile_modules(books_digits, MODULE_MIN_LENGTH)
    recipes = build_recipes(books_digits, modules)
    validation = validate_formula(books_digits, modules, recipes)
    if not validation["roundtrip_ok"]:
        raise ValueError(f"roundtrip failed for books {validation['roundtrip_failures']}")

    sample_internal = "ITELBENNA"
    sample_encodings = {
        "top": encode_symbols(sample_internal, symbol_to_codes, "top", code_counts),
        "first": encode_symbols(sample_internal, symbol_to_codes, "first", code_counts),
        "cycle": encode_symbols(sample_internal, symbol_to_codes, "cycle", code_counts),
    }

    return {
        "schema": "mechanical_469_formula.v1",
        "created_at": "2026-06-18",
        "translation_delta": "NONE",
        "scope": "mechanical_generation_only_no_semantics",
        "inputs": {
            "books_digits": str(BOOKS_DIGITS.relative_to(ROOT)),
            "occ_streams": str(OCC_STREAMS.relative_to(ROOT)),
            "m1_out": str(M1_OUT.relative_to(ROOT)),
            "c2_out": str(C2_OUT.relative_to(ROOT)),
        },
        "formula": {
            "internal_alphabet": "".join(sorted(symbol_to_codes)),
            "digit_domain": "00..99 except 39",
            "decode_code": "T(code) = code_to_symbol[code]",
            "decode_pair": "For all pairs except {1,9}, T(ab)=T(ba)=pair_symbol[min(a,b),max(a,b)]; 19/91 is the sole conflict; 39 is undefined.",
            "encode_symbols": "E(symbols, policy) = concat(select_code(symbol_i, policy)); policy is mechanical, not semantic.",
            "generate_book": "B_k = concat(module(M_i) or literal_digit_string from book_recipe[k]).",
        },
        "code_to_symbol": {code: code_to_symbol[code] for code in sorted(code_to_symbol)},
        "symbol_to_codes": symbol_to_codes,
        "code_counts": {code: code_counts[code] for code in sorted(code_counts)},
        "pair_table": build_pair_table(code_to_symbol),
        "modules": modules,
        "book_recipes": recipes,
        "validation": validation,
        "sample_internal_symbol_string": sample_internal,
        "sample_mechanical_encodings": sample_encodings,
        "inconsistency_register": build_inconsistency_register(validation, code_to_symbol),
    }


def write_report(formula: dict) -> None:
    validation = formula["validation"]
    entries = formula["inconsistency_register"]
    modules = formula["modules"]

    lines = [
        "# Mechanical 469 Formula and Consistency Register",
        "",
        "Generated by `02_compile_mechanical_formula.py`.",
        "",
        "This is a formula for generating the **mechanical numeric layer** of 469.",
        "It is not a formula for generating meanings or translations.",
        "",
        "## Formula",
        "",
        "Let:",
        "",
        "- `D = {00..99} \\ {39}` be the valid 2-digit code domain.",
        f"- `Sigma = {formula['formula']['internal_alphabet']}` be the internal symbol alphabet.",
        "- `T: D -> Sigma` be the explicit code table in `mechanical_formula_469.json`.",
        "- `H(s) = {c in D | T(c)=s}` be the homophone class of symbol `s`.",
        "",
        "Then:",
        "",
        "```text",
        "DecodeCode(c) = T(c)",
        "DecodePair(a,b) = T(ab)",
        "  where T(ab)=T(ba) for every unordered pair except {1,9}",
        "  T(19)=I, T(91)=N, and T(39) is undefined",
        "",
        "EncodeSymbols(s1..sn, policy) = concat(select_code(si, policy))",
        "",
        "GenerateBook(k) = concat(item_1..item_m)",
        "  item_j = module_ref(Mi) or literal_digit_string",
        "```",
        "",
        "The book-generation formula is lossless for the 70-book raw digit corpus.",
        "",
        "## Validation",
        "",
        f"- Roundtrip: `{validation['roundtrip_ok']}`.",
        f"- Modules: {validation['module_count']}.",
        f"- Module inventory digits: {validation['inventory_digits']}.",
        f"- Module items in book recipes: {validation['module_items']}.",
        f"- Literal items in book recipes: {validation['literal_items']}.",
        f"- Literal digits: {validation['literal_digits']}.",
        f"- Covered digits: {validation['covered_digits']} ({100 * validation['covered_fraction']:.1f}%).",
        f"- Unique content digits: {validation['unique_content_digits']}.",
        f"- Literal-free generated books: {validation['fully_literal_free_books']}.",
        "",
        "Sample mechanical encodings for internal symbol string",
        f"`{formula['sample_internal_symbol_string']}`:",
        "",
        "| Policy | Numeric output |",
        "|---|---:|",
    ]

    for policy, numeric in formula["sample_mechanical_encodings"].items():
        lines.append(f"| `{policy}` | `{numeric}` |")

    lines.extend(
        [
            "",
            "These samples are syntax examples only. They do not mean words.",
            "",
            "## Top modules",
            "",
            "| Module | Len | Uses | Prefix |",
            "|---|---:|---:|---|",
        ]
    )

    for module in sorted(
        modules,
        key=lambda item: (-(item["length"] * len(item["occurrences"])), item["id"]),
    )[:12]:
        lines.append(
            "| `{}` | {} | {} | `{}` |".format(
                module["id"],
                module["length"],
                len(module["occurrences"]),
                module["text"][:56],
            )
        )

    lines.extend(
        [
            "",
            "## Inconsistency Register",
            "",
            "| ID | Status | Resolution | Canonical handling |",
            "|---|---|---|---|",
        ]
    )

    for entry in entries:
        lines.append(
            "| `{id}` | `{status}` | {resolution} | {canonical} |".format(**entry)
        )

    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "This formula is intentionally mechanical. It can reproduce the numeric",
            "books and generate table-consistent pseudo-469 strings. It cannot certify",
            "any plaintext or word meaning without new external ground truth.",
            "",
        ]
    )
    REPORT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    formula = build_formula()
    FORMULA_JSON.write_text(
        json.dumps(formula, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    write_report(formula)
    print(f"wrote {FORMULA_JSON.relative_to(HERE)}")
    print(f"wrote {REPORT_MD.relative_to(HERE)}")
    print(
        "roundtrip={roundtrip_ok} modules={module_count} literal_digits={literal_digits}".format(
            **formula["validation"]
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
