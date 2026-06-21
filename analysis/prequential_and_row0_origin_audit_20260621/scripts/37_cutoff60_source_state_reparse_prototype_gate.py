from __future__ import annotations

import importlib.util
import json
import math
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
TEST_RESULTS = HERE / "reports" / "test_results"
AUTHORIAL = ROOT / "analysis" / "authorial_mechanism_20260620"

SOURCE_FORMULA = (
    AUTHORIAL
    / "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_source_default_exception_formula_469.json"
)
BOOKS_DIGITS = ROOT / "analysis" / "audit_20260609" / "books_digits.json"
COMPILE_134 = AUTHORIAL / "scripts" / "134_op_type_derived_recipe_compile.py"
AUDIT_126 = AUTHORIAL / "scripts" / "126_prequential_recipe_reparse_audit.py"
AUDIT_137 = AUTHORIAL / "scripts" / "137_copy_source_default_decodability_audit.py"
GATE36 = TEST_RESULTS / "36_active_reparse_feasibility_after_state_compression_gate.json"

CUTOFF = 60
DIGITS = [str(index) for index in range(10)]
ITEM_TYPES = ["literal", "copy"]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def assert_boundary(name: str, data: dict[str, Any]) -> None:
    if data.get("translation_delta") != "NONE":
        raise RuntimeError(f"{name} changed translation boundary")
    if data.get("case_reopened", False) is not False:
        raise RuntimeError(f"{name} reopened case")
    if data.get("plaintext_claim", False) is not False:
        raise RuntimeError(f"{name} introduced plaintext")
    decision = data.get("decision", {})
    if decision.get("row0_origin_status") not in {None, "unchanged_exogenous"}:
        raise RuntimeError(f"{name} changed row0 origin")
    if decision.get("translation_or_plaintext_status", "NONE") != "NONE":
        raise RuntimeError(f"{name} introduced plaintext status")


def previous_copy_end_before(formula: dict[str, Any], cutoff: int) -> int | None:
    previous_end = None
    for book in map(str, formula["policy"]["book_order"]):
        if int(book) >= cutoff:
            break
        for op in formula["book_recipes"][book]["ops"]:
            if op["type"] == "copy":
                previous_end = int(op["source_digit_pos"]) + int(op["length"])
    return previous_end


def source_counts(rows: list[dict[str, Any]], *, max_source_count: int) -> dict[str, Any]:
    counts = {"flag": {True: 0.0, False: 0.0}, "exception": {}}
    for row in rows:
        is_default = bool(row["source_equals_default"])
        counts["flag"][is_default] += 1.0
        if not is_default:
            source = int(row["source_digit_pos"])
            counts["exception"][source] = counts["exception"].get(source, 0.0) + 1.0
    prefix = [0.0]
    running = 0.0
    exception = counts["exception"]
    for value in range(max_source_count + 1):
        running += exception.get(value, 0.0)
        prefix.append(running)
    counts["exception_prefix"] = prefix
    return counts


def source_default_exception_bits(
    *,
    source: int,
    legal_source_count: int,
    previous_copy_end: int | None,
    counts: dict[str, Any],
) -> tuple[float, bool, float, float]:
    default = (
        previous_copy_end
        if previous_copy_end is not None and previous_copy_end < legal_source_count
        else 0
    )
    is_default = source == default
    flag_bucket = counts["flag"]
    flag_probability = (flag_bucket[is_default] + 1.0) / (
        flag_bucket[True] + flag_bucket[False] + 2.0
    )
    flag_bits = -math.log2(flag_probability)
    if is_default:
        return flag_bits, True, flag_bits, 0.0

    if not 0 <= source < legal_source_count:
        return float("inf"), False, flag_bits, float("inf")
    exception_bucket = counts["exception"]
    alphabet_size = legal_source_count - (1 if 0 <= default < legal_source_count else 0)
    if alphabet_size <= 0:
        return float("inf"), False, flag_bits, float("inf")
    prefix = counts["exception_prefix"]
    total = prefix[legal_source_count]
    if 0 <= default < legal_source_count:
        total -= exception_bucket.get(default, 0.0)
    probability = (exception_bucket.get(source, 0.0) + 1.0) / (
        total + alphabet_size
    )
    exception_bits = -math.log2(probability)
    return flag_bits + exception_bits, False, flag_bits, exception_bits


