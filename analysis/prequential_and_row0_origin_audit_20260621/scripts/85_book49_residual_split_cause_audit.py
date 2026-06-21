from __future__ import annotations

import importlib.util
import json
import math
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
TEST_RESULTS = HERE / "reports" / "test_results"

GATE84_SCRIPT = HERE / "scripts" / "84_residual_literal_payload_neutralization_gate.py"
GATE84 = TEST_RESULTS / "84_residual_literal_payload_neutralization_gate.json"

BOOK = 49
CUTOFFS = [10, 20, 35]
CONTROLS = [
    "observed_payload_mode",
    "no_literal_length_charge",
    "no_item_type_charge",
    "no_item_or_literal_length_charge",
]
COMPONENTS = [
    "item_type",
    "copy_source_flag",
    "copy_source_uniform_exception",
    "copy_length_uniform",
    "literal_payload_uniform",
    "literal_length",
]


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


def zero_components() -> dict[str, float]:
    return {component: 0.0 for component in COMPONENTS}


def collect_book49_views(gate84, gate82, gate77_module) -> dict[int, dict[str, Any]]:
    views = {}
    for cutoff in CUTOFFS:
        context = gate77_module.load_parser_context_for_cutoff(cutoff)
        context["gate82"] = gate82
        gate37 = context["gate37"]
        formula = context["formula"]
        books = context["books"]
        available = "".join(books[str(index)] for index in range(cutoff))
        previous_end = gate37.previous_copy_end_before(formula, cutoff)
        for book in range(cutoff, 70):
            initial_previous_end = previous_end
            row = gate84.sparse_parse_literal_payload_uniform(
                context=context,
                book=book,
                available=available,
                initial_previous_copy_end=initial_previous_end,
            )
            if not row["roundtrip_ok"]:
                raise RuntimeError({"cutoff": cutoff, "book": book})
            if book == BOOK:
                views[cutoff] = {
                    "context": context,
                    "available": available,
                    "initial_previous_copy_end": initial_previous_end,
                    "winner": row,
                }
                break
            available += books[str(book)]
            previous_end = row["final_previous_copy_end"]
    return views


def variant_name(ops: list[dict[str, Any]]) -> str:
    first = ops[:3]
    if (
        len(first) == 3
        and first[0]["type"] == "literal"
        and first[0]["length"] == 11
        and first[1]["type"] == "copy"
        and first[1]["length"] == 7
        and first[2]["type"] == "literal"
        and first[2]["length"] == 7
    ):
        return "split_prefix"
    if ops and ops[0]["type"] == "literal" and ops[0]["length"] == 25:
        return "coalesced_prefix"
    return "other"


def op_profile(ops: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "type_sequence": "".join("C" if op["type"] == "copy" else "L" for op in ops),
        "length_sequence": [int(op["length"]) for op in ops],
        "copy_sources": [int(op["source"]) for op in ops if op["type"] == "copy"],
        "literal_digits": sum(int(op["length"]) for op in ops if op["type"] == "literal"),
        "copied_digits": sum(int(op["length"]) for op in ops if op["type"] == "copy"),
    }


