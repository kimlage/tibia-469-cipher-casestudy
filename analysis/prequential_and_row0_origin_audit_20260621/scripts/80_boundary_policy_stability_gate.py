from __future__ import annotations

import importlib.util
import json
import math
from pathlib import Path
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
TEST_RESULTS = HERE / "reports" / "test_results"

GATE77_SCRIPT = HERE / "scripts" / "77_multi_cutoff_sparse_suffix_parser_validation.py"
GATE78_SCRIPT = HERE / "scripts" / "78_multi_cutoff_parser_path_stability_audit.py"
GATE79 = TEST_RESULTS / "79_unstable_parser_path_decomposition_audit.json"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
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
    if decision.get("row0_origin_status") not in {
        None,
        "unchanged_exogenous",
        "exogenous_under_current_evidence",
    }:
        raise RuntimeError(f"{name} changed row0 origin")
    if decision.get("translation_or_plaintext_status", "NONE") != "NONE":
        raise RuntimeError(f"{name} introduced translation/plaintext")


def op_type_sequence(ops: list[dict[str, Any]]) -> str:
    return "".join("C" if op["type"] == "copy" else "L" for op in ops)


def length_sequence(ops: list[dict[str, Any]]) -> tuple[int, ...]:
    return tuple(int(op["length"]) for op in ops)


def copy_sources(ops: list[dict[str, Any]]) -> tuple[int, ...]:
    return tuple(int(op["source"]) for op in ops if op["type"] == "copy")


def copy_lengths(ops: list[dict[str, Any]]) -> tuple[int, ...]:
    return tuple(int(op["length"]) for op in ops if op["type"] == "copy")


def literal_digits(ops: list[dict[str, Any]]) -> int:
    return sum(int(op["length"]) for op in ops if op["type"] == "literal")


def copied_digits(ops: list[dict[str, Any]]) -> int:
    return sum(int(op["length"]) for op in ops if op["type"] == "copy")


def default_count(ops: list[dict[str, Any]]) -> int:
    return sum(
        1
        for op in ops
        if op["type"] == "copy" and bool(op.get("source_default"))
    )


def variant_key(variant: dict[str, Any]) -> str:
    return str(variant["signature"])


