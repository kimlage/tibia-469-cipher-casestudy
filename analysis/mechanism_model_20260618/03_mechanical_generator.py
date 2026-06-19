#!/usr/bin/env python3
"""Use the compiled mechanical 469 formula.

This is a syntax-only helper. It does not translate 469 into plaintext.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path


HERE = Path(__file__).resolve().parent
FORMULA_JSON = HERE / "mechanical_formula_469.json"


def load_formula() -> dict:
    if not FORMULA_JSON.exists():
        raise SystemExit(
            "missing mechanical_formula_469.json; run "
            "02_compile_mechanical_formula.py first"
        )
    with FORMULA_JSON.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def encode_symbols(
    symbols: str,
    symbol_to_codes: dict[str, list[str]],
    code_counts: dict[str, int],
    policy: str,
) -> str:
    parts = []
    cycle_index: Counter[str] = Counter()
    for symbol in symbols:
        if symbol.isspace():
            continue
        if symbol not in symbol_to_codes:
            raise SystemExit(f"unknown internal symbol {symbol!r}")
        codes = symbol_to_codes[symbol]
        if policy == "first":
            code = codes[0]
        elif policy == "cycle":
            code = codes[cycle_index[symbol] % len(codes)]
            cycle_index[symbol] += 1
        elif policy == "top":
            code = max(codes, key=lambda item: (code_counts.get(item, 0), item))
        else:
            raise SystemExit(f"unknown policy {policy!r}")
        parts.append(code)
    return "".join(parts)


def reconstruct_book(book_id: str, formula: dict) -> str:
    modules = {module["id"]: module["text"] for module in formula["modules"]}
    recipes = formula["book_recipes"]
    if book_id not in recipes:
        available = ", ".join(sorted(recipes, key=lambda value: int(value)))
        raise SystemExit(f"unknown book {book_id!r}; available: {available}")
    parts = []
    for item in recipes[book_id]:
        if item["type"] == "module":
            parts.append(modules[item["id"]])
        elif item["type"] == "literal":
            parts.append(item["text"])
        else:
            raise SystemExit(f"unknown recipe item type {item['type']!r}")
    return "".join(parts)


def decode_codes(digits: str, formula: dict) -> str:
    digits = "".join(ch for ch in digits if ch.isdigit())
    if len(digits) % 2:
        raise SystemExit("decode-codes requires an even number of digits")
    code_to_symbol = formula["code_to_symbol"]
    symbols = []
    for index in range(0, len(digits), 2):
        code = digits[index : index + 2]
        if code not in code_to_symbol:
            raise SystemExit(f"undefined code {code!r} at offset {index}")
        symbols.append(code_to_symbol[code])
    return "".join(symbols)


def lookup_code(code: str, formula: dict) -> dict:
    if len(code) != 2 or not code.isdigit():
        raise SystemExit("lookup-code expects one 2-digit code")
    code_to_symbol = formula["code_to_symbol"]
    pair_key = "".join(sorted(code))
    pair = formula["pair_table"].get(pair_key)
    return {
        "code": code,
        "symbol": code_to_symbol.get(code),
        "reverse_code": code[::-1],
        "reverse_symbol": code_to_symbol.get(code[::-1]),
        "unordered_pair_key": pair_key,
        "pair_status": pair["status"] if pair else None,
        "pair_symbols": pair["symbols"] if pair else [],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    enc = sub.add_parser("encode-symbols", help="encode internal symbols")
    enc.add_argument("symbols")
    enc.add_argument("--policy", choices=("top", "first", "cycle"), default="top")

    book = sub.add_parser("generate-book", help="reconstruct a raw book")
    book.add_argument("book_id")

    dec = sub.add_parser("decode-codes", help="decode explicit 2-digit codes")
    dec.add_argument("digits")

    lookup = sub.add_parser("lookup-code", help="inspect a code and its reverse")
    lookup.add_argument("code")

    args = parser.parse_args(argv)
    formula = load_formula()

    if args.command == "encode-symbols":
        print(
            encode_symbols(
                args.symbols,
                formula["symbol_to_codes"],
                formula["code_counts"],
                args.policy,
            )
        )
    elif args.command == "generate-book":
        print(reconstruct_book(args.book_id, formula))
    elif args.command == "decode-codes":
        print(decode_codes(args.digits, formula))
    elif args.command == "lookup-code":
        print(json.dumps(lookup_code(args.code, formula), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
