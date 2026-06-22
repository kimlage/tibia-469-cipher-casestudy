#!/usr/bin/env python3
"""Minimal external tape program audit.

This front consolidates residual controls into one executable decoder contract
instead of opening another isolated field audit. It asks whether a small
macro/template program over the unified external tapes reduces the declared
external ledger after paying grammar and correction costs.

Scope is analysis-only. It does not touch row0, plaintext, semantics, or the
compression bound.
"""

from __future__ import annotations

import json
import math
import random
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
FRONT = ROOT / "analysis" / "minimal_external_tape_program_audit_20260622"
TEST_RESULTS = FRONT / "reports" / "test_results"

BOOKS_PATH = ROOT / "analysis" / "audit_20260609" / "books_digits.json"
CONTROL_LEDGER_PATH = (
    ROOT
    / "analysis"
    / "unified_control_program_audit_20260622"
    / "reports"
    / "test_results"
    / "01_unified_residual_control_ledger.json"
)
COMPOSITION_INDEX_PATH = (
    ROOT
    / "analysis"
    / "composition_index_structure_audit_20260622"
    / "reports"
    / "test_results"
    / "01_composition_index_structure_gate.json"
)
FAMILY_HOLDOUT_PATH = (
    ROOT
    / "analysis"
    / "prequential_and_row0_origin_audit_20260621"
    / "reports"
    / "test_results"
    / "08_recipe_reparse_family_holdout.json"
)

CONTRACT_JSON = TEST_RESULTS / "01_executable_decoder_contract.json"
CONTRACT_MD = TEST_RESULTS / "01_executable_decoder_contract.md"
LEDGER_JSON = TEST_RESULTS / "02_unified_external_tape_ledger.json"
LEDGER_MD = TEST_RESULTS / "02_unified_external_tape_ledger.md"
GATE_JSON = TEST_RESULTS / "03_macro_program_gate.json"
GATE_MD = TEST_RESULTS / "03_macro_program_gate.md"

LOG2_10 = math.log2(10)
COARSE_VOCAB = [f"{kind}:{bucket}" for kind in ("literal", "copy") for bucket in (
    "len_0008",
    "len_0016",
    "len_0032",
    "len_0064",
    "len_0128",
    "len_0256p",
)]
COARSE_BITS = math.log2(len(COARSE_VOCAB))
CUTOFFS = [20, 30, 40, 50, 60]
RANDOM_TRIALS = 200
MACRO_MIN_LEN = 2
MACRO_MAX_LEN = 5
MACRO_MIN_COUNT = 2
MACRO_LIMIT = 24
ALPHA = 0.5


def log2(value: float) -> float:
    return math.log2(value)


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def load_json(path: Path) -> Any:
    return json.loads(path.read_text())


def book_length_bucket(length: int) -> str:
    if length <= 64:
        return "book_len_0064"
    if length <= 128:
        return "book_len_0128"
    if length <= 256:
        return "book_len_0256"
    return "book_len_0512p"


def op_count_bucket(count: int) -> str:
    if count <= 1:
        return "ops_01"
    if count <= 3:
        return "ops_02_03"
    if count <= 6:
        return "ops_04_06"
    if count <= 10:
        return "ops_07_10"
    return "ops_11p"


def position_bucket(index: int, count: int) -> str:
    if index == 0:
        return "first"
    if index == count - 1:
        return "last"
    if index <= 2:
        return "early"
    return "middle"


def qbucket(fraction: float) -> str:
    return f"q{min(9, max(0, int(fraction * 10))):02d}"


def load_control_rows() -> dict[int, list[dict]]:
    rows = load_json(CONTROL_LEDGER_PATH)["ledger_rows"]
    by_book: dict[int, list[dict]] = defaultdict(list)
    for row in rows:
        by_book[int(row["book"])].append(row)
    return {book: sorted(book_rows, key=lambda row: int(row["op_index"])) for book, book_rows in by_book.items()}


def load_composition_rows() -> dict[int, dict]:
    data = load_json(COMPOSITION_INDEX_PATH)
    return {int(row["book"]): row for row in data["rank_rows"]}