def score_fixed_ops(
    *,
    context: dict[str, Any],
    book: int,
    available: str,
    initial_previous_copy_end: int | None,
    ops: list[dict[str, Any]],
) -> dict[str, Any]:
    gate37 = context["gate37"]
    audit126 = context["audit126"]
    formula = context["formula"]
    train_counts = context["train_counts"]
    source_train_counts = context["source_train_counts"]
    copy_prefixes = context["copy_prefixes"]
    text = context["books"][str(book)]
    min_len = int(formula["policy"]["min_len"])
    literal_length_model = formula["policy"]["literal_run_length_model"]
    payload_model = formula["policy"]["literal_payload_model"]
    copy_model = formula["policy"]["copy_length_model"]
    item_model = formula["policy"]["item_type_model"]
    copy_context = audit126.copy_context_key(book)
    payload_prefix = audit126.literal_payload_prefix_costs(
        text=text,
        emitted_before_book=available,
        payload_counts=train_counts["payload"],
        order=int(payload_model["order"]),
        alpha=float(payload_model["alpha"]),
    )

    bits = 0.0
    position = 0
    previous_item = "BOS"
    previous_end = initial_previous_copy_end
    local_emitted = available
    for op in ops:
        length = int(op["length"])
        if length <= 0 or int(op["target_start"]) != position:
            return {"valid": False, "bits": float("inf"), "reason": "bad_target_or_length"}
        remaining = len(text) - position
        if length > remaining:
            return {"valid": False, "bits": float("inf"), "reason": "over_book_end"}

        if op["type"] == "literal":
            if previous_item == "literal":
                return {"valid": False, "bits": float("inf"), "reason": "adjacent_literal"}
            literal_forced = remaining < min_len
            if literal_forced and length != remaining:
                return {"valid": False, "bits": float("inf"), "reason": "bad_forced_literal_length"}
            next_position = position + length
            bits += payload_prefix[next_position] - payload_prefix[position]
            if not literal_forced:
                bits += audit126.item_bits_for_choice(
                    forced=False,
                    item_type="literal",
                    book_int=book,
                    item_model=item_model,
                    item_counts=train_counts["item"],
                )
                bits += audit126.length_bits(length + 1, literal_length_model)
            local_emitted += text[position:next_position]
            position = next_position
            previous_item = "literal"
            continue

        if op["type"] != "copy":
            return {"valid": False, "bits": float("inf"), "reason": "unknown_op"}

        if remaining < min_len or length < min_len:
            return {"valid": False, "bits": float("inf"), "reason": "short_copy"}
        source = int(op["source"])
        target_digit_global = len(available) + position
        legal_source_count = max(1, target_digit_global - min_len + 1)
        max_length = min(remaining, target_digit_global - source)
        symbol_count = max_length - min_len + 1
        length_index = length - min_len
        if (
            source < 0
            or source >= legal_source_count
            or symbol_count <= 0
            or length_index < 0
            or length_index >= symbol_count
        ):
            return {"valid": False, "bits": float("inf"), "reason": "illegal_copy"}
        copied = local_emitted[source : source + length]
        target = text[position : position + length]
        if copied != target:
            return {"valid": False, "bits": float("inf"), "reason": "copy_mismatch"}
        source_bits, _is_default, _flag_bits, _exception_bits = (
            gate37.source_default_exception_bits(
                source=source,
                legal_source_count=legal_source_count,
                previous_copy_end=previous_end,
                counts=source_train_counts,
            )
        )
        if not math.isfinite(source_bits):
            return {"valid": False, "bits": float("inf"), "reason": "source_inf"}
        forced = previous_item == "literal"
        bits += audit126.item_bits_for_choice(
            forced=forced,
            item_type="copy",
            book_int=book,
            item_model=item_model,
            item_counts=train_counts["item"],
        )
        bits += source_bits
        bits += gate37.fast_copy_length_bits(
            counts=train_counts["copy"],
            prefixes=copy_prefixes,
            context=copy_context,
            length_index=length_index,
            symbol_count=symbol_count,
            alpha=int(copy_model["alpha"]),
        )
        local_emitted += copied
        position += length
        previous_item = "copy"
        previous_end = source + length

    return {
        "valid": position == len(text) and local_emitted.endswith(text),
        "bits": bits if position == len(text) else float("inf"),
        "reason": "ok" if position == len(text) else "incomplete",
        "final_previous_copy_end": previous_end,
    }


def replay_rows_with_initials() -> list[dict[str, Any]]:
    gate77 = load_module("gate77_multi_cutoff_validation", GATE77_SCRIPT)
    gate78 = load_module("gate78_path_stability", GATE78_SCRIPT)
    rows: list[dict[str, Any]] = []
    for cutoff in gate77.CUTOFFS:
        context = gate77.load_parser_context_for_cutoff(cutoff)
        gate37 = context["gate37"]
        formula = context["formula"]
        books = context["books"]
        available = "".join(books[str(index)] for index in range(cutoff))
        previous_end = gate37.previous_copy_end_before(formula, cutoff)
        for book in range(cutoff, 70):
            initial_previous_end = previous_end
            row = gate78.sparse_parse_with_signature(
                context=context,
                book=book,
                available=available,
                initial_previous_copy_end=initial_previous_end,
            )
            row["cutoff"] = cutoff
            row["initial_previous_copy_end"] = initial_previous_end
            row["available_length"] = len(available)
            row["context"] = context
            row["available"] = available
            rows.append(row)
            available += books[str(book)]
            previous_end = row["final_previous_copy_end"]
    return rows


PolicyKey = Callable[[dict[str, Any]], tuple[Any, ...]]


