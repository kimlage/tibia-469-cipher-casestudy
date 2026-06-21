from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
TEST_RESULTS = HERE / "reports" / "test_results"

GATE111_SCRIPT = HERE / "scripts" / "111_decoder_length_candidate_ambiguity_audit.py"
GATE100 = TEST_RESULTS / "100_skeleton_rule_coverage_audit.json"
GATE111 = TEST_RESULTS / "111_decoder_length_candidate_ambiguity_audit.json"
OUT_STEM = "112_decoder_length_policy_audit"
MIN_COPY_LEN = 5


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


def clamp(value: int, low: int, high: int) -> int:
    return max(low, min(high, value))


def candidate_at_fraction(low: int, high: int, fraction: float) -> int:
    if low == high:
        return low
    return clamp(round(low + (high - low) * fraction), low, high)


def build_rows() -> list[dict[str, Any]]:
    gate100 = load_json(GATE100)
    gate111_module = load_module("gate111_for_gate112", GATE111_SCRIPT)
    rows: list[dict[str, Any]] = []
    for copy_row in gate111_module.make_copy_rows():
        book = int(copy_row["book"])
        op_index = int(copy_row["op_index"])
        declared = int(copy_row["length"])
        low = MIN_COPY_LEN
        high = int(copy_row["decoder_max_possible_after_declared_source"])
        if not (low <= declared <= high):
            raise RuntimeError(
                {
                    "type": "declared_copy_outside_candidate_set",
                    "book": book,
                    "op_index": op_index,
                    "declared": declared,
                    "low": low,
                    "high": high,
                }
            )
        rows.append(
            {
                "book": book,
                "op_index": op_index,
                "op_type": "copy",
                "declared_length": declared,
                "candidate_low": low,
                "candidate_high": high,
                "candidate_count": high - low + 1,
                "remaining": int(copy_row["remaining_book_digits"]),
                "previous_in_book_length": None,
            }
        )

    for skeleton in sorted(
        gate100["skeleton_rows"],
        key=lambda row: (int(row["book"]), int(row["op_index"])),
    ):
        if skeleton["type"] != "literal":
            continue
        book = int(skeleton["book"])
        op_index = int(skeleton["op_index"])
        declared = int(skeleton["length"])
        low = 1
        high = int(skeleton["remaining"])
        if not (low <= declared <= high):
            raise RuntimeError(
                {
                    "type": "declared_literal_outside_candidate_set",
                    "book": book,
                    "op_index": op_index,
                    "declared": declared,
                    "low": low,
                    "high": high,
                }
            )
        rows.append(
            {
                "book": book,
                "op_index": op_index,
                "op_type": "literal",
                "declared_length": declared,
                "candidate_low": low,
                "candidate_high": high,
                "candidate_count": high - low + 1,
                "remaining": int(skeleton["remaining"]),
                "previous_in_book_length": skeleton["previous_in_book_length"],
            }
        )
    return rows


Policy = Callable[[dict[str, Any], int | None], int]


def policy_min(row: dict[str, Any], previous: int | None) -> int:
    return int(row["candidate_low"])


def policy_max(row: dict[str, Any], previous: int | None) -> int:
    return int(row["candidate_high"])


def policy_q25(row: dict[str, Any], previous: int | None) -> int:
    return candidate_at_fraction(int(row["candidate_low"]), int(row["candidate_high"]), 0.25)


def policy_median(row: dict[str, Any], previous: int | None) -> int:
    return candidate_at_fraction(int(row["candidate_low"]), int(row["candidate_high"]), 0.5)


def policy_q75(row: dict[str, Any], previous: int | None) -> int:
    return candidate_at_fraction(int(row["candidate_low"]), int(row["candidate_high"]), 0.75)


def policy_previous_else_min(row: dict[str, Any], previous: int | None) -> int:
    if previous is None:
        return policy_min(row, previous)
    return clamp(previous, int(row["candidate_low"]), int(row["candidate_high"]))


def policy_previous_else_max(row: dict[str, Any], previous: int | None) -> int:
    if previous is None:
        return policy_max(row, previous)
    return clamp(previous, int(row["candidate_low"]), int(row["candidate_high"]))