def load_families() -> dict[str, set[int]]:
    if not FAMILY_HOLDOUT_PATH.exists():
        return {}
    data = load_json(FAMILY_HOLDOUT_PATH)
    families = {}
    for row in data.get("rows", []):
        books = {int(book) for book in row.get("test_books", []) if int(book) >= 10}
        if books:
            families[str(row["label"])] = books
    return families


def seed_bits(books: dict[str, str]) -> float:
    return sum(len(books[str(book)]) * LOG2_10 for book in range(10))


def validate_decoder(books: dict[str, str], by_book: dict[int, list[dict]]) -> dict:
    emitted_books = {str(book): books[str(book)] for book in range(10)}
    stream = "".join(books[str(book)] for book in range(10))
    errors = []
    op_count = 0
    for book in range(10, 70):
        output = []
        for row in by_book[book]:
            op_count += 1
            if row["op_type"] == "literal":
                output.append(row["literal_payload"])
            else:
                source = int(row["copy_source_raw"])
                length = int(row["length"])
                available = stream + "".join(output)
                output.append(available[source : source + length])
        rendered = "".join(output)
        if rendered != books[str(book)]:
            mismatch = next(
                (idx for idx, pair in enumerate(zip(rendered, books[str(book)])) if pair[0] != pair[1]),
                None,
            )
            errors.append(
                {
                    "book": book,
                    "rendered_length": len(rendered),
                    "expected_length": len(books[str(book)]),
                    "first_mismatch": mismatch,
                }
            )
        emitted_books[str(book)] = rendered
        stream += rendered
    exact_books = sum(emitted_books[str(book)] == books[str(book)] for book in range(70))
    return {
        "errors": errors,
        "exact_books": exact_books,
        "operation_count": op_count,
        "roundtrip_70_70": exact_books == 70 and not errors,
        "seed_books": list(range(10)),
        "stream_digits": len(stream),
    }


def make_contract(books: dict[str, str], by_book: dict[int, list[dict]]) -> dict:
    validation = validate_decoder(books, by_book)
    return {
        "case_reopened": False,
        "compression_bound_status": "unchanged",
        "decoder_contract": {
            "derived_fields": [
                "target_start from prior emitted operation lengths",
                "book text by executing literal/copy ops over emitted digit stream",
                "op_type from coarse type:length_bucket token",
                "length bucket from coarse type:length_bucket token",
            ],
            "external_tapes": [
                "seed books 0..9 digit payload",
                "coarse type:length_bucket control stream",
                "book-level composition index for exact lengths",
                "literal innovation payload tape",
                "copy hint rank/source tape",
                "macro/template correction tape when program misses",
            ],
            "granted_inputs": [
                "canonical book order 0..69",
                "book lengths",
                "row0 code table as exogenous mechanical substrate",
            ],
            "paid_fields": [
                "seed payload bits",
                "coarse control bits or macro-coded replacement",
                "composition-index bits",
                "literal-payload bits",
                "copy-hint rank bits",
                "macro grammar and correction bits",
            ],
            "target_text_dependencies": [
                "literal payload tape is target digits",
                "copy hint ranks are computed against canonical target chunk/source availability",
                "composition index is computed from exact target lengths",
            ],
        },
        "inputs": {
            "books_digits": rel(BOOKS_PATH),
            "control_ledger": rel(CONTROL_LEDGER_PATH),
            "composition_index": rel(COMPOSITION_INDEX_PATH),
        },
        "plaintext_claim": False,
        "row0_status": "unchanged_exogenous",
        "schema": "minimal_external_tape_decoder_contract.v1",
        "scope": "analysis_only_executable_decoder_contract",
        "translation_delta": "NONE",
        "validation": validation,
    }


def write_contract_md(contract: dict) -> None:
    validation = contract["validation"]
    lines = [
        "# Executable Decoder Contract",
        "",
        "Status: `analysis_only`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Contract",
        "",
        "This decoder reconstructs the numeric 469 books from explicit external tapes. "
        "It is a reproducible execution contract, not an authorial formula.",
        "",
        f"- Seed books: `{contract['decoder_contract']['external_tapes'][0]}`.",
        f"- Exact books: `{validation['exact_books']}/70`.",
        f"- Derived operation count: `{validation['operation_count']}`.",
        f"- Roundtrip: `{validation['roundtrip_70_70']}`.",
        f"- Stream digits: `{validation['stream_digits']}`.",
        "",
        "## External Tapes",
        "",
    ]
    for item in contract["decoder_contract"]["external_tapes"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Target Dependencies", ""])
    for item in contract["decoder_contract"]["target_text_dependencies"]:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## Decision",
            "",
            "The executable contract is valid as an audit baseline. A later macro "
            "program must reduce these tapes after paying grammar/corrections before "
            "it can be promoted as generation progress.",
        ]
    )
    CONTRACT_MD.write_text("\n".join(lines) + "\n")


