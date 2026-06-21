from __future__ import annotations

import copy
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
    / "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_source_path_optimized_formula_469.json"
)
OUT_FORMULA = (
    AUTHORIAL
    / "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_source_substitution_frontier_formula_469.json"
)
BOOKS_DIGITS = ROOT / "analysis" / "audit_20260609" / "books_digits.json"
COMPILE_134 = AUTHORIAL / "scripts" / "134_op_type_derived_recipe_compile.py"
GATE39_SCRIPT = HERE / "scripts" / "39_multicutoff_source_choice_optimizer_gate.py"
GATE41_RESULT = TEST_RESULTS / "41_full_corpus_source_path_formula_gate.json"

ACTIVE_TOTAL_KEY = (
    "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_source_path_optimized_bits"
)
OUT_TOTAL_KEY = (
    "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_source_substitution_frontier_bits"
)
DECLARATION_BITS = 12.0


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


def normalize_ops_flexible(formula: dict[str, Any]) -> dict[str, Any]:
    out = copy.deepcopy(formula)
    for book in map(str, out["policy"]["book_order"]):
        for op in out["book_recipes"][book]["ops"]:
            if "text" in op and "source_digit_pos" not in op:
                op["type"] = "literal"
                op["length"] = len(op["text"])
            elif "source_digit_pos" in op and "length" in op and "text" not in op:
                op["type"] = "copy"
            else:
                raise RuntimeError({"type": "cannot_normalize_op", "book": book, "op": op})
    return out


def build_source_events(
    *,
    formula: dict[str, Any],
    books: dict[str, str],
    gate39,
) -> dict[str, Any]:
    min_len = int(formula["policy"]["min_len"])
    emitted = ""
    events: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    for book in map(str, formula["policy"]["book_order"]):
        target = books[book]
        book_pos = 0
        for op_index, op in enumerate(formula["book_recipes"][book]["ops"]):
            if op["type"] == "literal":
                text = op["text"]
                if target[book_pos : book_pos + len(text)] != text:
                    errors.append({"book": int(book), "op_index": op_index, "type": "literal_mismatch"})
                emitted += text
                book_pos += len(text)
                continue
            if op["type"] != "copy":
                errors.append({"book": int(book), "op_index": op_index, "type": "bad_op"})
                continue

            source = int(op["source_digit_pos"])
            length = int(op["length"])
            legal_source_count = max(1, len(emitted) - min_len + 1)
            chunk = emitted[source : source + length]
            if target[book_pos : book_pos + length] != chunk:
                errors.append({"book": int(book), "op_index": op_index, "type": "copy_mismatch"})
            candidates = gate39.legal_sources_for_chunk(
                emitted=emitted,
                chunk=chunk,
                legal_source_count=legal_source_count,
            )
            if source not in candidates:
                candidates.append(source)
            events.append(
                {
                    "event_index": len(events),
                    "book": int(book),
                    "op_index": op_index,
                    "book_pos": book_pos,
                    "source_digit_pos": source,
                    "length": length,
                    "legal_source_count": legal_source_count,
                    "candidates": sorted(set(candidates)),
                }
            )
            emitted += chunk
            book_pos += length
        if book_pos != len(target):
            errors.append(
                {
                    "book": int(book),
                    "type": "book_length_mismatch",
                    "decoded_length": book_pos,
                    "target_length": len(target),
                }
            )
    return {"events": events, "errors": errors}


def rows_for_sources(events: list[dict[str, Any]], sources: list[int]) -> list[dict[str, Any]]:
    previous_source = None
    previous_length = None
    rows = []
    for event, source in zip(events, sources):
        legal_source_count = int(event["legal_source_count"])
        if not 0 <= source < legal_source_count:
            raise RuntimeError({"type": "illegal_source", "event": event, "source": source})
        if previous_source is None or previous_length is None:
            default = 0
        else:
            candidate = previous_source + previous_length
            default = candidate if candidate < legal_source_count else 0
        rows.append(
            {
                "book": event["book"],
                "op_index": event["op_index"],
                "book_pos": event["book_pos"],
                "source_digit_pos": source,
                "length": event["length"],
                "legal_source_count": legal_source_count,
                "previous_source_plus_length_default": default,
                "source_equals_default": source == default,
            }
        )
        previous_source = source
        previous_length = int(event["length"])
    return rows