def policy_previous_else_median(row: dict[str, Any], previous: int | None) -> int:
    if previous is None:
        return policy_median(row, previous)
    return clamp(previous, int(row["candidate_low"]), int(row["candidate_high"]))


POLICIES: dict[str, Policy] = {
    "min_candidate": policy_min,
    "max_candidate": policy_max,
    "q25_candidate": policy_q25,
    "median_candidate": policy_median,
    "q75_candidate": policy_q75,
    "previous_length_else_min": policy_previous_else_min,
    "previous_length_else_max": policy_previous_else_max,
    "previous_length_else_median": policy_previous_else_median,
}


def score_policy(rows: list[dict[str, Any]], name: str, fn: Policy) -> dict[str, Any]:
    hits = 0
    copy_hits = 0
    literal_hits = 0
    previous_by_book: dict[int, int] = {}
    failures: list[dict[str, Any]] = []
    for row in rows:
        book = int(row["book"])
        previous = previous_by_book.get(book)
        predicted = fn(row, previous)
        declared = int(row["declared_length"])
        ok = predicted == declared
        if ok:
            hits += 1
            if row["op_type"] == "copy":
                copy_hits += 1
            else:
                literal_hits += 1
        elif len(failures) < 10:
            failures.append(
                {
                    "book": book,
                    "op_index": int(row["op_index"]),
                    "op_type": row["op_type"],
                    "declared_length": declared,
                    "predicted_length": predicted,
                    "candidate_low": int(row["candidate_low"]),
                    "candidate_high": int(row["candidate_high"]),
                    "candidate_count": int(row["candidate_count"]),
                }
            )
        previous_by_book[book] = declared

    copy_total = sum(1 for row in rows if row["op_type"] == "copy")
    literal_total = len(rows) - copy_total
    return {
        "policy": name,
        "hits": hits,
        "total": len(rows),
        "coverage": hits / len(rows),
        "copy_hits": copy_hits,
        "copy_total": copy_total,
        "literal_hits": literal_hits,
        "literal_total": literal_total,
        "promotes_policy": hits == len(rows),
        "sample_failures": failures,
    }


def position_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    forced = 0
    min_hits = 0
    max_hits = 0
    lower_quarter = 0
    upper_quarter = 0
    normalized_positions = []
    for row in rows:
        low = int(row["candidate_low"])
        high = int(row["candidate_high"])
        declared = int(row["declared_length"])
        if low == high:
            forced += 1
            normalized_positions.append(0.0)
            continue
        position = (declared - low) / (high - low)
        normalized_positions.append(position)
        if declared == low:
            min_hits += 1
        if declared == high:
            max_hits += 1
        if position <= 0.25:
            lower_quarter += 1
        if position >= 0.75:
            upper_quarter += 1
    return {
        "forced_rows": forced,
        "declared_min_hits": min_hits,
        "declared_max_hits": max_hits,
        "declared_lower_quarter_rows": lower_quarter,
        "declared_upper_quarter_rows": upper_quarter,
        "mean_normalized_position": sum(normalized_positions)
        / len(normalized_positions),
    }