POLICIES: dict[str, PolicyKey] = {
    "lexicographic_length_min": lambda variant: (
        length_sequence(variant["ops"]),
        copy_sources(variant["ops"]),
    ),
    "lexicographic_length_max": lambda variant: (
        tuple(-value for value in length_sequence(variant["ops"])),
        copy_sources(variant["ops"]),
    ),
    "front_loaded_copy_lengths": lambda variant: (
        tuple(-value for value in copy_lengths(variant["ops"])),
        copy_sources(variant["ops"]),
    ),
    "back_loaded_copy_lengths": lambda variant: (
        tuple(-value for value in reversed(copy_lengths(variant["ops"]))),
        copy_sources(variant["ops"]),
    ),
    "earliest_sources": lambda variant: (
        copy_sources(variant["ops"]),
        length_sequence(variant["ops"]),
    ),
    "latest_sources": lambda variant: (
        tuple(-value for value in copy_sources(variant["ops"])),
        length_sequence(variant["ops"]),
    ),
    "fewest_literal_digits": lambda variant: (
        literal_digits(variant["ops"]),
        length_sequence(variant["ops"]),
        copy_sources(variant["ops"]),
    ),
    "most_copied_digits": lambda variant: (
        -copied_digits(variant["ops"]),
        length_sequence(variant["ops"]),
        copy_sources(variant["ops"]),
    ),
    "most_source_defaults": lambda variant: (
        -default_count(variant["ops"]),
        length_sequence(variant["ops"]),
        copy_sources(variant["ops"]),
    ),
}


def choose_policy_variant(
    policy: str,
    variants: list[dict[str, Any]],
    average_bits_by_signature: dict[str, float],
) -> dict[str, Any]:
    if policy == "oracle_min_average_reprice":
        return min(
            variants,
            key=lambda variant: (
                average_bits_by_signature.get(variant_key(variant), float("inf")),
                variant_key(variant),
            ),
        )
    return min(variants, key=POLICIES[policy])


def collect_variants(
    rows: list[dict[str, Any]],
    unstable_books: set[int],
) -> tuple[dict[int, list[dict[str, Any]]], dict[tuple[int, int], dict[str, Any]]]:
    variants_by_book: dict[int, dict[str, dict[str, Any]]] = {
        book: {} for book in unstable_books
    }
    rows_by_cutoff_book: dict[tuple[int, int], dict[str, Any]] = {}
    for row in rows:
        book = int(row["book"])
        if book not in unstable_books:
            continue
        rows_by_cutoff_book[(int(row["cutoff"]), book)] = row
        variants_by_book[book].setdefault(
            row["signature"],
            {
                "signature": row["signature"],
                "ops": row["signature_ops"],
                "cutoffs": [],
                "type_sequence": op_type_sequence(row["signature_ops"]),
                "length_sequence": list(length_sequence(row["signature_ops"])),
                "copy_sources": list(copy_sources(row["signature_ops"])),
                "literal_digits": literal_digits(row["signature_ops"]),
                "copied_digits": copied_digits(row["signature_ops"]),
                "source_default_count": default_count(row["signature_ops"]),
            },
        )
        variants_by_book[book][row["signature"]]["cutoffs"].append(int(row["cutoff"]))
    return (
        {
            book: sorted(
                variants.values(),
                key=lambda variant: (-len(variant["cutoffs"]), variant["cutoffs"][0]),
            )
            for book, variants in variants_by_book.items()
        },
        rows_by_cutoff_book,
    )