def make_unified_ledger(books: dict[str, str], by_book: dict[int, list[dict]], composition: dict[int, dict]) -> dict:
    rows = []
    summary = Counter()
    total_bits = Counter()
    for book in range(10, 70):
        book_rows = by_book[book]
        comp = composition[book]
        op_count = len(book_rows)
        for index, row in enumerate(book_rows):
            is_first = index == 0
            composition_bits = float(comp["composition_bits_uniform"]) if is_first else 0.0
            literal_bits = float(row.get("literal_payload_bits") or 0.0)
            copy_hint_bits = float(row.get("copy_hint_rank_bits") or 0.0)
            coarse_bits = COARSE_BITS
            total = coarse_bits + composition_bits + literal_bits + copy_hint_bits
            if row["op_type"] == "literal":
                payload_status = "external_literal_tape"
                summary["literal_ops"] += 1
            else:
                payload_status = "external_copy_hint_tape"
                summary["copy_ops"] += 1
            summary["ops"] += 1
            total_bits["coarse_control_bits_uniform"] += coarse_bits
            total_bits["composition_index_bits"] += composition_bits
            total_bits["literal_payload_bits"] += literal_bits
            total_bits["copy_hint_rank_bits"] += copy_hint_bits
            total_bits["total_external_tape_bits_excluding_seed"] += total
            rows.append(
                {
                    "book": book,
                    "book_length": int(row["book_length"]),
                    "book_length_bucket": book_length_bucket(int(row["book_length"])),
                    "book_op_count": op_count,
                    "coarse_control_bits_uniform": coarse_bits,
                    "coarse_type_length_bucket": row["type_length_symbol"],
                    "composition_count": int(comp["composition_count"]),
                    "composition_index_bits_charged_here": composition_bits,
                    "composition_rank": int(comp["composition_rank"]),
                    "composition_rank_fraction": float(comp["rank_fraction"]),
                    "copy_hint_rank": row.get("copy_hint_rank"),
                    "copy_hint_rank_bits": copy_hint_bits,
                    "copy_hint_rank_bucket": row.get("copy_hint_rank_bucket"),
                    "copy_source_raw": row.get("copy_source_raw"),
                    "derived_fields": ["target_start"],
                    "external_status": payload_status,
                    "exact_length": int(row["length"]),
                    "fields_still_external": [
                        "coarse_control_symbol",
                        "composition_index" if is_first else "composition_index_continues_from_book_header",
                        "literal_payload" if row["op_type"] == "literal" else "copy_hint_rank",
                    ],
                    "literal_payload": row.get("literal_payload"),
                    "literal_payload_bits": literal_bits,
                    "literal_tape_end": row.get("literal_tape_end"),
                    "literal_tape_start": row.get("literal_tape_start"),
                    "op_index": int(row["op_index"]),
                    "op_pos_bucket": position_bucket(index, op_count),
                    "op_type": row["op_type"],
                    "row0_status": "unchanged_exogenous",
                    "target_start": int(row["target_start"]),
                    "target_text_dependency": row.get("target_text_dependency", []),
                    "total_external_bits_charged_here": total,
                }
            )

    total_bits["seed_payload_bits"] = seed_bits(books)
    total_bits["total_external_tape_bits_including_seed"] = (
        total_bits["total_external_tape_bits_excluding_seed"] + total_bits["seed_payload_bits"]
    )
    return {
        "case_reopened": False,
        "compression_bound_status": "unchanged",
        "ledger_rows": rows,
        "plaintext_claim": False,
        "row0_status": "unchanged_exogenous",
        "schema": "unified_external_tape_ledger.v1",
        "scope": "analysis_only_unified_external_tape_ledger",
        "summary": {
            **{key: int(value) for key, value in summary.items()},
            **{key: float(value) for key, value in total_bits.items()},
            "books": 60,
            "seed_books": 10,
        },
        "translation_delta": "NONE",
    }