def copy_length_prefix_counts(copy_counts: dict[str, dict[int, float]], *, max_length: int) -> dict[str, list[float]]:
    prefixes = {}
    for context, bucket in copy_counts.items():
        prefix = [0.0]
        running = 0.0
        for index in range(max_length + 1):
            running += bucket.get(index, 0.0)
            prefix.append(running)
        prefixes[context] = prefix
    return prefixes


def fast_copy_length_bits(
    *,
    counts: dict[str, dict[int, float]],
    prefixes: dict[str, list[float]],
    context: str,
    length_index: int,
    symbol_count: int,
    alpha: int,
) -> float:
    bucket = counts.get(context, {})
    prefix = prefixes.get(context)
    legal_observations = prefix[symbol_count] if prefix is not None else 0.0
    probability = (bucket.get(length_index, 0.0) + alpha) / (
        legal_observations + alpha * symbol_count
    )
    return -math.log2(probability)


def active_source_state_reparse_book(
    *,
    book: str,
    text: str,
    available: str,
    formula: dict[str, Any],
    train_counts: dict[str, Any],
    source_train_counts: dict[str, Any],
    copy_length_prefixes: dict[str, list[float]],
    initial_previous_copy_end: int | None,
    audit126,
) -> dict[str, Any]:
    min_len = int(formula["policy"]["min_len"])
    literal_length_model = formula["policy"]["literal_run_length_model"]
    payload_model = formula["policy"]["literal_payload_model"]
    copy_model = formula["policy"]["copy_length_model"]
    item_model = formula["policy"]["item_type_model"]

    matches = audit126.precompute_matches(text, available, min_len)
    copy_positions = {pos for pos, row in enumerate(matches) if row}
    n = len(text)
    literal_endpoints = sorted(copy_positions | {n})
    payload_prefix = audit126.literal_payload_prefix_costs(
        text=text,
        emitted_before_book=available,
        payload_counts=train_counts["payload"],
        order=int(payload_model["order"]),
        alpha=float(payload_model["alpha"]),
    )
    end_states = {
        source + length
        for row in matches
        for source, length, _length_index in row
    }
    end_states.add(initial_previous_copy_end)
    previous_end_domain = sorted(end_states, key=lambda value: -1 if value is None else value)
    previous_items = ["BOS", "literal", "copy"]

    dp: dict[tuple[int, str, int | None], float] = {}
    choice: dict[tuple[int, str, int | None], tuple[Any, ...]] = {}
    state_evaluations = 0
    transition_evaluations = 0
    for previous in previous_items:
        for previous_end in previous_end_domain:
            dp[(n, previous, previous_end)] = 0.0

    for pos in range(n - 1, -1, -1):
        remaining = n - pos
        for previous in previous_items:
            for previous_end in previous_end_domain:
                state_evaluations += 1
                best = float("inf")
                best_choice: tuple[Any, ...] | None = None

                literal_forced = previous != "literal" and remaining < min_len
                if literal_forced:
                    literal_lengths = [remaining]
                else:
                    start_idx = audit126.bisect.bisect_right(literal_endpoints, pos)
                    literal_lengths = [end - pos for end in literal_endpoints[start_idx:]]
                if previous != "literal":
                    for length in literal_lengths:
                        next_pos = pos + length
                        transition_evaluations += 1
                        forced = literal_forced
                        cost = (
                            audit126.item_bits_for_choice(
                                forced=forced,
                                item_type="literal",
                                book_int=int(book),
                                item_model=item_model,
                                item_counts=train_counts["item"],
                            )
                            + (0 if forced else audit126.length_bits(length + 1, literal_length_model))
                            + payload_prefix[pos + length]
                            - payload_prefix[pos]
                            + dp[(next_pos, "literal", previous_end)]
                        )
                        if cost < best:
                            best = cost
                            best_choice = ("literal", length, forced)

                if remaining >= min_len:
                    for source_pos, length, length_index in matches[pos]:
                        target_digit_global = len(available) + pos
                        legal_source_count = max(1, target_digit_global - min_len + 1)
                        if source_pos >= legal_source_count:
                            continue
                        max_length = min(remaining, target_digit_global - source_pos)
                        symbol_count = max_length - min_len + 1
                        if symbol_count <= 0 or length_index >= symbol_count:
                            continue
                        new_previous_end = source_pos + length
                        source_bits, is_default, flag_bits, exception_bits = (
                            source_default_exception_bits(
                                source=source_pos,
                                legal_source_count=legal_source_count,
                                previous_copy_end=previous_end,
                                counts=source_train_counts,
                            )
                        )
                        if not math.isfinite(source_bits):
                            continue
                        transition_evaluations += 1
                        forced = previous == "literal"
                        cost = (
                            audit126.item_bits_for_choice(
                                forced=forced,
                                item_type="copy",
                                book_int=int(book),
                                item_model=item_model,
                                item_counts=train_counts["item"],
                            )
                            + source_bits
                            + fast_copy_length_bits(
                                counts=train_counts["copy"],
                                prefixes=copy_length_prefixes,
                                context=audit126.copy_context_key(int(book)),
                                length_index=length_index,
                                symbol_count=symbol_count,
                                alpha=int(copy_model["alpha"]),
                            )
                            + dp[(pos + length, "copy", new_previous_end)]
                        )
                        if cost < best:
                            best = cost
                            best_choice = (
                                "copy",
                                source_pos,
                                length,
                                forced,
                                symbol_count,
                                is_default,
                                flag_bits,
                                exception_bits,
                            )

                dp[(pos, previous, previous_end)] = best
                if best_choice is not None:
                    choice[(pos, previous, previous_end)] = best_choice

    start_key = (0, "BOS", initial_previous_copy_end)
    if not math.isfinite(dp[start_key]):
        raise RuntimeError({"book": book, "type": "no_finite_parse"})

    pos = 0
    previous = "BOS"
    previous_end = initial_previous_copy_end
    local_emitted = available
    rendered = []
    ops = []
    totals = {
        "literal_length_bits": 0.0,
        "literal_payload_bits": 0.0,
        "item_type_stream_bits": 0.0,
        "copy_source_default_exception_bits": 0.0,
        "copy_source_flag_bits": 0.0,
        "copy_source_exception_bits": 0.0,
        "copy_length_stream_bits": 0.0,
        "literal_runs": 0,
        "literal_digits": 0,
        "copy_items": 0,
        "copied_digits": 0,
        "source_default_count": 0,
        "source_exception_count": 0,
        "forced_literals": 0,
        "forced_copies": 0,
    }
    while pos < n:
        item = choice[(pos, previous, previous_end)]
        if item[0] == "literal":
            _kind, length, forced = item
            chunk = text[pos : pos + length]
            if not forced:
                totals["literal_length_bits"] += audit126.length_bits(
                    length + 1, literal_length_model
                )
                totals["item_type_stream_bits"] += audit126.item_bits_for_choice(
                    forced=False,
                    item_type="literal",
                    book_int=int(book),
                    item_model=item_model,
                    item_counts=train_counts["item"],
                )
            else:
                totals["forced_literals"] += 1
            totals["literal_payload_bits"] += payload_prefix[pos + length] - payload_prefix[pos]
            totals["literal_runs"] += 1
            totals["literal_digits"] += length
            ops.append({"type": "literal", "text": chunk, "length": length, "forced": forced})
            rendered.append(chunk)
            local_emitted += chunk
            pos += length
            previous = "literal"
        elif item[0] == "copy":
            (
                _kind,
                source_pos,
                length,
                forced,
                symbol_count,
                is_default,
                flag_bits,
                exception_bits,
            ) = item
            length_index = length - min_len
            chunk = local_emitted[source_pos : source_pos + length]
            if len(chunk) != length:
                raise RuntimeError({"book": book, "type": "short_copy", "source": source_pos})
            if not forced:
                totals["item_type_stream_bits"] += audit126.item_bits_for_choice(
                    forced=False,
                    item_type="copy",
                    book_int=int(book),
                    item_model=item_model,
                    item_counts=train_counts["item"],
                )
            else:
                totals["forced_copies"] += 1
            copy_length_bits = fast_copy_length_bits(
                counts=train_counts["copy"],
                prefixes=copy_length_prefixes,
                context=audit126.copy_context_key(int(book)),
                length_index=length_index,
                symbol_count=int(symbol_count),
                alpha=int(copy_model["alpha"]),
            )
            totals["copy_source_default_exception_bits"] += flag_bits + exception_bits
            totals["copy_source_flag_bits"] += flag_bits
            totals["copy_source_exception_bits"] += exception_bits
            totals["copy_length_stream_bits"] += copy_length_bits
            totals["copy_items"] += 1
            totals["copied_digits"] += length
            if is_default:
                totals["source_default_count"] += 1
            else:
                totals["source_exception_count"] += 1
            ops.append(
                {
                    "type": "copy",
                    "source_digit_pos": int(source_pos),
                    "length": int(length),
                    "target_start": int(pos),
                    "forced": forced,
                    "source_is_default": bool(is_default),
                }
            )
            rendered.append(chunk)
            local_emitted += chunk
            pos += length
            previous = "copy"
            previous_end = source_pos + length
        else:
            raise ValueError(item)

    errors = [] if "".join(rendered) == text else ["book_mismatch"]
    bits = sum(
        totals[key]
        for key in [
            "literal_length_bits",
            "literal_payload_bits",
            "item_type_stream_bits",
            "copy_source_default_exception_bits",
            "copy_length_stream_bits",
        ]
    )
    return {
        "book": book,
        "bits": bits,
        "dp_bits": dp[start_key],
        "ops": ops,
        "final_previous_copy_end": previous_end,
        "state_evaluations": state_evaluations,
        "transition_evaluations": transition_evaluations,
        "previous_end_domain_size": len(previous_end_domain),
        "validation": {"errors": errors, "roundtrip_ok": not errors},
        **totals,
    }