def make_result() -> dict[str, Any]:
    gate79 = load_json(GATE79)
    assert_boundary("unstable_parser_path_decomposition", gate79)
    unstable_books = {
        int(row["book"]) for row in gate79["summary"]["book_rows"]
    }
    rows = replay_rows_with_initials()
    variants_by_book, rows_by_cutoff_book = collect_variants(rows, unstable_books)

    book_rows = []
    policy_totals: dict[str, dict[str, float]] = {
        name: {
            "book_count": 0.0,
            "cutoff_observation_count": 0.0,
            "exact_signature_matches": 0.0,
            "valid_observation_count": 0.0,
            "total_regret_bits": 0.0,
            "max_regret_bits": 0.0,
        }
        for name in [*POLICIES, "oracle_min_average_reprice"]
    }

    for book in sorted(unstable_books):
        variants = variants_by_book[book]
        cutoff_rows = sorted(
            (
                row
                for (cutoff, row_book), row in rows_by_cutoff_book.items()
                if row_book == book
            ),
            key=lambda row: int(row["cutoff"]),
        )
        variant_scores: dict[str, dict[str, dict[str, Any]]] = {}
        for variant in variants:
            signature = variant_key(variant)
            variant_scores[signature] = {}
            for row in cutoff_rows:
                scored = score_fixed_ops(
                    context=row["context"],
                    book=book,
                    available=row["available"],
                    initial_previous_copy_end=row["initial_previous_copy_end"],
                    ops=variant["ops"],
                )
                regret = float(scored["bits"]) - float(row["parser_bits"])
                variant_scores[signature][str(row["cutoff"])] = {
                    "valid": bool(scored["valid"]),
                    "bits": float(scored["bits"]),
                    "regret_bits": regret,
                    "winner_signature": row["signature"],
                    "winner_bits": float(row["parser_bits"]),
                    "winner_match": signature == row["signature"],
                    "reason": scored["reason"],
                }
        average_bits_by_signature = {
            signature: sum(score["bits"] for score in scores.values())
            / len(scores)
            for signature, scores in variant_scores.items()
            if all(score["valid"] for score in scores.values())
        }
        policy_choices = {}
        for policy in policy_totals:
            chosen = choose_policy_variant(policy, variants, average_bits_by_signature)
            signature = variant_key(chosen)
            scores = variant_scores[signature]
            exact_matches = sum(1 for score in scores.values() if score["winner_match"])
            valid_count = sum(1 for score in scores.values() if score["valid"])
            total_regret = sum(score["regret_bits"] for score in scores.values())
            max_regret = max(score["regret_bits"] for score in scores.values())
            policy_totals[policy]["book_count"] += 1.0
            policy_totals[policy]["cutoff_observation_count"] += len(scores)
            policy_totals[policy]["exact_signature_matches"] += exact_matches
            policy_totals[policy]["valid_observation_count"] += valid_count
            policy_totals[policy]["total_regret_bits"] += total_regret
            policy_totals[policy]["max_regret_bits"] = max(
                policy_totals[policy]["max_regret_bits"], max_regret
            )
            policy_choices[policy] = {
                "signature": signature,
                "type_sequence": chosen["type_sequence"],
                "length_sequence": chosen["length_sequence"],
                "copy_sources": chosen["copy_sources"],
                "exact_matches": exact_matches,
                "observation_count": len(scores),
                "total_regret_bits": total_regret,
                "max_regret_bits": max_regret,
            }
        book_rows.append(
            {
                "book": book,
                "variant_count": len(variants),
                "cutoffs": [int(row["cutoff"]) for row in cutoff_rows],
                "winner_signatures_by_cutoff": {
                    str(row["cutoff"]): row["signature"] for row in cutoff_rows
                },
                "variants": [
                    {
                        key: value
                        for key, value in variant.items()
                        if key != "ops"
                    }
                    for variant in variants
                ],
                "variant_scores": variant_scores,
                "policy_choices": policy_choices,
            }
        )

    policy_rows = []
    for policy, totals in policy_totals.items():
        obs = totals["cutoff_observation_count"]
        matches = totals["exact_signature_matches"]
        valid = totals["valid_observation_count"]
        total_regret = totals["total_regret_bits"]
        policy_rows.append(
            {
                "policy": policy,
                "book_count": int(totals["book_count"]),
                "cutoff_observation_count": int(obs),
                "exact_signature_matches": int(matches),
                "exact_signature_match_rate": matches / obs if obs else 0.0,
                "valid_observation_count": int(valid),
                "total_regret_bits": total_regret,
                "mean_regret_bits": total_regret / obs if obs else float("inf"),
                "max_regret_bits": totals["max_regret_bits"],
            }
        )
    policy_rows.sort(
        key=lambda row: (
            row["total_regret_bits"],
            -row["exact_signature_match_rate"],
            row["policy"],
        )
    )
    best_structural = [
        row for row in policy_rows if row["policy"] != "oracle_min_average_reprice"
    ][0]
    oracle = next(
        row for row in policy_rows if row["policy"] == "oracle_min_average_reprice"
    )
    promotes_policy = (
        best_structural["exact_signature_matches"]
        == best_structural["cutoff_observation_count"]
        and abs(best_structural["total_regret_bits"]) <= 1e-9
    )
    classification = (
        "boundary_policy_promotable"
        if promotes_policy
        else "simple_boundary_policies_not_promoted"
    )
    return {
        "schema": "boundary_policy_stability_gate.v1",
        "classification": classification,
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "gate79_unstable_path_decomposition": rel(GATE79),
            "gate78_path_replay": rel(GATE78_SCRIPT),
            "gate77_context_loader": rel(GATE77_SCRIPT),
        },
        "scope": {
            "analysis_only": True,
            "unstable_books_only": True,
            "fixed_policy_no_parameter_sweep": True,
            "compression_bound_changed": False,
            "new_formula_emitted": False,
            "row0_origin_changed": False,
            "does_not_search_plaintext": True,
        },
        "summary": {
            "unstable_book_count": len(unstable_books),
            "cutoff_observation_count": int(
                sum(row["cutoff_observation_count"] for row in policy_rows[:1])
            ),
            "policy_rows": policy_rows,
            "best_structural_policy": best_structural,
            "oracle_min_average_reprice": oracle,
            "policy_promoted": promotes_policy,
            "book_rows": book_rows,
            "interpretation": (
                "Every tested simple invariant boundary policy leaves exact "
                "path mismatches and positive regret against the per-cutoff "
                "parser winners. The observed instability is therefore not "
                "explained by a cheap global rule such as front-loading copy "
                "lengths, back-loading copy lengths, choosing earliest/latest "
                "sources, or preserving source-default choices. Boundary "
                "selection remains a structural blocker rather than a closed "
                "mechanism."
            ),
        },
        "decision": {
            "compression_bound_status": "unchanged_8154_676268",
            "source_length_parser_status": "simple_boundary_policy_rejected",
            "generation_explanation_status": "boundary_selection_still_exogenous_to_parser_costs",
            "row0_origin_status": "unchanged_exogenous",
            "translation_or_plaintext_status": "NONE",
        },
    }