def write_ledger_md(ledger: dict) -> None:
    s = ledger["summary"]
    lines = [
        "# Unified External Tape Ledger",
        "",
        "Status: `analysis_only`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Summary",
        "",
        f"- Derived books: `{s['books']}`.",
        f"- Operations: `{s['ops']}` (`{s['literal_ops']}` literal, `{s['copy_ops']}` copy).",
        f"- Seed payload bits: `{s['seed_payload_bits']:.3f}`.",
        f"- Uniform coarse-control bits: `{s['coarse_control_bits_uniform']:.3f}`.",
        f"- Composition-index bits: `{s['composition_index_bits']:.3f}`.",
        f"- Literal-payload bits: `{s['literal_payload_bits']:.3f}`.",
        f"- Copy-hint rank bits: `{s['copy_hint_rank_bits']:.3f}`.",
        f"- Total external tape bits including seed: `{s['total_external_tape_bits_including_seed']:.3f}`.",
        "",
        "## Ledger Fields",
        "",
        "Each row records the book/op, coarse control token, exact length, "
        "composition-index charge, literal or copy-hint tape charge, derived fields, "
        "and target-conditioned dependencies.",
        "",
        "## Decision",
        "",
        "This ledger is the baseline for a unified control program. Any promoted "
        "macro grammar must reduce this external tape total after paying grammar "
        "and correction costs.",
    ]
    LEDGER_MD.write_text("\n".join(lines) + "\n")


@dataclass
class BookIR:
    book: int
    book_length: int
    op_count: int
    sequence: tuple[str, ...]
    tape_symbols: tuple[str, ...]
    composition_rank_fraction: float
    composition_count: int
    composition_bits: float


def make_book_ir(ledger: dict) -> dict[int, BookIR]:
    grouped: dict[int, list[dict]] = defaultdict(list)
    for row in ledger["ledger_rows"]:
        grouped[int(row["book"])].append(row)
    result = {}
    for book, rows in grouped.items():
        rows = sorted(rows, key=lambda row: row["op_index"])
        tape_symbols = []
        for row in rows:
            if row["op_type"] == "literal":
                aux = f"lit_len_{len(row['literal_payload'] or '')}"
            else:
                aux = f"copy_rank_{row['copy_hint_rank_bucket']}"
            if row["op_index"] == 0:
                aux += f":comp_{qbucket(float(row['composition_rank_fraction']))}"
            tape_symbols.append(f"{row['coarse_type_length_bucket']}|{aux}")
        result[book] = BookIR(
            book=book,
            book_length=int(rows[0]["book_length"]),
            op_count=len(rows),
            sequence=tuple(row["coarse_type_length_bucket"] for row in rows),
            tape_symbols=tuple(tape_symbols),
            composition_rank_fraction=float(rows[0]["composition_rank_fraction"]),
            composition_count=int(rows[0]["composition_count"]),
            composition_bits=float(sum(row["composition_index_bits_charged_here"] for row in rows)),
        )
    return result


def train_macros(train_books: list[BookIR]) -> list[tuple[str, ...]]:
    counts: Counter[tuple[str, ...]] = Counter()
    for book in train_books:
        seq = book.sequence
        for length in range(MACRO_MIN_LEN, MACRO_MAX_LEN + 1):
            for start in range(0, max(0, len(seq) - length + 1)):
                counts[seq[start : start + length]] += 1
    candidates = [
        (macro, (len(macro) - 1) * count, count)
        for macro, count in counts.items()
        if count >= MACRO_MIN_COUNT
    ]
    candidates.sort(key=lambda item: (-item[1], -len(item[0]), item[0]))
    selected: list[tuple[str, ...]] = []
    seen = set()
    for macro, _, _ in candidates:
        if macro not in seen:
            selected.append(macro)
            seen.add(macro)
        if len(selected) >= MACRO_LIMIT:
            break
    return selected


def greedy_macro_encode(sequence: tuple[str, ...], macros: list[tuple[str, ...]]) -> list[tuple[str, ...]]:
    macros_by_len = sorted(macros, key=lambda item: (-len(item), item))
    encoded = []
    index = 0
    while index < len(sequence):
        match = None
        for macro in macros_by_len:
            if sequence[index : index + len(macro)] == macro:
                match = macro
                break
        if match is None:
            match = (sequence[index],)
        encoded.append(match)
        index += len(match)
    return encoded