def score_ops(
    *,
    view: dict[str, Any],
    ops: list[dict[str, Any]],
    control: str,
) -> dict[str, Any]:
    context = view["context"]
    gate82 = context["gate82"]
    audit126 = context["audit126"]
    formula = context["formula"]
    train_counts = context["train_counts"]
    source_train_counts = context["source_train_counts"]
    text = context["books"][str(BOOK)]
    available = view["available"]
    previous_end = view["initial_previous_copy_end"]
    min_len = int(formula["policy"]["min_len"])
    literal_length_model = formula["policy"]["literal_run_length_model"]
    item_model = formula["policy"]["item_type_model"]

    no_literal_length = control in {
        "no_literal_length_charge",
        "no_item_or_literal_length_charge",
    }
    no_item = control in {
        "no_item_type_charge",
        "no_item_or_literal_length_charge",
    }

    components = zero_components()
    position = 0
    previous_item = "BOS"
    local_emitted = available
    for op in ops:
        length = int(op["length"])
        if int(op["target_start"]) != position:
            return {"valid": False, "bits": float("inf"), "reason": "bad_target", "components": components}
        remaining = len(text) - position
        if op["type"] == "literal":
            if previous_item == "literal":
                return {"valid": False, "bits": float("inf"), "reason": "adjacent_literal", "components": components}
            literal_forced = remaining < min_len
            if literal_forced and length != remaining:
                return {"valid": False, "bits": float("inf"), "reason": "bad_forced_literal", "components": components}
            components["literal_payload_uniform"] += length * math.log2(10)
            if not literal_forced:
                if not no_item:
                    components["item_type"] += audit126.item_bits_for_choice(
                        forced=False,
                        item_type="literal",
                        book_int=BOOK,
                        item_model=item_model,
                        item_counts=train_counts["item"],
                    )
                if not no_literal_length:
                    components["literal_length"] += audit126.length_bits(
                        length + 1,
                        literal_length_model,
                    )
            next_position = position + length
            local_emitted += text[position:next_position]
            position = next_position
            previous_item = "literal"
            continue

        if op["type"] != "copy":
            return {"valid": False, "bits": float("inf"), "reason": "unknown_op", "components": components}
        if remaining < min_len or length < min_len:
            return {"valid": False, "bits": float("inf"), "reason": "short_copy", "components": components}
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
            return {"valid": False, "bits": float("inf"), "reason": "illegal_copy", "components": components}
        copied = local_emitted[source : source + length]
        if copied != text[position : position + length]:
            return {"valid": False, "bits": float("inf"), "reason": "copy_mismatch", "components": components}
        source_bits, _is_default, flag_bits, exception_bits = gate82.uniform_source_bits(
            source=source,
            legal_source_count=legal_source_count,
            previous_copy_end=previous_end,
            counts=source_train_counts,
            uniform_flag=False,
        )
        if not math.isfinite(source_bits):
            return {"valid": False, "bits": float("inf"), "reason": "source_inf", "components": components}
        if not no_item:
            components["item_type"] += audit126.item_bits_for_choice(
                forced=previous_item == "literal",
                item_type="copy",
                book_int=BOOK,
                item_model=item_model,
                item_counts=train_counts["item"],
            )
        components["copy_source_flag"] += flag_bits
        components["copy_source_uniform_exception"] += exception_bits
        components["copy_length_uniform"] += math.log2(symbol_count)
        local_emitted += copied
        position += length
        previous_item = "copy"
        previous_end = source + length

    return {
        "valid": position == len(text) and local_emitted.endswith(text),
        "bits": sum(components.values()) if position == len(text) else float("inf"),
        "reason": "ok" if position == len(text) else "incomplete",
        "components": components,
    }


