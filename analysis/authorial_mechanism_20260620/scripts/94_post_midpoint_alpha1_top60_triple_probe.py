from __future__ import annotations

import importlib.util
import itertools
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports" / "test_results"

FORMULA = HERE / "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_midpoint_alpha1_minaddr_repair2_formula_469.json"
BOOKS_DIGITS = ROOT / "analysis/audit_20260609/books_digits.json"
PAIR = HERE / "scripts/88_post_midpoint_alpha1_pair_frontier.py"
FRONTIER = HERE / "scripts/71_minaddr_local_frontier.py"
MIDPOINT = HERE / "scripts/85_post_midpoint_local_frontier.py"
CONTEXT = HERE / "scripts/84_post_adaptive_copy_length_context_search.py"

CURRENT_TOTAL_KEY = "sequential_lz_digit_address_contextual_bounded_adaptive_copy_length_midpoint_alpha1_minaddr_repair2_bits"
TOP_N = 60


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_result(name: str, result: dict, lines: list[str]) -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / f"{name}.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (REPORTS / f"{name}.md").write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def repairs_compatible(repairs: tuple[dict, ...], pair_module) -> bool:
    for left, right in itertools.combinations(repairs, 2):
        if not pair_module.repairs_compatible(left, right):
            return False
    return True


def strip_score(row: dict | None) -> dict | None:
    if row is None:
        return None
    return {key: value for key, value in row.items() if key != "score"}


def main() -> None:
    pair_module = load_module("post_midpoint_alpha1_pair_frontier", PAIR)
    frontier = load_module("minaddr_frontier", FRONTIER)
    midpoint = load_module("post_midpoint_frontier", MIDPOINT)
    context_module = load_module("post_adaptive_copy_length_context", CONTEXT)
    formula = load_json(FORMULA)
    books = {str(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    current_bits = float(formula["mdl_estimate_rough"][CURRENT_TOTAL_KEY])
    current_score = pair_module.score_formula(formula, books, frontier, midpoint, context_module)
    if current_score["validation"]["errors"]:
        raise RuntimeError(current_score["validation"])
    if abs(current_score["total_bits"] - current_bits) > 1e-6:
        raise RuntimeError((current_score["total_bits"], current_bits))

    candidates, single_counts = pair_module.collect_single_candidates(
        formula,
        books,
        current_bits,
        frontier,
        midpoint,
        context_module,
    )
    sorted_candidates = sorted(candidates, key=lambda row: row["single_delta_bits"])
    top_candidates = sorted_candidates[: min(TOP_N, len(sorted_candidates))]
    best_single = sorted_candidates[0] if sorted_candidates else None
    best_triple = None
    top_results = []
    counts = {
        "valid_single_candidates": len(candidates),
        "top_n_requested": TOP_N,
        "top_n_used": len(top_candidates),
        "total_triples_considered": 0,
        "compatible_triples": 0,
        "incompatible_triples_skipped": 0,
        "invalid_triples": 0,
        "valid_triples": 0,
    }

    for repairs in itertools.combinations(top_candidates, 3):
        counts["total_triples_considered"] += 1
        if not repairs_compatible(repairs, pair_module):
            counts["incompatible_triples_skipped"] += 1
            continue
        counts["compatible_triples"] += 1
        score = pair_module.score_formula(
            pair_module.apply_repair_pair(formula, repairs),
            books,
            frontier,
            midpoint,
            context_module,
        )
        if score["validation"]["errors"]:
            counts["invalid_triples"] += 1
            continue
        counts["valid_triples"] += 1
        row = {
            "total_bits": score["total_bits"],
            "delta_bits": score["total_bits"] - current_bits,
            "repairs": list(repairs),
            "score": score,
        }
        if best_triple is None or row["total_bits"] < best_triple["total_bits"]:
            best_triple = row
        top_results.append(strip_score(row))
        top_results.sort(key=lambda item: item["total_bits"])
        del top_results[20:]

    classification = (
        "bounded_post_midpoint_alpha1_top60_triple_probe_candidate"
        if best_triple is not None and best_triple["delta_bits"] < -1e-9
        else "bounded_post_midpoint_alpha1_top60_triple_probe_not_promoted"
    )

    result = {
        "schema": "post_midpoint_alpha1_top60_triple_probe.v1",
        "test": "94_post_midpoint_alpha1_top60_triple_probe",
        "classification": classification,
        "translation_delta": "NONE",
        "source_formula": str(FORMULA.relative_to(ROOT)),
        "current_formula_bits": current_bits,
        "current_score_audit": current_score,
        "single_counts": single_counts,
        "best_single_repair": best_single,
        "bounded_scope": (
            f"all compatible triples among the top {len(top_candidates)} local single-edit "
            "candidates sorted by exact single-edit delta; this is not an exhaustive "
            "189-candidate triple frontier"
        ),
        "triple_counts": counts,
        "best_triple_repair": strip_score(best_triple),
        "best_triple_score": best_triple["score"] if best_triple else None,
        "top_triple_results": top_results,
        "promotion_rule": (
            "record as candidate only if a bounded top-N compatible triple beats the active "
            "midpoint alpha=1 formula under full rescoring; do not treat non-promotion as "
            "exhaustive closure outside the top-N scope"
        ),
        "boundary": formula["boundary"],
    }

    lines = [
        "# Post-Midpoint Alpha1 Top60 Triple Probe",
        "",
        f"Verdict: `{classification}`. Translation delta: `NONE`.",
        "",
        "This bounded probe tests compatible triples among the top local single",
        "edits after the midpoint alpha=1 pair frontier closed. It is deliberately",
        "not an exhaustive triple frontier over all local candidates.",
        "",
        "## Scope",
        "",
        f"- Current formula bits: `{current_bits:.3f}`",
        f"- Valid single candidates: `{len(candidates)}`",
        f"- Top-N candidates used: `{len(top_candidates)}`",
        f"- Total triples considered: `{counts['total_triples_considered']}`",
        f"- Compatible triples: `{counts['compatible_triples']}`",
        f"- Valid triples: `{counts['valid_triples']}`",
        f"- Invalid triples: `{counts['invalid_triples']}`",
    ]
    if best_single:
        lines.extend(
            [
                "",
                "## Best Single",
                "",
                f"- Delta: `{best_single['single_delta_bits']:.3f}` bits",
                f"- Book/op/text: `{best_single['book']}` / `{best_single['op_index']}` / `{best_single['text']}`",
            ]
        )
    if best_triple:
        lines.extend(
            [
                "",
                "## Best Bounded Triple",
                "",
                f"- Delta: `{best_triple['delta_bits']:.3f}` bits",
                f"- Total bits: `{best_triple['total_bits']:.3f}`",
            ]
        )
        for index, repair in enumerate(best_triple["repairs"], start=1):
            lines.append(
                f"- Repair {index}: `{repair['edit_type']}` book `{repair['book']}`, "
                f"op `{repair['op_index']}`, text `{repair['text']}`, length `{repair['length']}`"
            )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "This probe can find a candidate improvement inside its bounded top-N",
            "scope. A negative result here is evidence against the most plausible",
            "triple combinations, but it is not an exhaustive closure of every",
            "possible triple of the 189 local candidates.",
            "",
            "## Boundary",
            "",
            "This is a mechanical recipe-cost audit only. It does not alter row0,",
            "introduce plaintext, or make an authorial-intent claim.",
        ]
    )
    write_result("94_post_midpoint_alpha1_top60_triple_probe", result, lines)


if __name__ == "__main__":
    main()