def macro_program_score(train_books: list[BookIR], test_books: list[BookIR]) -> dict:
    macros = train_macros(train_books)
    grammar_bits = sum(len(macro) * COARSE_BITS for macro in macros)
    vocab_bits = log2(len(COARSE_VOCAB) + len(macros)) if macros else COARSE_BITS
    emitted = []
    exact_books_without_terminals = 0
    nontrivial_exact_books_without_terminals = 0
    exact_ops_without_terminals = 0
    for book in test_books:
        encoded = greedy_macro_encode(book.sequence, macros)
        emitted.extend(encoded)
        if len(encoded) == 1 and encoded[0] in macros:
            exact_books_without_terminals += 1
            exact_ops_without_terminals += len(book.sequence)
            if len(book.sequence) > 1:
                nontrivial_exact_books_without_terminals += 1
    program_bits = grammar_bits + len(emitted) * vocab_bits
    baseline_bits = sum(len(book.sequence) * COARSE_BITS for book in test_books)
    return {
        "baseline_bits": baseline_bits,
        "emitted_symbols": len(emitted),
        "exact_books_without_terminals": exact_books_without_terminals,
        "exact_ops_without_terminals": exact_ops_without_terminals,
        "grammar_bits": grammar_bits,
        "macro_count": len(macros),
        "nontrivial_exact_books_without_terminals": nontrivial_exact_books_without_terminals,
        "program_bits": program_bits,
        "saving_bits": baseline_bits - program_bits,
        "test_books": len(test_books),
        "test_ops": sum(len(book.sequence) for book in test_books),
    }


def train_templates(train_books: list[BookIR]) -> dict[tuple[str, str], tuple[str, ...]]:
    groups: dict[tuple[str, str], Counter[tuple[str, ...]]] = defaultdict(Counter)
    for book in train_books:
        key = (book_length_bucket(book.book_length), op_count_bucket(book.op_count))
        groups[key][book.sequence] += 1
    return {
        key: sorted(counter.items(), key=lambda item: (-item[1], item[0]))[0][0]
        for key, counter in groups.items()
    }


def template_program_score(train_books: list[BookIR], test_books: list[BookIR]) -> dict:
    templates = train_templates(train_books)
    grammar_bits = sum(len(sequence) * COARSE_BITS for sequence in templates.values())
    corrections_bits = 0.0
    exact_books = 0
    nontrivial_exact_books = 0
    exact_ops = 0
    predicted_books = 0
    for book in test_books:
        key = (book_length_bucket(book.book_length), op_count_bucket(book.op_count))
        predicted = templates.get(key)
        if predicted is None:
            corrections_bits += len(book.sequence) * COARSE_BITS
            continue
        predicted_books += 1
        if predicted == book.sequence:
            exact_books += 1
            exact_ops += len(book.sequence)
            if len(book.sequence) > 1:
                nontrivial_exact_books += 1
        else:
            corrections_bits += len(book.sequence) * COARSE_BITS
    program_bits = grammar_bits + corrections_bits
    baseline_bits = sum(len(book.sequence) * COARSE_BITS for book in test_books)
    return {
        "baseline_bits": baseline_bits,
        "correction_bits": corrections_bits,
        "exact_books_without_sequence_atlas": exact_books,
        "exact_ops_without_sequence_atlas": exact_ops,
        "grammar_bits": grammar_bits,
        "nontrivial_exact_books_without_sequence_atlas": nontrivial_exact_books,
        "predicted_books": predicted_books,
        "program_bits": program_bits,
        "saving_bits": baseline_bits - program_bits,
        "template_count": len(templates),
        "test_books": len(test_books),
        "test_ops": sum(len(book.sequence) for book in test_books),
    }


