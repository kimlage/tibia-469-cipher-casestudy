from __future__ import annotations

import copy
import importlib.util
import itertools
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports" / "test_results"

FORMULA = HERE / "sequential_lz_digit_address_contextual_copy_to_literal_formula_469.json"
BOOKS_DIGITS = ROOT / "analysis/audit_20260609/books_digits.json"
LITERAL_TO_COPY = HERE / "scripts/64_contextual_local_repair_search.py"
COPY_TO_LITERAL = HERE / "scripts/65_contextual_copy_to_literal_repair_search.py"
CURRENT_TOTAL_KEY = "sequential_lz_digit_address_contextual_copy_to_literal_bits"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_result(name: str, result: dict, lines: list[str]) -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / f"{name}.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (REPORTS / f"{name}.md").write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def public_repair(row: dict | None) -> dict | None:
    if row is None:
        return None
    return {key: value for key, value in row.items() if key != "score"}


def collect_copy_to_literal_candidates(formula: dict, books: dict[str, str], current_bits: float, scorer) -> tuple[list[dict], int]:
    emitted = ""
    invalid = 0
    candidates = []
    for book in map(str, formula["policy"]["book_order"]):
        book_pos = 0
        for op_index, op in enumerate(formula["book_recipes"][book]["ops"]):
            length = int(op["length"])
            if op["type"] == "literal":
                chunk = op["text"]
            elif op["type"] == "copy":
                source_digit_pos = int(op["source_digit_pos"])
                chunk = emitted[source_digit_pos : source_digit_pos + length]
                repair = {
                    "book": book,
                    "op_index": op_index,
                    "book_pos": book_pos,
                    "length": length,
                    "source_digit_pos": source_digit_pos,
                    "text": chunk,
                }
                candidate = copy_to_literal_formula(formula, [repair])
                score = scorer.score_formula(candidate, books)
                if score["validation"]["errors"]:
                    invalid += 1
                else:
                    candidates.append({**repair, "delta_bits": score["total_bits"] - current_bits})
            else:
                raise ValueError(op)
            emitted += chunk
            book_pos += length
    return candidates, invalid


def copy_to_literal_formula(formula: dict, repairs: list[dict]) -> dict:
    out = copy.deepcopy(formula)
    for repair in sorted(repairs, key=lambda row: (int(row["book"]), row["op_index"]), reverse=True):
        out["book_recipes"][repair["book"]]["ops"][repair["op_index"]] = {
            "type": "literal",
            "text": repair["text"],
            "length": repair["length"],
        }
    return out


def best_copy_to_literal_pair(formula: dict, books: dict[str, str], current_bits: float, scorer) -> tuple[dict | None, int, int]:
    candidates, single_invalid = collect_copy_to_literal_candidates(formula, books, current_bits, scorer)
    best = None
    tested = 0
    invalid = 0
    for left, right in itertools.combinations(candidates, 2):
        tested += 1
        candidate = copy_to_literal_formula(formula, [left, right])
        score = scorer.score_formula(candidate, books)
        if score["validation"]["errors"]:
            invalid += 1
            continue
        delta = score["total_bits"] - current_bits
        if best is None or delta < best["delta_bits"]:
            best = {
                "delta_bits": delta,
                "left": left,
                "right": right,
                "score_bits": score["total_bits"],
            }
    return best, tested, invalid + single_invalid