class Fenwick:
    def __init__(self, size: int) -> None:
        self.size = size
        self.tree = [0.0] * (size + 1)

    def add(self, index: int, value: float) -> None:
        cursor = index + 1
        while cursor <= self.size:
            self.tree[cursor] += value
            cursor += cursor & -cursor

    def prefix(self, count: int) -> float:
        cursor = min(count, self.size)
        total = 0.0
        while cursor > 0:
            total += self.tree[cursor]
            cursor -= cursor & -cursor
        return total

    def get(self, index: int) -> float:
        return self.prefix(index + 1) - self.prefix(index)


def score_sources(
    events: list[dict[str, Any]],
    sources: list[int],
    *,
    include_rows: bool = False,
) -> dict[str, Any]:
    max_source_count = max(int(event["legal_source_count"]) for event in events) + 1
    exception_counts = Fenwick(max_source_count + 1)
    flag_counts = {True: 0.0, False: 0.0}
    flag_bits = 0.0
    exception_bits = 0.0
    default_count = 0
    exception_count = 0
    previous_source = None
    previous_length = None

    for event, source in zip(events, sources):
        legal_source_count = int(event["legal_source_count"])
        if previous_source is None or previous_length is None:
            default = 0
        else:
            candidate_default = previous_source + previous_length
            default = candidate_default if candidate_default < legal_source_count else 0
        is_default = source == default
        flag_probability = (flag_counts[is_default] + 1.0) / (
            flag_counts[True] + flag_counts[False] + 2.0
        )
        flag_bits += -math.log2(flag_probability)
        flag_counts[is_default] += 1.0

        if is_default:
            default_count += 1
        else:
            exception_count += 1
            if not 0 <= source < legal_source_count:
                raise RuntimeError(
                    {"type": "illegal_source", "event": event, "source": source}
                )
            alphabet_size = legal_source_count - (
                1 if 0 <= default < legal_source_count else 0
            )
            if alphabet_size <= 0:
                raise RuntimeError({"type": "empty_exception_alphabet", "event": event})
            total = exception_counts.prefix(legal_source_count)
            if 0 <= default < legal_source_count:
                total -= exception_counts.get(default)
            probability = (exception_counts.get(source) + 1.0) / (
                total + alphabet_size
            )
            exception_bits += -math.log2(probability)
            exception_counts.add(source, 1.0)

        previous_source = source
        previous_length = int(event["length"])

    stream_bits = flag_bits + exception_bits
    model = {
        "family": "previous_source_plus_length_default_with_global_adaptive_exception_source",
        "default_rule": "previous copy source plus previous copy length if legal, else 0",
        "flag_context": "global",
        "exception_source_context": "global",
        "alpha": 1,
        "flag_bits": flag_bits,
        "exception_source_bits": exception_bits,
        "stream_bits": stream_bits,
        "default_count": default_count,
        "exception_count": exception_count,
        "decodable": True,
    }
    return {
        "rows": rows_for_sources(events, sources) if include_rows else [],
        "model": model,
        "copy_source_bits": float(model["stream_bits"]) + DECLARATION_BITS,
    }


def apply_substitutions(formula: dict[str, Any], substitutions: list[dict[str, Any]]) -> dict[str, Any]:
    candidate = copy.deepcopy(formula)
    for substitution in substitutions:
        book = str(substitution["book"])
        op_index = int(substitution["op_index"])
        candidate["book_recipes"][book]["ops"][op_index]["source_digit_pos"] = int(
            substitution["candidate_source"]
        )
    return candidate


def summarize_substitution(
    event: dict[str, Any],
    candidate_source: int,
    *,
    source_bits: float,
    gain_bits: float,
) -> dict[str, Any]:
    return {
        "event_index": event["event_index"],
        "book": event["book"],
        "op_index": event["op_index"],
        "length": event["length"],
        "candidate_count": len(event["candidates"]),
        "original_source": event["source_digit_pos"],
        "candidate_source": candidate_source,
        "copy_source_bits": source_bits,
        "gain_bits": gain_bits,
    }