def train_tape_context_model(train_books: list[BookIR]) -> tuple[dict[tuple[str, ...], Counter], Counter, set[str]]:
    counts: dict[tuple[str, ...], Counter] = defaultdict(Counter)
    global_counts: Counter = Counter()
    vocab = set()
    for book in train_books:
        prev = "<BOS>"
        for index, symbol in enumerate(book.tape_symbols):
            coarse = book.sequence[index]
            key = (prev, coarse, position_bucket(index, book.op_count), op_count_bucket(book.op_count))
            counts[key][symbol] += 1
            global_counts[symbol] += 1
            vocab.add(symbol)
            prev = symbol
    return dict(counts), global_counts, vocab


def tape_context_score(train_books: list[BookIR], test_books: list[BookIR]) -> dict:
    counts, global_counts, vocab = train_tape_context_model(train_books)
    vocab_size = max(1, len(vocab))
    model_bits = 0.0
    uniform_bits = 0.0
    top1_hits = 0
    total_symbols = 0
    for book in test_books:
        prev = "<BOS>"
        for index, symbol in enumerate(book.tape_symbols):
            coarse = book.sequence[index]
            key = (prev, coarse, position_bucket(index, book.op_count), op_count_bucket(book.op_count))
            selected = counts.get(key, global_counts)
            total = sum(selected.values())
            prob = (selected.get(symbol, 0) + ALPHA) / (total + ALPHA * vocab_size)
            model_bits += -log2(max(prob, 1e-300))
            uniform_bits += log2(vocab_size)
            if selected:
                best = sorted(selected.items(), key=lambda item: (-item[1], item[0]))[0][0]
                if best == symbol:
                    top1_hits += 1
            prev = symbol
            total_symbols += 1
    return {
        "model_bits": model_bits,
        "saving_bits": uniform_bits - model_bits,
        "symbol_top1_hits": top1_hits,
        "test_symbols": total_symbols,
        "uniform_bits": uniform_bits,
        "vocab_size": vocab_size,
    }


def split_rows(book_ir: dict[int, BookIR]) -> list[tuple[str, list[int], list[int]]]:
    books = sorted(book_ir)
    rows = []
    for cutoff in CUTOFFS:
        train = [book for book in books if book < cutoff]
        test = [book for book in books if book >= cutoff]
        rows.append((f"prefix_{cutoff}", train, test))
    for label, test_set in sorted(load_families().items()):
        test = sorted(book for book in test_set if book in book_ir)
        train = sorted(book for book in books if book not in test_set)
        if train and test:
            rows.append((f"family_{label}", train, test))
    return rows


def score_split(book_ir: dict[int, BookIR], train_ids: list[int], test_ids: list[int]) -> dict:
    train_books = [book_ir[book] for book in train_ids]
    test_books = [book_ir[book] for book in test_ids]
    macro = macro_program_score(train_books, test_books)
    template = template_program_score(train_books, test_books)
    coupling = tape_context_score(train_books, test_books)
    separated_bits = sum(
        len(book.sequence) * COARSE_BITS + book.composition_bits
        for book in test_books
    )
    best_program_bits = min(macro["program_bits"], template["program_bits"]) + sum(
        book.composition_bits for book in test_books
    )
    return {
        "coupling": coupling,
        "macro": macro,
        "program_reduction_vs_separated_control_plus_composition_bits": separated_bits - best_program_bits,
        "separated_control_plus_composition_bits": separated_bits,
        "template": template,
        "test_books": len(test_books),
        "test_ops": sum(book.op_count for book in test_books),
        "train_books": len(train_books),
    }


def shuffled_sequence_control(book_ir: dict[int, BookIR], train_ids: list[int], test_ids: list[int], rng: random.Random) -> float:
    fake_ir = dict(book_ir)
    for book in test_ids:
        original = book_ir[book]
        seq = list(original.sequence)
        rng.shuffle(seq)
        fake_ir[book] = BookIR(
            book=original.book,
            book_length=original.book_length,
            op_count=original.op_count,
            sequence=tuple(seq),
            tape_symbols=original.tape_symbols,
            composition_rank_fraction=original.composition_rank_fraction,
            composition_count=original.composition_count,
            composition_bits=original.composition_bits,
        )
    scored = score_split(fake_ir, train_ids, test_ids)
    return scored["program_reduction_vs_separated_control_plus_composition_bits"]