def reprice_encoded_book_source_state(
    *,
    encoded: dict[str, Any],
    available: str,
    formula: dict[str, Any],
    source_train_counts: dict[str, Any],
    initial_previous_copy_end: int | None,
) -> dict[str, Any]:
    min_len = int(formula["policy"]["min_len"])
    local_emitted = available
    previous_end = initial_previous_copy_end
    source_bits = 0.0
    flag_bits = 0.0
    exception_bits = 0.0
    default_count = 0
    exception_count = 0
    rendered = []
    for op in encoded["ops"]:
        if op["type"] == "literal":
            chunk = op["text"]
            local_emitted += chunk
            rendered.append(chunk)
            continue

        source = int(op["source_digit_pos"])
        length = int(op["length"])
        legal_source_count = max(1, len(local_emitted) - min_len + 1)
        bits, is_default, flag, exception = source_default_exception_bits(
            source=source,
            legal_source_count=legal_source_count,
            previous_copy_end=previous_end,
            counts=source_train_counts,
        )
        if not math.isfinite(bits):
            raise RuntimeError(
                {
                    "type": "nonfinite_source_bits",
                    "source": source,
                    "legal_source_count": legal_source_count,
                    "previous_end": previous_end,
                }
            )
        chunk = local_emitted[source : source + length]
        if len(chunk) != length:
            raise RuntimeError({"type": "short_copy", "source": source, "length": length})
        source_bits += bits
        flag_bits += flag
        exception_bits += exception
        if is_default:
            default_count += 1
        else:
            exception_count += 1
        previous_end = source + length
        local_emitted += chunk
        rendered.append(chunk)
    return {
        "source_bits": source_bits,
        "source_flag_bits": flag_bits,
        "source_exception_bits": exception_bits,
        "source_default_count": default_count,
        "source_exception_count": exception_count,
        "final_previous_copy_end": previous_end,
        "rendered": "".join(rendered),
    }