def make_result() -> dict[str, Any]:
    gate41_result = load_json(GATE41_RESULT)
    assert_boundary("full_corpus_source_path_formula_gate", gate41_result)
    gate39 = load_module("gate39_source_choice", GATE39_SCRIPT)

    formula = normalize_ops_flexible(load_json(SOURCE_FORMULA))
    books = {str(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    active_total_bits = float(formula["mdl_estimate_rough"][ACTIVE_TOTAL_KEY])
    active_copy_source_bits = float(formula["mdl_estimate_rough"]["copy_source_default_exception_bits"])
    event_data = build_source_events(formula=formula, books=books, gate39=gate39)
    if event_data["errors"]:
        raise RuntimeError(event_data["errors"])
    events = event_data["events"]
    base_sources = [int(event["source_digit_pos"]) for event in events]
    active_score = score_sources(events, base_sources)
    if not math.isclose(active_score["copy_source_bits"], active_copy_source_bits, abs_tol=1e-9):
        raise RuntimeError(
            {
                "type": "active_score_mismatch",
                "formula": active_copy_source_bits,
                "rescored": active_score["copy_source_bits"],
            }
        )

    alternatives: list[tuple[int, int]] = []
    for event in events:
        for source in event["candidates"]:
            if source != event["source_digit_pos"]:
                alternatives.append((int(event["event_index"]), int(source)))

    best = {
        "arity": 0,
        "substitutions": [],
        "copy_source_bits": active_copy_source_bits,
        "gain_bits": 0.0,
        "model": active_score["model"],
    }
    positive_single_count = 0
    single_rows = []
    for event_index, source in alternatives:
        candidate_sources = list(base_sources)
        candidate_sources[event_index] = source
        score = score_sources(events, candidate_sources)
        gain = active_copy_source_bits - score["copy_source_bits"]
        row = summarize_substitution(
            events[event_index],
            source,
            source_bits=score["copy_source_bits"],
            gain_bits=gain,
        )
        single_rows.append(row)
        if gain > 0:
            positive_single_count += 1
        if gain > best["gain_bits"]:
            best = {
                "arity": 1,
                "substitutions": [row],
                "copy_source_bits": score["copy_source_bits"],
                "gain_bits": gain,
                "model": score["model"],
            }

    pair_count = 0
    positive_pair_count = 0
    best_pair_rows = []
    for left_index, (event_a, source_a) in enumerate(alternatives):
        for event_b, source_b in alternatives[left_index + 1 :]:
            if event_a == event_b:
                continue
            pair_count += 1
            candidate_sources = list(base_sources)
            candidate_sources[event_a] = source_a
            candidate_sources[event_b] = source_b
            score = score_sources(events, candidate_sources)
            gain = active_copy_source_bits - score["copy_source_bits"]
            if gain > 0:
                positive_pair_count += 1
            if gain > best["gain_bits"]:
                first = summarize_substitution(
                    events[event_a],
                    source_a,
                    source_bits=score["copy_source_bits"],
                    gain_bits=gain,
                )
                second = summarize_substitution(
                    events[event_b],
                    source_b,
                    source_bits=score["copy_source_bits"],
                    gain_bits=gain,
                )
                best = {
                    "arity": 2,
                    "substitutions": [first, second],
                    "copy_source_bits": score["copy_source_bits"],
                    "gain_bits": gain,
                    "model": score["model"],
                }
                best_pair_rows = [first, second]

    candidate_total_bits = active_total_bits - best["gain_bits"]
    classification = (
        "full_corpus_source_substitution_frontier_improves_bound"
        if best["gain_bits"] > 0
        else "full_corpus_source_substitution_frontier_closed"
    )
    candidate_output_formula = None
    if best["gain_bits"] > 0:
        candidate_formula = apply_substitutions(formula, best["substitutions"])
        candidate_formula["classification"] = classification
        candidate_formula["source_formula"] = rel(SOURCE_FORMULA)
        candidate_formula["source_substitution_frontier_compile"] = {
            "searched_single_substitutions": len(alternatives),
            "searched_pair_substitutions": pair_count,
            "positive_single_count": positive_single_count,
            "positive_pair_count": positive_pair_count,
            "best_arity": best["arity"],
            "best_gain_bits": best["gain_bits"],
            "best_copy_source_bits": best["copy_source_bits"],
            "best_stream_bits": best["model"]["stream_bits"],
            "best_flag_bits": best["model"]["flag_bits"],
            "best_exception_source_bits": best["model"]["exception_source_bits"],
            "best_default_count": best["model"]["default_count"],
            "best_exception_count": best["model"]["exception_count"],
            "active_copy_source_bits": active_copy_source_bits,
            "substitutions": best["substitutions"],
        }
        candidate_formula["policy"] = {
            **candidate_formula["policy"],
            "copy_source_substitution_frontier": {
                "source": "42_full_corpus_source_substitution_frontier_gate",
                "scope": "single and pair same-chunk legal source substitutions; segmentation and copy lengths fixed",
                "adaptive_rescore": True,
            },
        }
        candidate_formula["mdl_estimate_rough"] = {
            **candidate_formula["mdl_estimate_rough"],
            OUT_TOTAL_KEY: candidate_total_bits,
            "previous_source_path_optimized_bits": active_total_bits,
            "gain_vs_previous_source_path_optimized_bits": best["gain_bits"],
            "copy_source_substitution_frontier_bits": best["copy_source_bits"],
            "copy_source_substitution_frontier_stream_bits": best["model"]["stream_bits"],
            "copy_source_substitution_frontier_flag_bits": best["model"]["flag_bits"],
            "copy_source_substitution_frontier_source_bits": best["model"][
                "exception_source_bits"
            ],
            "copy_source_default_exception_bits": best["copy_source_bits"],
            "copy_source_default_exception_stream_bits": best["model"]["stream_bits"],
            "copy_source_default_exception_flag_bits": best["model"]["flag_bits"],
            "copy_source_default_exception_source_bits": best["model"][
                "exception_source_bits"
            ],
            "copy_address_bits": best["copy_source_bits"],
        }
        candidate_formula["boundary"] = {
            **candidate_formula["boundary"],
            "translation_delta": "NONE",
            "row0_origin_changed": False,
            "semantic_delta": "NONE",
            "authorial_intent_claim": False,
        }
        OUT_FORMULA.write_text(
            json.dumps(candidate_formula, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        candidate_output_formula = rel(OUT_FORMULA)

    return {
        "schema": "full_corpus_source_substitution_frontier_gate.v1",
        "classification": classification,
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "source_formula": rel(SOURCE_FORMULA),
            "books_digits": rel(BOOKS_DIGITS),
            "gate41_result": rel(GATE41_RESULT),
        },
        "candidate_output_formula": candidate_output_formula,
        "scope": {
            "searched_single_substitutions": True,
            "searched_pair_substitutions": True,
            "same_chunk_source_choices_only": True,
            "fixed_segmentation": True,
            "fixed_copy_lengths": True,
            "adaptive_rescore": True,
            "searched_triples_or_higher": False,
        },
        "summary": {
            "active_total_bits": active_total_bits,
            "candidate_total_bits": candidate_total_bits,
            "candidate_gain_bits": best["gain_bits"],
            "active_copy_source_bits": active_copy_source_bits,
            "candidate_copy_source_bits": best["copy_source_bits"],
            "copy_event_count": len(events),
            "candidate_source_option_count": sum(len(event["candidates"]) for event in events),
            "alternative_count": len(alternatives),
            "single_substitution_count": len(alternatives),
            "positive_single_count": positive_single_count,
            "pair_substitution_count": pair_count,
            "positive_pair_count": positive_pair_count,
            "best_arity": best["arity"],
            "best_substitutions": best["substitutions"],
            "top_single_rows": sorted(single_rows, key=lambda row: row["gain_bits"], reverse=True)[:10],
            "best_pair_rows": best_pair_rows,
            "active_default_count": active_score["model"]["default_count"],
            "active_exception_count": active_score["model"]["exception_count"],
            "candidate_default_count": best["model"]["default_count"],
            "candidate_exception_count": best["model"]["exception_count"],
            "candidate_flag_bits": best["model"]["flag_bits"],
            "candidate_exception_source_bits": best["model"]["exception_source_bits"],
            "remaining_blockers": [
                "Only same-chunk source substitutions are searched.",
                "Segmentation and copy lengths remain fixed.",
                "Triples and higher-order source substitutions are not searched in this gate.",
                "Row0 origin remains exogenous.",
            ],
        },
        "decision": {
            "compression_bound_status": (
                "improved_by_source_substitution_frontier"
                if best["gain_bits"] > 0
                else "unchanged_8162_412_source_path_bound"
            ),
            "recipe_discovery_status": "fixed_recipe_source_substitution_frontier_tested",
            "row0_origin_status": "unchanged_exogenous",
            "translation_or_plaintext_status": "NONE",
        },
    }


def write_result(result: dict[str, Any]) -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    (TEST_RESULTS / "42_full_corpus_source_substitution_frontier_gate.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    s = result["summary"]
    lines = [
        "# Full-Corpus Source Substitution Frontier Gate",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Gate 41 promoted a fixed-recipe source-path formula. This gate tests the",
        "next local frontier: every single and pair same-chunk legal source",
        "substitution is rescored under the real adaptive source default/exception",
        "stream. Segmentation and copy lengths remain fixed.",
        "",
        "## Summary",
        "",
        f"- Active total bits: `{s['active_total_bits']:.3f}`.",
        f"- Candidate total bits: `{s['candidate_total_bits']:.3f}`.",
        f"- Candidate gain: `{s['candidate_gain_bits']:+.3f}` bits.",
        f"- Active copy-source bits: `{s['active_copy_source_bits']:.3f}`.",
        f"- Candidate copy-source bits: `{s['candidate_copy_source_bits']:.3f}`.",
        f"- Copy events: `{s['copy_event_count']}`.",
        f"- Candidate source options: `{s['candidate_source_option_count']}`.",
        f"- Single substitutions searched: `{s['single_substitution_count']}`.",
        f"- Positive singles: `{s['positive_single_count']}`.",
        f"- Pair substitutions searched: `{s['pair_substitution_count']}`.",
        f"- Positive pairs: `{s['positive_pair_count']}`.",
        f"- Best arity: `{s['best_arity']}`.",
    ]
    if result["candidate_output_formula"]:
        lines.extend(
            [
                "",
                "## Promoted Formula",
                "",
                f"- [{Path(result['candidate_output_formula']).name}](../../../authorial_mechanism_20260620/{Path(result['candidate_output_formula']).name})",
            ]
        )
    lines.extend(
        [
            "",
            "## Best Substitutions",
            "",
            "| Event | Book | Op | Length | Old source | New source | Gain bits |",
            "|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for row in s["best_substitutions"]:
        lines.append(
            f"| `{row['event_index']}` | `{row['book']}` | `{row['op_index']}` | "
            f"`{row['length']}` | `{row['original_source']}` | "
            f"`{row['candidate_source']}` | `{row['gain_bits']:+.3f}` |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "This is a local source frontier, not a complete parser. It can promote a",
            "new compression bound only if a single or pair source substitution",
            "improves the full adaptive source-stream score.",
            "",
            "## Boundary",
            "",
            "- No plaintext, translation, semantic reading, or case reopening is introduced.",
            "- Row0 origin remains unchanged and exogenous.",
            "- Recipe segmentation and copy lengths remain fixed.",
            "- Triple and higher-order source substitutions are outside this gate.",
        ]
    )
    (TEST_RESULTS / "42_full_corpus_source_substitution_frontier_gate.md").write_text(
        "\n".join(lines).rstrip() + "\n",
        encoding="utf-8",
    )


def main() -> None:
    write_result(make_result())


if __name__ == "__main__":
    main()