def permuted_train_control(book_ir: dict[int, BookIR], train_size: int, rng: random.Random) -> float:
    books = sorted(book_ir)
    train_ids = sorted(rng.sample(books, train_size))
    test_ids = [book for book in books if book not in set(train_ids)]
    if not test_ids:
        return 0.0
    scored = score_split(book_ir, train_ids, test_ids)
    return scored["program_reduction_vs_separated_control_plus_composition_bits"]


def run_macro_gate(ledger: dict) -> dict:
    book_ir = make_book_ir(ledger)
    rng = random.Random(469)
    rows = []
    totals = Counter()
    shuffled_savings = []
    permuted_savings = []
    for label, train_ids, test_ids in split_rows(book_ir):
        scored = score_split(book_ir, train_ids, test_ids)
        for key in (
            "program_reduction_vs_separated_control_plus_composition_bits",
            "separated_control_plus_composition_bits",
        ):
            totals[key] += scored[key]
        for family in ("macro", "template"):
            for key, value in scored[family].items():
                if isinstance(value, (int, float)):
                    totals[f"{family}_{key}"] += value
        for key, value in scored["coupling"].items():
            if isinstance(value, (int, float)):
                totals[f"coupling_{key}"] += value
        rows.append({"label": label, "test_ids": test_ids, "train_ids": train_ids, **scored})

        for _ in range(RANDOM_TRIALS):
            shuffled_savings.append(shuffled_sequence_control(book_ir, train_ids, test_ids, rng))
        if label.startswith("prefix_"):
            for _ in range(RANDOM_TRIALS):
                permuted_savings.append(permuted_train_control(book_ir, len(train_ids), rng))

    shuffled_p95 = sorted(shuffled_savings)[int(0.95 * (len(shuffled_savings) - 1))] if shuffled_savings else 0.0
    permuted_p95 = sorted(permuted_savings)[int(0.95 * (len(permuted_savings) - 1))] if permuted_savings else 0.0
    total_reduction = totals["program_reduction_vs_separated_control_plus_composition_bits"]
    exact_books = totals["template_exact_books_without_sequence_atlas"] + totals["macro_exact_books_without_terminals"]
    exact_ops = totals["template_exact_ops_without_sequence_atlas"] + totals["macro_exact_ops_without_terminals"]
    nontrivial_exact_books = (
        totals["template_nontrivial_exact_books_without_sequence_atlas"]
        + totals["macro_nontrivial_exact_books_without_terminals"]
    )
    promoted = total_reduction > 0 and total_reduction > shuffled_p95 and total_reduction > permuted_p95
    # Exact hits are reported but not promoted by themselves here: this gate has
    # no exact-hit control that proves nontrivial generation above trivial one-op
    #/template reuse. Promotion therefore requires paid ledger reduction.
    exact_promoted = False
    classification = (
        "PROMOTED_MINIMAL_EXTERNAL_TAPE_PROGRAM"
        if promoted or exact_promoted
        else "minimal_external_tape_program_not_promoted"
    )
    return {
        "case_reopened": False,
        "classification": classification,
        "compression_bound_status": "unchanged",
        "controls": {
            "permuted_order_reduction_p95": permuted_p95,
            "random_trials": RANDOM_TRIALS,
            "same_multiset_shuffled_reduction_p95": shuffled_p95,
        },
        "decision": {
            "row0_status": "unchanged_exogenous",
            "promoted": classification == "PROMOTED_MINIMAL_EXTERNAL_TAPE_PROGRAM",
        },
        "inputs": {
            "contract": rel(CONTRACT_JSON),
            "ledger": rel(LEDGER_JSON),
            "macro_limit": MACRO_LIMIT,
            "macro_max_len": MACRO_MAX_LEN,
            "macro_min_count": MACRO_MIN_COUNT,
            "macro_min_len": MACRO_MIN_LEN,
        },
        "plaintext_claim": False,
        "rows": rows,
        "schema": "minimal_external_tape_macro_program_gate.v1",
        "scope": "analysis_only_minimal_external_tape_program",
        "summary": {
            "coupling_saving_bits": totals["coupling_saving_bits"],
            "macro_saving_bits": totals["macro_saving_bits"],
            "program_reduction_vs_separated_control_plus_composition_bits": total_reduction,
            "template_exact_books_without_sequence_atlas": totals["template_exact_books_without_sequence_atlas"],
            "template_exact_ops_without_sequence_atlas": totals["template_exact_ops_without_sequence_atlas"],
            "template_nontrivial_exact_books_without_sequence_atlas": totals[
                "template_nontrivial_exact_books_without_sequence_atlas"
            ],
            "template_saving_bits": totals["template_saving_bits"],
            "total_exact_books_without_atlas_or_terminals": exact_books,
            "total_exact_ops_without_atlas_or_terminals": exact_ops,
            "total_nontrivial_exact_books_without_atlas_or_terminals": nontrivial_exact_books,
        },
        "translation_delta": "NONE",
    }