def make_result() -> dict[str, Any]:
    gate36 = load_json(GATE36)
    assert_boundary("active_reparse_feasibility_after_state_compression_gate", gate36)
    if not gate36["summary"]["all_books_below_1m_end_state_proxy"]:
        raise RuntimeError("cutoff60 prototype requires gate36 frontier to be below threshold")

    compile134 = load_module("op_type_compile_134", COMPILE_134)
    audit126 = load_module("audit126", AUDIT_126)
    audit137 = load_module("audit137", AUDIT_137)
    payload_module = load_module("payload_context", audit126.PAYLOAD_CONTEXT)
    copy_module = load_module("copy_context", audit126.COPY_CONTEXT)
    item_module = load_module("item_context", audit126.ITEM_CONTEXT)

    formula = compile134.normalize_ops(load_json(SOURCE_FORMULA))
    books = {str(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    copy_rows = copy_module.collect_copy_rows(formula, books)
    payload_rows = payload_module.collect_literal_digit_rows(formula, books)
    item_rows, item_stats = item_module.collect_item_rows(formula, books)
    if item_stats["forced_rule_violations"]:
        raise RuntimeError(item_stats["forced_rule_violations"])

    train_counts = audit126.train_counts_for_cutoff(
        cutoff=CUTOFF,
        formula=formula,
        copy_rows=copy_rows,
        payload_rows=payload_rows,
        item_rows=item_rows,
    )
    source_rows = audit137.collect_source_rows(formula, books)
    if source_rows["errors"]:
        raise RuntimeError(source_rows["errors"])
    source_train_counts = source_counts(
        [row for row in source_rows["rows"] if int(row["book"]) < CUTOFF],
        max_source_count=sum(len(text) for text in books.values()) + 1,
    )

    available = "".join(books[str(book)] for book in range(CUTOFF))
    previous_end = previous_copy_end_before(formula, CUTOFF)
    book_rows = []
    aggregate = {
        "bits": 0.0,
        "uniform_address_reparse_bits": 0.0,
        "raw_digit_uniform_bits": 0.0,
        "literal_length_bits": 0.0,
        "literal_payload_bits": 0.0,
        "item_type_stream_bits": 0.0,
        "copy_source_default_exception_bits": 0.0,
        "copy_source_flag_bits": 0.0,
        "copy_source_exception_bits": 0.0,
        "copy_length_stream_bits": 0.0,
        "literal_runs": 0,
        "literal_digits": 0,
        "copy_items": 0,
        "copied_digits": 0,
        "source_default_count": 0,
        "source_exception_count": 0,
    }
    errors = []
    for book in range(CUTOFF, 70):
        book_key = str(book)
        uniform = audit126.encode_book_frozen_reparse(
            book=book_key,
            text=books[book_key],
            available=available,
            formula=formula,
            train_counts=train_counts,
        )
        if uniform["validation"]["errors"]:
            errors.extend(
                {"book": book, "error": error}
                for error in uniform["validation"]["errors"]
            )
        repriced = reprice_encoded_book_source_state(
            encoded=uniform,
            available=available,
            formula=formula,
            source_train_counts=source_train_counts,
            initial_previous_copy_end=previous_end,
        )
        if repriced["rendered"] != books[book_key]:
            errors.append({"book": book, "error": "repriced_render_mismatch"})
        bits = (
            float(uniform["bits"])
            - float(uniform["copy_address_bits"])
            + repriced["source_bits"]
        )
        row = {key: value for key, value in uniform.items() if key != "ops"}
        row["bits"] = bits
        row["copy_source_default_exception_bits"] = repriced["source_bits"]
        row["copy_source_flag_bits"] = repriced["source_flag_bits"]
        row["copy_source_exception_bits"] = repriced["source_exception_bits"]
        row["source_default_count"] = repriced["source_default_count"]
        row["source_exception_count"] = repriced["source_exception_count"]
        row["final_previous_copy_end"] = repriced["final_previous_copy_end"]
        row["uniform_address_reparse_bits"] = uniform["bits"]
        row["source_state_minus_uniform_address_bits"] = bits - uniform["bits"]
        row["raw_digit_uniform_bits"] = len(books[book_key]) * math.log2(10)
        row["gain_vs_raw_digit_uniform_bits"] = row["raw_digit_uniform_bits"] - bits
        book_rows.append(row)
        for key in aggregate:
            if key == "uniform_address_reparse_bits":
                aggregate[key] += uniform["bits"]
            elif key == "raw_digit_uniform_bits":
                aggregate[key] += row["raw_digit_uniform_bits"]
            elif key == "bits":
                aggregate[key] += bits
            elif key == "copy_source_default_exception_bits":
                aggregate[key] += repriced["source_bits"]
            elif key == "copy_source_flag_bits":
                aggregate[key] += repriced["source_flag_bits"]
            elif key == "copy_source_exception_bits":
                aggregate[key] += repriced["source_exception_bits"]
            elif key == "source_default_count":
                aggregate[key] += repriced["source_default_count"]
            elif key == "source_exception_count":
                aggregate[key] += repriced["source_exception_count"]
            elif key in uniform:
                aggregate[key] += uniform[key]
        previous_end = repriced["final_previous_copy_end"]
        available += books[book_key]

    aggregate["source_state_minus_uniform_address_bits"] = (
        aggregate["bits"] - aggregate["uniform_address_reparse_bits"]
    )
    aggregate["gain_vs_raw_digit_uniform_bits"] = (
        aggregate["raw_digit_uniform_bits"] - aggregate["bits"]
    )
    aggregate["uniform_address_gain_vs_raw_digit_uniform_bits"] = (
        aggregate["raw_digit_uniform_bits"] - aggregate["uniform_address_reparse_bits"]
    )

    roundtrip_count = sum(1 for row in book_rows if row["validation"]["roundtrip_ok"])
    beats_raw_count = sum(1 for row in book_rows if row["gain_vs_raw_digit_uniform_bits"] > 0)
    beats_uniform_reparse_count = sum(
        1 for row in book_rows if row["source_state_minus_uniform_address_bits"] < 0
    )
    classification = (
        "cutoff60_source_state_reprice_roundtrip_positive_unpromoted"
        if roundtrip_count == len(book_rows) and beats_raw_count == len(book_rows)
        else "cutoff60_source_state_reprice_mixed_unpromoted"
    )

    return {
        "schema": "cutoff60_source_state_reparse_prototype_gate.v1",
        "classification": classification,
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "source_formula": rel(SOURCE_FORMULA),
            "books_digits": rel(BOOKS_DIGITS),
            "gate36": rel(GATE36),
            "audit126": rel(AUDIT_126),
            "audit137": rel(AUDIT_137),
        },
        "scope": {
            "cutoff": CUTOFF,
            "train_books": list(range(CUTOFF)),
            "test_books": list(range(CUTOFF, 70)),
            "prototype_type": "deterministic reparse recipes repriced with previous_copy_end source default ledger",
            "not_recipe_reoptimization": True,
        },
        "summary": {
            "roundtrip_book_count": roundtrip_count,
            "book_count": len(book_rows),
            "beats_raw_book_count": beats_raw_count,
            "beats_uniform_address_reparse_book_count": beats_uniform_reparse_count,
            "aggregate": aggregate,
            "book_rows": book_rows,
            "remaining_blockers": [
                "Only cutoff 60 is repriced in this gate.",
                "The prototype reprices deterministic reparse recipes; it does not reoptimize recipe segmentation under source-state cost.",
                "Non-source component counts and source counts are frozen from the train prefix.",
                "It does not promote a complete active parser or a new compression bound.",
            ],
        },
        "decision": {
            "source_state_reparse_status": "cutoff60_reprice_executable_roundtrips_but_unpromoted",
            "recipe_discovery_status": "source_state_reprice_only_no_recipe_reoptimization",
            "compression_bound_status": "unchanged_8177_317_active_bound",
            "row0_origin_status": "unchanged_exogenous",
            "translation_or_plaintext_status": "NONE",
        },
    }


def write_result(result: dict[str, Any]) -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    (TEST_RESULTS / "37_cutoff60_source_state_reparse_prototype_gate.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    s = result["summary"]
    agg = s["aggregate"]
    lines = [
        "# Cutoff 60 Source-State Reparse Prototype Gate",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Gate 36 showed that `previous_copy_end` makes the source-state frontier",
        "small enough for book-local prototyping by proxy. This gate executes",
        "the first cheaper operational step at cutoff `60`: deterministic reparse",
        "recipes are roundtrip-checked and then repriced with the active",
        "`previous_copy_end` default/exception source ledger. It does not",
        "reoptimize segmentation under source-state cost.",
        "",
        "## Summary",
        "",
        f"- Roundtrip books: `{s['roundtrip_book_count']}/{s['book_count']}`.",
        f"- Books beating raw digit uniform: `{s['beats_raw_book_count']}/{s['book_count']}`.",
        f"- Books beating old uniform-address reparse: `{s['beats_uniform_address_reparse_book_count']}/{s['book_count']}`.",
        f"- Source-state prototype bits: `{agg['bits']:.3f}`.",
        f"- Uniform-address reparse bits on same cutoff: `{agg['uniform_address_reparse_bits']:.3f}`.",
        f"- Source-state minus uniform-address bits: `{agg['source_state_minus_uniform_address_bits']:+.3f}`.",
        f"- Gain versus raw digit uniform: `{agg['gain_vs_raw_digit_uniform_bits']:.3f}` bits.",
        f"- Source defaults/exceptions: `{agg['source_default_count']}` / `{agg['source_exception_count']}`.",
        "",
        "## Book Rows",
        "",
        "| Book | Bits | Uniform-address reparse | Delta | Raw gain | Copy items | Defaults | Exceptions |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in s["book_rows"]:
        lines.append(
            f"| `{row['book']}` | `{row['bits']:.3f}` | "
            f"`{row['uniform_address_reparse_bits']:.3f}` | "
            f"`{row['source_state_minus_uniform_address_bits']:+.3f}` | "
            f"`{row['gain_vs_raw_digit_uniform_bits']:.3f}` | "
            f"`{row['copy_items']}` | `{row['source_default_count']}` | "
            f"`{row['source_exception_count']}` |"
        )

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "The compressed source-state ledger is now executable for the cutoff-60",
            "suffix on deterministic reparse recipes: all ten held-out books",
            "roundtrip and keep positive gain against raw digit coding. This is a",
            "real implementation advance over a pure state proxy.",
            "",
            "It is not a promoted generation method. On this cutoff, charging the",
            "active source default/exception model inside the deterministic reparse",
            "is cheaper in aggregate than the older uniform-address comparator,",
            "but only `4/10` books improve individually and this gate does not",
            "reoptimize the recipes under source-state cost.",
            "",
            "## Boundary",
            "",
            "- No compression-bound change is introduced.",
            "- No complete active parser or global recipe-discovery promotion is introduced.",
            "- Row0 origin remains unchanged and exogenous.",
            "- No plaintext, translation, semantic reading, or case reopening is introduced.",
        ]
    )
    (TEST_RESULTS / "37_cutoff60_source_state_reparse_prototype_gate.md").write_text(
        "\n".join(lines).rstrip() + "\n",
        encoding="utf-8",
    )


def main() -> None:
    write_result(make_result())


if __name__ == "__main__":
    main()