def write_result(result: dict[str, Any]) -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    json_path = TEST_RESULTS / "80_boundary_policy_stability_gate.json"
    md_path = TEST_RESULTS / "80_boundary_policy_stability_gate.md"
    json_path.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    s = result["summary"]
    lines = [
        "# Boundary Policy Stability Gate",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Gate 79 showed that the remaining unstable parser paths are primarily",
        "copy-boundary and segmentation choices. This gate tests fixed, simple",
        "invariant boundary policies against the observed unstable variants,",
        "repricing each observed variant in every cutoff view where the book",
        "appears.",
        "",
        "## Summary",
        "",
        f"- Unstable books tested: `{s['unstable_book_count']}`.",
        f"- Cutoff observations tested: `{s['cutoff_observation_count']}`.",
        f"- Policy promoted: `{s['policy_promoted']}`.",
        "",
        "## Policy Scoreboard",
        "",
        "| Policy | Exact matches | Match rate | Total regret bits | Mean regret bits | Max regret bits |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in s["policy_rows"]:
        lines.append(
            "| {policy} | {exact_signature_matches}/{cutoff_observation_count} | {exact_signature_match_rate:.3f} | {total_regret_bits:.6f} | {mean_regret_bits:.6f} | {max_regret_bits:.6f} |".format(
                **row
            )
        )
    best = s["best_structural_policy"]
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- Best structural policy: `{best['policy']}` with `{best['exact_signature_matches']}/{best['cutoff_observation_count']}` exact matches and `{best['total_regret_bits']:.6f}` total regret bits.",
            f"- {s['interpretation']}",
            "- No compression-bound change is introduced.",
            "- No corpus-wide formula promotion is introduced.",
            "- Row0 remains unchanged and exogenous.",
            "- No plaintext, translation, semantic reading, or case reopening is introduced.",
        ]
    )
    md_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> None:
    result = make_result()
    write_result(result)
    print(json.dumps(result["summary"]["policy_rows"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