def make_result() -> dict[str, Any]:
    gate100 = load_json(GATE100)
    gate111 = load_json(GATE111)
    for name, data in [
        ("skeleton_rule_coverage", gate100),
        ("decoder_length_candidate_ambiguity", gate111),
    ]:
        assert_boundary(name, data)
    if gate111["classification"] != "decoder_length_candidates_ambiguous_dependency_retained":
        raise RuntimeError("gate111 does not retain length ambiguity")

    rows = build_rows()
    policy_rows = [score_policy(rows, name, fn) for name, fn in POLICIES.items()]
    best_policy = max(policy_rows, key=lambda row: (row["hits"], row["policy"]))
    best_copy = max(policy_rows, key=lambda row: (row["copy_hits"], row["policy"]))
    best_literal = max(policy_rows, key=lambda row: (row["literal_hits"], row["policy"]))
    promotes_policy = best_policy["hits"] == len(rows)

    return {
        "schema": "decoder_length_policy_audit.v1",
        "classification": "simple_length_candidate_policies_not_promoted",
        "translation_delta": "NONE",
        "case_reopened": False,
        "plaintext_claim": False,
        "inputs": {
            "gate100_skeleton_rule_coverage": rel(GATE100),
            "gate111_decoder_length_candidate_ambiguity": rel(GATE111),
        },
        "scope": {
            "analysis_only": True,
            "fixed_policy_audit_only": True,
            "compression_bound_changed": False,
            "new_formula_emitted": False,
            "row0_origin_changed": False,
            "does_not_search_plaintext": True,
            "policy_set": sorted(POLICIES),
        },
        "summary": {
            "operation_count": len(rows),
            "copy_count": gate100["summary"]["copy_count"],
            "literal_count": gate100["summary"]["literal_count"],
            "policy_count": len(POLICIES),
            "best_policy": best_policy,
            "best_copy_policy": best_copy,
            "best_literal_policy": best_literal,
            "position_summary": position_summary(rows),
            "promotes_length_policy": promotes_policy,
            "interpretation": (
                "Fixed decoder-side length policies do not explain the length "
                "sequence. The best tested policy is only a partial boundary "
                "diagnostic, not a generator: declared lengths are spread across "
                "candidate sets rather than being consistently min, max, median, "
                "quartile, or previous-length choices. Length selection remains "
                "a retained parser objective."
            ),
        },
        "policy_rows": policy_rows,
        "decision": {
            "compression_bound_status": "unchanged_8154_676268",
            "generation_explanation_status": "simple_length_policy_rejected",
            "skeleton_status": "length_choice_not_simple_candidate_policy",
            "source_dependency_status": "retained_declared_dependency",
            "row0_origin_status": "unchanged_exogenous",
            "translation_or_plaintext_status": "NONE",
        },
    }


def write_result(result: dict[str, Any]) -> None:
    json_path = TEST_RESULTS / f"{OUT_STEM}.json"
    md_path = TEST_RESULTS / f"{OUT_STEM}.md"
    json_path.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    s = result["summary"]
    best = s["best_policy"]
    pos = s["position_summary"]
    lines = [
        "# Decoder Length Policy Audit",
        "",
        f"Classification: `{result['classification']}`",
        "Translation delta: `NONE`",
        "",
        "## Purpose",
        "",
        "Gate 111 showed that operation lengths remain ambiguous even after",
        "granting op type and copy source. This audit tests whether fixed",
        "decoder-side policies over those candidate sets recover the declared",
        "length sequence.",
        "",
        "## Policy Scoreboard",
        "",
        "| Policy | Hits | Copy hits | Literal hits | Promoted |",
        "|---|---:|---:|---:|---|",
    ]
    for row in sorted(result["policy_rows"], key=lambda item: (-item["hits"], item["policy"])):
        lines.append(
            f"| `{row['policy']}` | `{row['hits']}/{row['total']}` | "
            f"`{row['copy_hits']}/{row['copy_total']}` | "
            f"`{row['literal_hits']}/{row['literal_total']}` | "
            f"`{row['promotes_policy']}` |"
        )
    lines.extend(
        [
            "",
            "## Declared Position Diagnostics",
            "",
            f"- Forced rows: `{pos['forced_rows']}`.",
            f"- Declared min hits: `{pos['declared_min_hits']}`.",
            f"- Declared max hits: `{pos['declared_max_hits']}`.",
            f"- Declared lower-quarter rows: `{pos['declared_lower_quarter_rows']}`.",
            f"- Declared upper-quarter rows: `{pos['declared_upper_quarter_rows']}`.",
            f"- Mean normalized candidate position: `{pos['mean_normalized_position']:.6f}`.",
            "",
            "## Decision",
            "",
            f"- Best policy: `{best['policy']}` = `{best['hits']}/{best['total']}`.",
            f"- Promotes length policy: `{s['promotes_length_policy']}`.",
            f"- {s['interpretation']}",
            "- No compression-bound change is introduced.",
            "- No formula is emitted.",
            "- Row0 remains unchanged and exogenous.",
            "- No plaintext, translation, semantic reading, or case reopening is introduced.",
            "",
        ]
    )
    md_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    result = make_result()
    write_result(result)
    print(json.dumps(result["decision"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