def main() -> None:
    literal_to_copy = load_module(LITERAL_TO_COPY, "contextual_literal_to_copy")
    copy_to_literal = load_module(COPY_TO_LITERAL, "contextual_copy_to_literal")
    scorer = copy_to_literal.load_scorer()
    formula = load_json(FORMULA)
    books = {str(key): value for key, value in load_json(BOOKS_DIGITS).items()}
    current_bits = float(formula["mdl_estimate_rough"][CURRENT_TOTAL_KEY])
    current_score = scorer.score_formula(formula, books)
    if current_score["validation"]["errors"]:
        raise RuntimeError(current_score["validation"])

    best_l2c, tested_l2c = literal_to_copy.find_best_single_repair(formula, books, current_bits)
    best_c2l, tested_c2l, invalid_c2l = copy_to_literal.find_best_copy_to_literal(
        formula, books, current_bits, scorer
    )
    best_l2c_delta = None if best_l2c is None else best_l2c["delta_bits"]
    best_c2l_delta = None if best_c2l is None else best_c2l["delta_bits"]
    best_c2l_pair, tested_c2l_pairs, invalid_c2l_pairs = best_copy_to_literal_pair(
        formula, books, current_bits, scorer
    )
    best_c2l_pair_delta = None if best_c2l_pair is None else best_c2l_pair["delta_bits"]
    promotes = (
        (best_l2c_delta is not None and best_l2c_delta < -1e-9)
        or (best_c2l_delta is not None and best_c2l_delta < -1e-9)
        or (best_c2l_pair_delta is not None and best_c2l_pair_delta < -1e-9)
    )
    classification = (
        "post_copy_literal_local_frontier_candidate"
        if promotes
        else "post_copy_literal_local_frontier_closed"
    )

    result = {
        "schema": "post_copy_literal_local_frontier.v1",
        "test": "66_post_copy_literal_local_frontier",
        "classification": classification,
        "translation_delta": "NONE",
        "source_formula": str(FORMULA.relative_to(ROOT)),
        "current_formula_bits": current_bits,
        "current_score_audit": current_score,
        "literal_to_copy": {
            "tested_repairs": tested_l2c,
            "best_repair": public_repair(best_l2c),
        },
        "copy_to_literal": {
            "tested_repairs": tested_c2l,
            "invalid_repairs": invalid_c2l,
            "best_repair": public_repair(best_c2l),
        },
        "copy_to_literal_pairs": {
            "tested_pairs": tested_c2l_pairs,
            "invalid_pairs_or_singles": invalid_c2l_pairs,
            "best_pair": best_c2l_pair,
        },
        "promotion_rule": (
            "frontier remains closed only if the best single literal-to-copy, single "
            "copy-to-literal, and copy-to-literal pair edits are all non-improving "
            "under exact contextual rescoring"
        ),
        "boundary": formula["boundary"],
    }

    lines = [
        "# Post Copy-to-Literal Local Frontier",
        "",
        f"Verdict: `{classification}`. Translation delta: `NONE`.",
        "",
        "This audit retests the local one-edit frontier after the promoted",
        "copy-to-literal repair. It checks both directions under the current exact",
        "contextual cost model: literal-to-copy and copy-to-literal.",
        "",
        "## Results",
        "",
        f"- Current formula bits: `{current_bits:.1f}`",
        f"- Literal-to-copy candidates tested: `{tested_l2c}`",
        f"- Best literal-to-copy delta: "
        f"`{best_l2c_delta:.1f}` bits" if best_l2c_delta is not None else "- Best literal-to-copy delta: none",
        f"- Copy-to-literal candidates tested: `{tested_c2l}`",
        f"- Invalid copy-to-literal candidates: `{invalid_c2l}`",
        f"- Best copy-to-literal delta: "
        f"`{best_c2l_delta:.1f}` bits" if best_c2l_delta is not None else "- Best copy-to-literal delta: none",
        f"- Copy-to-literal pairs tested: `{tested_c2l_pairs}`",
        f"- Invalid copy-to-literal pairs/singles: `{invalid_c2l_pairs}`",
        f"- Best copy-to-literal pair delta: "
        f"`{best_c2l_pair_delta:.1f}` bits" if best_c2l_pair_delta is not None else "- Best copy-to-literal pair delta: none",
        "",
        "## Interpretation",
        "",
        "No additional local repair is promoted if all best deltas are positive.",
        "This closes the immediate one-edit frontier and the copy-to-literal pair",
        "frontier for the current contextual formula, without changing the",
        "semantic verdict.",
    ]
    write_result("66_post_copy_literal_local_frontier", result, lines)


if __name__ == "__main__":
    main()