def write_gate_md(result: dict) -> None:
    s = result["summary"]
    c = result["controls"]
    lines = [
        "# Macro Program Gate",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "Plaintext claim: `False`",
        "Case reopened: `False`",
        "",
        "## Purpose",
        "",
        "Test whether a macro/template program over the unified external tapes "
        "reduces the declared residual ledger after paying grammar and corrections.",
        "",
        "## Summary",
        "",
        f"- Program reduction vs separated coarse+composition ledger: `{s['program_reduction_vs_separated_control_plus_composition_bits']:.3f}` bits.",
        f"- Macro saving before composition carry-through: `{s['macro_saving_bits']:.3f}` bits.",
        f"- Template saving before composition carry-through: `{s['template_saving_bits']:.3f}` bits.",
        f"- Coupling bucket-stream saving: `{s['coupling_saving_bits']:.3f}` bits.",
        f"- Exact books generated by templates/macros without sequence atlas: `{s['total_exact_books_without_atlas_or_terminals']}`.",
        f"- Nontrivial exact books generated without sequence atlas: `{s['total_nontrivial_exact_books_without_atlas_or_terminals']}`.",
        f"- Exact ops generated by templates/macros without sequence atlas: `{s['total_exact_ops_without_atlas_or_terminals']}`.",
        f"- Same-multiset shuffled p95: `{c['same_multiset_shuffled_reduction_p95']:.3f}` bits.",
        f"- Permuted-order p95: `{c['permuted_order_reduction_p95']:.3f}` bits.",
        "",
        "| Split | Test Books | Test Ops | Macro Saving | Template Saving | Coupling Saving | Program Reduction |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in result["rows"]:
        lines.append(
            f"| `{row['label']}` | `{row['test_books']}` | `{row['test_ops']}` | "
            f"`{row['macro']['saving_bits']:.3f}` | `{row['template']['saving_bits']:.3f}` | "
            f"`{row['coupling']['saving_bits']:.3f}` | "
            f"`{row['program_reduction_vs_separated_control_plus_composition_bits']:.3f}` |"
        )
    lines.extend(["", "## Decision", ""])
    if result["classification"] == "PROMOTED_MINIMAL_EXTERNAL_TAPE_PROGRAM":
        lines.append(
            "The unified program is promoted because it reduces the external ledger "
            "above controls after paying grammar and corrections."
        )
    else:
        lines.append(
            "`minimal_external_tape_program_not_promoted`: the executable decoder "
            "contract is valid and the ledger is unified, but the macro/template "
            "program does not reduce the paid external tapes above controls."
        )
    lines.extend(
        [
            "",
            "## Fields Still External",
            "",
            "- seed books `0..9`",
            "- coarse control stream when macro/template misses",
            "- book-level composition index",
            "- literal innovation payload tape",
            "- copy hint rank/source tape",
            "- correction tape for macro/template misses",
            "- `row0`",
        ]
    )
    GATE_MD.write_text("\n".join(lines) + "\n")


def main() -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    books = {str(key): value for key, value in load_json(BOOKS_PATH).items()}
    by_book = load_control_rows()
    composition = load_composition_rows()

    contract = make_contract(books, by_book)
    CONTRACT_JSON.write_text(json.dumps(contract, indent=2, sort_keys=True) + "\n")
    write_contract_md(contract)

    ledger = make_unified_ledger(books, by_book, composition)
    LEDGER_JSON.write_text(json.dumps(ledger, indent=2, sort_keys=True) + "\n")
    write_ledger_md(ledger)

    gate = run_macro_gate(ledger)
    GATE_JSON.write_text(json.dumps(gate, indent=2, sort_keys=True) + "\n")
    write_gate_md(gate)


if __name__ == "__main__":
    main()