def make_result() -> dict[str, Any]:
    gate84_result = load_json(GATE84)
    assert_boundary("residual_literal_payload_neutralization", gate84_result)
    gate84 = load_module("gate84_literal_payload", GATE84_SCRIPT)
    gate82 = gate84.load_module("gate82_for_gate85", gate84.GATE82_SCRIPT)
    gate77 = gate82.load_module("gate77_for_gate85", gate82.GATE77_SCRIPT)
    views = collect_book49_views(gate84, gate82, gate77)

    observed_variants: dict[str, dict[str, Any]] = {}
    for cutoff, view in views.items():
        ops = view["winner"]["signature_ops"]
        name = variant_name(ops)
        observed_variants.setdefault(
            name,
            {
                "name": name,
                "signature": view["winner"]["signature"],
                "observed_cutoffs": [],
                "ops": ops,
                "profile": op_profile(ops),
            },
        )
        observed_variants[name]["observed_cutoffs"].append(cutoff)
    if set(observed_variants) != {"split_prefix", "coalesced_prefix"}:
        raise RuntimeError(sorted(observed_variants))

    control_rows = []
    stable_controls = []
    for control in CONTROLS:
        winners = {}
        cutoff_rows = []
        for cutoff, view in views.items():
            scores = {
                name: score_ops(view=view, ops=variant["ops"], control=control)
                for name, variant in observed_variants.items()
            }
            for name, score in scores.items():
                if not score["valid"]:
                    raise RuntimeError({"cutoff": cutoff, "name": name, "score": score})
            winner = min(scores.items(), key=lambda item: (item[1]["bits"], item[0]))[0]
            winners[str(cutoff)] = winner
            delta = {
                component: scores["split_prefix"]["components"][component]
                - scores["coalesced_prefix"]["components"][component]
                for component in COMPONENTS
            }
            cutoff_rows.append(
                {
                    "cutoff": cutoff,
                    "winner": winner,
                    "split_bits": scores["split_prefix"]["bits"],
                    "coalesced_bits": scores["coalesced_prefix"]["bits"],
                    "split_minus_coalesced_bits": (
                        scores["split_prefix"]["bits"]
                        - scores["coalesced_prefix"]["bits"]
                    ),
                    "split_minus_coalesced_components": delta,
                }
            )
        stable = len(set(winners.values())) == 1
        if stable:
            stable_controls.append(control)
        control_rows.append(
            {
                "control": control,
                "stable_winner": stable,
                "winners_by_cutoff": winners,
                "cutoff_rows": cutoff_rows,
            }
        )

    promoted = False
    classification = (
        "book49_residual_split_explained_by_fixed_control"
        if stable_controls
        else "book49_residual_split_not_closed_by_fixed_controls"
    )
    return {
        "schema": "book49_residual_split_cause_audit.v1",
        "classification": classification,
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "gate84_residual_literal_payload_neutralization": rel(GATE84),
            "gate84_replay_script": rel(GATE84_SCRIPT),
        },
        "scope": {
            "analysis_only": True,
            "book": BOOK,
            "cutoffs": CUTOFFS,
            "controls": CONTROLS,
            "local_two_variant_audit": True,
            "compression_bound_changed": False,
            "new_formula_emitted": False,
            "row0_origin_changed": False,
            "does_not_search_plaintext": True,
        },
        "summary": {
            "observed_variants": {
                name: {
                    key: value
                    for key, value in variant.items()
                    if key != "ops"
                }
                for name, variant in observed_variants.items()
            },
            "control_rows": control_rows,
            "stable_controls": stable_controls,
            "promoted": promoted,
            "interpretation": (
                "The sole payload-neutralized residual is a local prefix split "
                "in book 49: cutoffs 10/20 choose literal-copy-literal at the "
                "start, while cutoff 35 chooses the coalesced 25-digit literal. "
                "The fixed local item/literal-length controls are audit-only; "
                "they do not emit a corpus formula."
            ),
        },
        "decision": {
            "compression_bound_status": "unchanged_8154_676268",
            "source_length_parser_status": classification,
            "generation_explanation_status": "book49_residual_localized_no_formula_promotion",
            "row0_origin_status": "unchanged_exogenous",
            "translation_or_plaintext_status": "NONE",
        },
    }


def write_result(result: dict[str, Any]) -> None:
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    json_path = TEST_RESULTS / "85_book49_residual_split_cause_audit.json"
    md_path = TEST_RESULTS / "85_book49_residual_split_cause_audit.md"
    json_path.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    s = result["summary"]
    lines = [
        "# Book 49 Residual Split Cause Audit",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Gate 84 leaves a single residual, book `49`. This audit compares the",
        "two observed prefix variants under fixed local controls to determine",
        "whether item-type or literal-length charges alone close the residual.",
        "",
        "## Observed Variants",
        "",
        "| Variant | Cutoffs | Type sequence | Length sequence |",
        "|---|---|---|---|",
    ]
    for name, row in sorted(s["observed_variants"].items()):
        lines.append(
            "| `{}` | `{}` | `{}` | `{}` |".format(
                name,
                row["observed_cutoffs"],
                row["profile"]["type_sequence"],
                row["profile"]["length_sequence"],
            )
        )
    lines.extend(
        [
            "",
            "## Control Winners",
            "",
            "| Control | Stable winner | Winners by cutoff |",
            "|---|---:|---|",
        ]
    )
    for row in s["control_rows"]:
        lines.append(
            "| `{}` | `{}` | `{}` |".format(
                row["control"],
                row["stable_winner"],
                row["winners_by_cutoff"],
            )
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
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
    print(json.dumps(result["summary"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
