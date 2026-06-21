from __future__ import annotations

import importlib.util
import json
import math
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
REPORTS = HERE / "reports"
TEST_RESULTS = REPORTS / "test_results"

LEGACY_SCRIPT = (
    ROOT
    / "analysis"
    / "authorial_mechanism_20260620"
    / "scripts"
    / "125_prequential_and_row0_origin_audit.py"
)
LEGACY_RESULT = (
    ROOT
    / "analysis"
    / "authorial_mechanism_20260620"
    / "reports"
    / "test_results"
    / "125_prequential_and_row0_origin_audit.json"
)
OCC_STREAMS = ROOT / "analysis" / "audit_20260609" / "homophone_channel" / "occ_streams.json"
BOOKS_DIGITS = ROOT / "analysis" / "audit_20260609" / "books_digits.json"

SCOPE_COMPRESSION_BOUND_BITS = 8558.666806283434
KNOWN_LATER_COMPRESSION_ONLY_BOUND_BITS = 8343.061944935467


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def load_module(path: Path):
    spec = importlib.util.spec_from_file_location("legacy_prequential_row0_audit", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def percentile(values: list[float], q: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = (len(ordered) - 1) * q
    lower = int(math.floor(index))
    upper = int(math.ceil(index))
    if lower == upper:
        return ordered[lower]
    return ordered[lower] * (upper - index) + ordered[upper] * (index - lower)


def summary(values: list[float]) -> dict[str, float | int | None]:
    if not values:
        return {"n": 0, "min": None, "median": None, "mean": None, "max": None}
    return {
        "n": len(values),
        "min": min(values),
        "median": percentile(values, 0.5),
        "mean": sum(values) / len(values),
        "max": max(values),
    }


def split_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    online = [float(row["aggregate"]["test_online_gain_vs_uniform_bits"]) for row in rows]
    frozen = [float(row["aggregate"]["test_frozen_gain_vs_uniform_bits"]) for row in rows]
    gaps = [float(row["aggregate"]["online_train_test_gap_bits_per_event"]) for row in rows]
    failures = [
        {
            "label": row["label"],
            "online_gain_vs_uniform_bits": row["aggregate"]["test_online_gain_vs_uniform_bits"],
            "frozen_gain_vs_uniform_bits": row["aggregate"]["test_frozen_gain_vs_uniform_bits"],
        }
        for row in rows
        if row["aggregate"]["test_online_gain_vs_uniform_bits"] <= 0
        or row["aggregate"]["test_frozen_gain_vs_uniform_bits"] <= 0
    ]
    return {
        "split_count": len(rows),
        "online_gain_vs_uniform_bits": summary(online),
        "frozen_gain_vs_uniform_bits": summary(frozen),
        "train_test_gap_bits_per_event": summary(gaps),
        "nonpositive_gain_failures": failures,
    }


def ablation_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_component: dict[str, list[float]] = {
        "copy_length": [],
        "literal_payload": [],
        "item_type": [],
    }
    for row in rows:
        online_total = float(row["aggregate"]["test_online_bits"])
        ablated = row["test_component_ablation_totals_bits"]
        by_component["copy_length"].append(float(ablated["copy_length_uniform_only"]) - online_total)
        by_component["literal_payload"].append(float(ablated["literal_payload_uniform_only"]) - online_total)
        by_component["item_type"].append(float(ablated["item_type_uniform_only"]) - online_total)
    return {component: summary(values) for component, values in by_component.items()}


def parameter_stability(rows: list[dict[str, Any]]) -> dict[str, Any]:
    parameter_rows = [
        row["parameter_stability"]["declared_parameters_frozen"]
        for row in rows
    ]
    first = parameter_rows[0] if parameter_rows else {}
    coverage: dict[str, dict[str, int]] = {}
    for component, key in [
        ("copy_length", "copy_length_context_coverage"),
        ("literal_payload", "literal_payload_context_coverage"),
        ("item_type", "item_type_context_coverage"),
    ]:
        missing = sum(
            int(row["parameter_stability"][key]["missing_context_events"])
            for row in rows
        )
        present = sum(
            int(row["parameter_stability"][key]["present_context_events"])
            for row in rows
        )
        coverage[component] = {
            "present_context_events": present,
            "missing_context_events": missing,
        }
    return {
        "parameters_identical_across_splits": all(row == first for row in parameter_rows),
        "declared_parameters": first,
        "context_coverage_total": coverage,
    }


def row0_substrate_facts() -> dict[str, Any]:
    occ = load_json(OCC_STREAMS)
    books = load_json(BOOKS_DIGITS)
    codes = sorted({code for values in occ["class_sizes"].values() for code in values})
    all_codes = {f"{index:02d}" for index in range(100)}
    return {
        "source_occ_streams": rel(OCC_STREAMS),
        "source_books_digits": rel(BOOKS_DIGITS),
        "book_count": len(books),
        "row0_symbol_count": len(occ["class_sizes"]),
        "class_code_count": len(codes),
        "missing_two_digit_codes": sorted(all_codes - set(codes)),
        "class_sizes": {key: len(value) for key, value in sorted(occ["class_sizes"].items())},
        "full_duplicate_book_count": len(occ.get("full_dup_books", [])),
        "note": (
            "These committed artifacts verify the code-class substrate used by the "
            "mechanical audits; they do not derive the 10x10 pair-cell labels."
        ),
    }


def make_result(legacy: dict[str, Any]) -> dict[str, Any]:
    predictive = legacy["predictive_validation"]
    prefix = predictive["prefix_future_suffix_splits"]
    blocks = predictive["contiguous_block_holdouts"]
    families = predictive["public_bookcase_family_holdouts"]
    random_controls = predictive["random_train_set_controls"]

    family_failures = split_summary(families)["nonpositive_gain_failures"]
    prefix_failures = split_summary(prefix)["nonpositive_gain_failures"]
    block_failures = split_summary(blocks)["nonpositive_gain_failures"]
    if prefix_failures:
        predictive_class = "posthoc_compressor_warning_prefix_holdout_failed"
    elif family_failures:
        predictive_class = "predictive_signal_partial_not_generation_method"
    elif block_failures:
        predictive_class = "predictive_signal_partial_block_instability"
    else:
        predictive_class = "predictive_signal_retained_but_recipe_still_posthoc"

    return {
        "schema": "prequential_and_row0_origin_audit_20260621.v1",
        "classification": "analysis_only_falsifiable_audit_row0_origin_exogenous",
        "translation_delta": "NONE",
        "plaintext_claim": False,
        "case_reopened": False,
        "scope": {
            "scope_compression_bound_bits": SCOPE_COMPRESSION_BOUND_BITS,
            "source_formula": legacy["source_formula"],
            "known_later_compression_only_bound_bits_not_used_as_generation_claim": (
                KNOWN_LATER_COMPRESSION_ONLY_BOUND_BITS
            ),
            "reason_later_bound_not_used_here": (
                "The requested method change freezes the 8558.667-bit formula as "
                "the predictive-validation target and stops treating later "
                "compression-only micro-improvements as generation evidence."
            ),
            "fixed_recipe_limitation": (
                "All predictive tests keep the full-corpus LZ recipe fixed. "
                "They validate learned component scoring, not recipe discovery."
            ),
        },
        "active_component_reproduction": legacy["active_component_reproduction"],
        "predictive_validation": {
            "classification": predictive_class,
            "prefix_future_suffix": {
                "summary": split_summary(prefix),
                "rows": prefix,
            },
            "contiguous_block_holdouts": {
                "summary": split_summary(blocks),
                "rows": blocks,
            },
            "public_bookcase_family_holdouts": {
                "summary": split_summary(families),
                "rows": families,
            },
            "randomized_order_controls": random_controls,
            "component_ablation_prefix_splits": ablation_summary(prefix),
            "parameter_stability_prefix_splits": parameter_stability(prefix),
            "failure_rule": (
                "If prefix holdout gains vanish, classify as posthoc compressor. "
                "Family failures downgrade the result to partial predictive signal, "
                "not an authorial generation method."
            ),
        },
        "row0_origin": {
            "classification": "row0_origin_remains_exogenous",
            "substrate_facts": row0_substrate_facts(),
            "what_row0_explains": legacy["row0_origin"]["what_row0_explains"],
            "what_remains_exogenous": legacy["row0_origin"]["what_remains_exogenous"],
            "hypotheses": legacy["row0_origin"]["hypotheses"],
            "promoted_row0_origin_formula_count": 0,
        },
        "progress_criterion": {
            "counts_as_progress": [
                "Prefix/block/family holdout validation or falsification.",
                "A clearer ad-hoc dependency ledger for the fixed LZ recipe and row0.",
                "Controlled rejection of row0-origin hypotheses with algorithm, cost, coverage, contradictions, and controls.",
            ],
            "does_not_count_as_progress": [
                "Number of scripts or test rows.",
                "Compression-only bit reductions without holdout or structural value.",
                "Any semantic projection unsupported by CipSoft/in-game evidence.",
            ],
        },
        "decision": {
            "compression_bound_status": "8558.667 bits is the frozen validation scope, not final authorial method.",
            "generation_explanation_status": predictive_class,
            "source_state_status": "path_dependent_previous_copy_state_retained",
            "copy_length_context_status": "midpoint_context_retained_searched_cutoff_rejected",
            "row0_origin_status": "exogenous_under_current_evidence",
            "translation_or_plaintext_status": "NONE",
        },
    }


def render_markdown(
    result: dict[str, Any],
    *,
    audit_link_prefix: str,
    family_failure_link: str,
    component_selector_link: str,
    recipe_externality_link: str,
    recipe_reparse_matrix_link: str,
    recipe_family_holdout_link: str,
    recipe_family_loss_decomposition_link: str,
    family_holdout_address_space_link: str,
    family_holdout_address_corrected_scoreboard_link: str,
    family_holdout_no_test_carryover_link: str,
    leave_one_book_out_no_self_link: str,
    leave_one_book_out_source_attribution_link: str,
    leave_one_book_out_book_bounded_source_link: str,
    leave_one_book_out_family_excluded_source_link: str,
    online_prefix_book_frontier_link: str,
    online_bootstrap_seed_policy_link: str,
    seeded_online_formula_rescore_link: str,
    seeded_rescore_loss_decomposition_link: str,
    seed_exception_signal_cost_link: str,
    online_order_frontier_controls_link: str,
    order_frontier_promotion_gate_link: str,
    source_blocker_structural_context_gate_link: str,
    source_canonicality_decodability_gate_link: str,
    source_state_dependency_gate_link: str,
    copy_length_midpoint_context_gate_link: str,
    row0_requirement_link: str,
) -> str:
    prefix = result["predictive_validation"]["prefix_future_suffix"]["rows"]
    random_controls = result["predictive_validation"]["randomized_order_controls"]
    block_summary = result["predictive_validation"]["contiguous_block_holdouts"]["summary"]
    family_summary = result["predictive_validation"]["public_bookcase_family_holdouts"]["summary"]
    ablations = result["predictive_validation"]["component_ablation_prefix_splits"]
    params = result["predictive_validation"]["parameter_stability_prefix_splits"]

    lines = [
        "# Prequential and Row0 Origin Audit",
        "",
        "Classification: `analysis_only_falsifiable_audit_row0_origin_exogenous`",
        "Translation delta: `NONE`",
        "",
        "## Scope",
        "",
        f"- Frozen validation compression bound: `{result['scope']['scope_compression_bound_bits']:.3f}` bits",
        f"- Later compression-only bound recorded but not used as generation evidence: `{result['scope']['known_later_compression_only_bound_bits_not_used_as_generation_claim']:.3f}` bits",
        "- No plaintext, translation, or case-reopening claim is made.",
        "- Limitation: the LZ recipe is fixed from the full corpus; this audit tests learned component scoring, not recipe discovery.",
        "",
        "## Predictive Validation",
        "",
        f"Predictive classification: `{result['predictive_validation']['classification']}`",
        "",
        "| Split | Train books | Test books | Train bits | Test online bits | Test frozen bits | Uniform bits | Online gain | Frozen gain | Gap/event |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in prefix:
        agg = row["aggregate"]
        lines.append(
            f"| `{row['label']}` | `{len(row['train_books'])}` | `{len(row['test_books'])}` | "
            f"`{agg['train_bits']:.3f}` | `{agg['test_online_bits']:.3f}` | "
            f"`{agg['test_frozen_bits']:.3f}` | `{agg['test_uniform_bits']:.3f}` | "
            f"`{agg['test_online_gain_vs_uniform_bits']:.3f}` | "
            f"`{agg['test_frozen_gain_vs_uniform_bits']:.3f}` | "
            f"`{agg['online_train_test_gap_bits_per_event']:.4f}` |"
        )

    lines.extend(
        [
            "",
            "### Baselines And Controls",
            "",
            f"- Prefix online gain summary: `{result['predictive_validation']['prefix_future_suffix']['summary']['online_gain_vs_uniform_bits']}`",
            f"- Prefix frozen gain summary: `{result['predictive_validation']['prefix_future_suffix']['summary']['frozen_gain_vs_uniform_bits']}`",
            f"- Contiguous block online summary: `{block_summary['online_gain_vs_uniform_bits']}`",
            f"- Public-bookcase family online summary: `{family_summary['online_gain_vs_uniform_bits']}`",
            f"- Public-bookcase family nonpositive failures: `{family_summary['nonpositive_gain_failures']}`",
            "",
            "| Cutoff | Observed prefix online gain | Random median gain | p(random >= observed) |",
            "|---:|---:|---:|---:|",
        ]
    )
    for row in random_controls:
        lines.append(
            f"| `{row['cutoff']}` | `{row['observed_prefix_online_gain_vs_uniform_bits']:.3f}` | "
            f"`{row['random_gain_summary_bits']['median']:.3f}` | "
            f"`{row['p_random_gain_ge_observed']:.4f}` |"
        )

    lines.extend(
        [
            "",
            "### Component Ablations",
            "",
            "Values are bits saved by the learned component over replacing only that component with a uniform code on prefix holdouts.",
            "",
            "| Component | Min | Median | Mean | Max |",
            "|---|---:|---:|---:|---:|",
        ]
    )
    for component, row in ablations.items():
        lines.append(
            f"| `{component}` | `{row['min']:.3f}` | `{row['median']:.3f}` | "
            f"`{row['mean']:.3f}` | `{row['max']:.3f}` |"
        )

    lines.extend(
        [
            "",
            "### Parameter Stability",
            "",
            f"- Parameters identical across prefix splits: `{params['parameters_identical_across_splits']}`",
            f"- Declared parameters: `{params['declared_parameters']}`",
            f"- Context coverage totals: `{params['context_coverage_total']}`",
            "",
            "Interpretation: prefix and contiguous-block tests retain positive advantage over uniform, but the family split has nonpositive failures. The result is therefore predictive signal only, not a final generation method.",
            "",
            "### Family Failure Follow-Up",
            "",
            "A follow-up failure audit decomposes the three public-bookcase family failures.",
            "They are component/sample-size stress cases rather than a new row0-origin signal:",
            "`hellgate_public_bookcase_33` and `hellgate_public_bookcase_8` are copy-only",
            "failures dominated by copy-length underperformance, while",
            "`hellgate_public_bookcase_6` is online-positive but frozen-negative because the",
            "item-type component loses to uniform under frozen counts.",
            f"See [02_family_holdout_failure_audit.md]({family_failure_link}).",
            "",
            "### Component Selector Follow-Up",
            "",
            "A train-CV component selector then asks whether those failures can be rescued",
            "without seeing the held-out family. For every public-bookcase family, inner",
            "training-family validation keeps all three active components. The selector",
            "therefore leaves the same failures in place; only a heldout oracle improves the",
            "ledger, so no component fallback is promoted.",
            f"See [03_train_cv_component_selector_audit.md]({component_selector_link}).",
            "",
            "### Recipe Externality Follow-Up",
            "",
            "A recipe-externality audit then quantifies the main remaining limitation of",
            "the prequential evidence. Of the `8558.667`-bit validation scope,",
            "`4285.876` bits (`50.076%`) are the prequentially scored copy-length,",
            "literal-payload, and item-type components, while `4272.791` bits",
            "(`49.924%`) remain fixed recipe or non-learned ledger: fixed bits,",
            "literal structure without payload, and copy addresses. The code path",
            "confirms that train/test splits score event rows extracted from the full",
            "formula before splitting; they do not discover held-out literal/copy",
            "segmentation or copy source addresses.",
            f"See [04_recipe_externality_audit.md]({recipe_externality_link}).",
            "",
            "### Recipe Reparse Evidence Matrix",
            "",
            "A follow-up evidence matrix then checks whether the later deterministic",
            "reparse audits actually reduce that fixed-recipe externality. They do:",
            "deterministic reparse roundtrips all future suffixes at cutoffs",
            "`10/20/35/50/60` and beats the active suffix recipe under frozen counts.",
            "Content controls are also weaker. The boundary remains partial because",
            "train-set controls show random same-size training inventories can match",
            "or exceed the numeric prefix: single-cutoff `50` gives `p=0.1538`, and",
            "the multi-cutoff control loses to the random-train mean at cutoff `60`.",
            f"See [06_recipe_reparse_evidence_matrix.md]({recipe_reparse_matrix_link}).",
            "",
            "### Recipe Reparse Family Holdout",
            "",
            "A public-bookcase family holdout then tests whether deterministic recipe",
            "discovery fails on the same family axis where component-only scoring had",
            "failures. It does not: reparse beats raw digits for `19/19` families and",
            "for `3/3` component-failure families. It beats the active frozen recipe in",
            "`14/19` families, so the active full-corpus recipe still has local wins and",
            "the generation explanation remains partial.",
            f"See [08_recipe_reparse_family_holdout.md]({recipe_family_holdout_link}).",
            "",
            "### Recipe Reparse Family Loss Decomposition",
            "",
            "The five families where reparse does not beat the active frozen recipe",
            "are then decomposed by charged component. All five still roundtrip and",
            "still beat raw digits. Four losses are dominated by copy-address bits,",
            "with identical literal/copy inventory against the active recipe; one is",
            "an exact tie. This localizes the remaining active-recipe advantage",
            "without promoting a new generation formula.",
            f"See [09_recipe_reparse_family_loss_decomposition.md]({recipe_family_loss_decomposition_link}).",
            "",
            "### Family Holdout Address Space Audit",
            "",
            "A same-coordinate address audit then checks whether those copy-address",
            "losses are real recipe losses. They are not: when the active recipe is",
            "rebased into the same holdout coordinate system used by the reparse,",
            "all five families roundtrip and the mean copy-address delta falls from",
            "`4.667` bits to approximately `0.000` bits under a `0.001` bit epsilon.",
            "The prior active-recipe local wins were therefore an address-space",
            "comparison artifact, not a reparse failure.",
            f"See [10_family_holdout_address_space_audit.md]({family_holdout_address_space_link}).",
            "",
            "### Address-Corrected Family Scoreboard",
            "",
            "Applying the same correction to all public-bookcase family holdouts",
            "changes the active comparison from `15/19` beat-or-tie families before",
            "correction to `19/19` after correction. Reparse still beats raw digits",
            "in `19/19` families, and the mean reparse-minus-active gap moves from",
            "`-139.959` to `-161.381` bits. This is stronger predictive recipe",
            "evidence, still not row0 derivation or semantics.",
            f"See [11_family_holdout_address_corrected_scoreboard.md]({family_holdout_address_corrected_scoreboard_link}).",
            "",
            "### No-Test-Carryover Family Holdout",
            "",
            "A stricter variant then removes cross-book carryover inside each held-out",
            "family. Each held-out book is parsed from the training-complement",
            "inventory alone. The result still roundtrips `19/19` families and beats",
            "raw digit coding in `19/19`, with mean gain `1054.570` bits versus raw.",
            "This shows the family signal does not depend on letting earlier held-out",
            "books feed later held-out books.",
            f"See [12_family_holdout_no_test_carryover_audit.md]({family_holdout_no_test_carryover_link}).",
            "",
            "### Leave-One-Book-Out No-Self Audit",
            "",
            "At singleton granularity, every book is then held out individually and",
            "reparsed from the other `69` books only. All `70/70` books roundtrip and",
            "beat raw digit coding; mean gain is `469.307` bits and the weakest gain",
            "is still `96.055` bits. This confirms item-level mechanical redundancy,",
            "while still not proving an authorial order because the inventory is the",
            "full complement of other books.",
            f"See [13_leave_one_book_out_no_self_audit.md]({leave_one_book_out_no_self_link}).",
            "",
            "### Leave-One-Book-Out Source Attribution",
            "",
            "The singleton result is then expanded into a source atlas. Across `70`",
            "singleton reparses there are `189` copy items and `11062` copied digits.",
            "The copied digits are attributable to concrete source books or, rarely,",
            "the already-emitted current prefix (`8` digits, share `0.000723`). The",
            "important caveat is explicit: `3001` copied digits (`0.271289`) cross",
            "artificial source-book boundaries created by concatenating the complement",
            "inventory without separators.",
            f"See [14_leave_one_book_out_source_attribution_audit.md]({leave_one_book_out_source_attribution_link}).",
            "",
            "### Book-Bounded Singleton Source Audit",
            "",
            "The boundary caveat is then tested directly by forbidding copy sources",
            "from crossing source-book boundaries. The singleton result survives:",
            "`70/70` books roundtrip and beat raw digit coding, mean gain remains",
            "`464.898` bits, and the mean penalty versus the unbounded singleton",
            "parser is only `4.409` bits.",
            f"See [15_leave_one_book_out_book_bounded_source_audit.md]({leave_one_book_out_book_bounded_source_link}).",
            "",
            "### Family-Excluded Singleton Source Audit",
            "",
            "The same singleton setup is then made stricter for public-bookcase",
            "families: when a target book has a known family label, all books in that",
            "same family are removed from both frozen train counts and copy sources.",
            "The result still roundtrips `70/70` books, beats raw digit coding in",
            "`70/70`, and the family-labeled subset beats raw in `46/46`. Mean gain",
            "is `460.251` bits, minimum gain is `56.053` bits, and the maximum penalty",
            "versus the book-bounded singleton parser is `119.076` bits. This reduces",
            "same-family memorization as an explanation for the singleton signal,",
            "while still not promoting a final authorial method.",
            f"See [16_leave_one_book_out_family_excluded_source_audit.md]({leave_one_book_out_family_excluded_source_link}).",
            "",
            "### Online Prefix Book Frontier Audit",
            "",
            "Finally, the deterministic online parser is decomposed at per-book",
            "granularity under the true numeric-prefix constraint: book `n` can use",
            "only books `< n` as external inventory. The book-bounded variant",
            "roundtrips `70/70`, beats raw digit coding in `69/70`, and the only",
            "failure is book `0`, before any prior-book inventory exists. After that",
            "bootstrap, it beats raw in `69/69` books; the cumulative book-bounded",
            "gain crosses break-even at book `2`. Mean book-bounded online gain is",
            "`419.761` bits. This strengthens sequential mechanical generation",
            "evidence while keeping the bootstrap caveat explicit.",
            f"See [17_online_prefix_book_frontier_audit.md]({online_prefix_book_frontier_link}).",
            "",
            "### Online Bootstrap Seed Policy Audit",
            "",
            "The bootstrap caveat is then tested directly as an accounting policy.",
            "Book `0` costs `488.857` bits under the online parser and `478.358`",
            "bits as a raw uniform seed, so the online cold start is `10.499` bits",
            "worse than raw. Charging book `0` as one explicit raw seed leaves books",
            "`1-69` unchanged and gives `70/70` wins-or-ties against raw, with",
            "`69/70` strict wins and no local failures. This closes the local",
            "bootstrap failure as a seed-policy issue, but is not promoted as a new",
            "compression bound or authorial proof.",
            f"See [18_online_bootstrap_seed_policy_audit.md]({online_bootstrap_seed_policy_link}).",
            "",
            "### Seeded Online Formula Rescore Audit",
            "",
            "The seed policy is then converted back into actual formula recipes and",
            "rescored under the complete active ledger. The result rejects promotion:",
            "the existing online formula remains `8343.062` bits, while replacing",
            "book `0` with one literal seed gives `8344.041` bits (`+0.979`). A",
            "book-bounded seeded variant is much worse at `8648.260` bits",
            "(`+305.198`). The seed is therefore retained only as bootstrap",
            "accounting, not as a new full-formula compression bound.",
            f"See [19_seeded_online_formula_rescore_audit.md]({seeded_online_formula_rescore_link}).",
            "",
            "### Seeded Rescore Loss Decomposition",
            "",
            "The rescore rejection is then decomposed by component. The seeded",
            "formula does save non-payload costs (`36.842` bits), but it adds a",
            "`37.821`-bit literal-payload penalty, leaving the formula `0.979` bits",
            "worse than online. In the book-bounded seeded variant, the largest",
            "penalty is copy address (`136.412` bits). This explains why the seed",
            "can close the local cold-start ledger while still failing complete",
            "formula scoring.",
            f"See [20_seeded_rescore_loss_decomposition.md]({seeded_rescore_loss_decomposition_link}).",
            "",
            "### Seed Exception Signal Cost Audit",
            "",
            "The last seed fallback is tested as an exception-signaling problem. Even",
            "the best-case zero-cost deterministic fallback is `+0.979` bits worse",
            "than the existing online formula. A one-book exception index would make",
            "the delta `+7.108` bits, and a bitmask would make it `+70.979` bits.",
            "Promotion would require a negative descriptor cost (`< -0.979` bits),",
            "so the seed exception cannot become a promoted formula under any",
            "nonnegative signaling cost.",
            f"See [21_seed_exception_signal_cost_audit.md]({seed_exception_signal_cost_link}).",
            "",
            "### Online Order Frontier Controls",
            "",
            "The per-book online frontier is then tested against the same order",
            "families used by the aggregate order-control audit. Numeric order still",
            "beats raw digit coding in `69/69` books after its first bootstrap",
            "position, but that criterion is not unique: `10/11` tested orders have",
            "perfect after-bootstrap raw wins, including `6/6` seeded random orders.",
            "The best after-bootstrap mean-gain and total-gain order is `random_04`,",
            "at `+0.549` bits versus numeric mean after-bootstrap gain and `+61.452`",
            "bits versus numeric total gain. This keeps the online frontier as",
            "predictive-parser evidence but rejects the stronger claim that the",
            "per-book frontier proves numeric book order.",
            f"See [22_online_order_frontier_controls.md]({online_order_frontier_controls_link}).",
            "",
            "### Order Frontier Promotion Gate",
            "",
            "The non-unique order-frontier result is then checked against the",
            "complete formula ledger. The local frontier winner, `random_04`, is",
            "`+61.452` bits better than numeric on book-bounded frontier total, but",
            "it is `+188.584` bits worse under the complete online formula before",
            "order cost and `+521.038` bits worse after the arbitrary permutation",
            "descriptor. No tested non-numeric order is promotable under a",
            "nonnegative descriptor. The frontier metric is therefore retained as",
            "a predictive diagnostic, not a compression-bound promotion score.",
            f"See [23_order_frontier_promotion_gate.md]({order_frontier_promotion_gate_link}).",
            "",
            "### Source Blocker Structural Context Gate",
            "",
            "The remaining cross-op optional-literal near tie is then tested as a",
            "source-cost blocker. The candidate is only `+0.027` bits worse than",
            "active, and a source-free oracle would be `-11.209` bits better, but",
            "that oracle is not decodable because it removes the required copy-source",
            "choice. The best tested simple source context, `book_half`, is still",
            "`+5.872` bits worse than the global source prior and loses in `5/5`",
            "prefix-frozen splits. This localizes the next source frontier: a future",
            "advance needs a new source derivation or representation, not a simple",
            "declared context split.",
            f"See [24_source_blocker_structural_context_gate.md]({source_blocker_structural_context_gate_link}).",
            "",
            "### Source Canonicality Decodability Gate",
            "",
            "The strongest source-derivation clue is then separated from decoder",
            "requirements. Every declared copy source is the earliest legal",
            "occurrence of the copied chunk (`261/261`), but only `123/261` source",
            "choices are unique at the declared length and `138/261` are ambiguous.",
            "More importantly, the earliest-exact-chunk rule depends on the future",
            "target chunk, which the decoder does not know until source and length",
            "are resolved. Source canonicality is therefore retained as encoder",
            "regularity, while the decodable default/exception source ledger remains",
            "the valid source representation.",
            f"See [25_source_canonicality_decodability_gate.md]({source_canonicality_decodability_gate_link}).",
            "",
            "### Source State Dependency Gate",
            "",
            "A final source-state gate then checks whether the active previous-copy",
            "source/length dependency can be removed by a decoder-computable",
            "state-free default. It cannot under the tested rules. The exact active",
            "reparse still needs state key",
            "`(book_pos, previous_item, previous_copy_source, previous_copy_length)`,",
            "and the best state-free rule, `state_free_back_current_length`, is",
            "`+15.186` bits worse on the full source ledger. It also loses all",
            "`5/5` prefix-frozen checks, with gap min/mean/max `7.652` /",
            "`14.615` / `22.840` bits. This keeps source state as a real",
            "generation-boundary dependency, not a removable tie-break.",
            f"See [26_source_state_dependency_gate.md]({source_state_dependency_gate_link}).",
            "",
            "### Copy Length Midpoint Context Gate",
            "",
            "The copy-length context is then checked as a positive generalization",
            "case. The active natural midpoint split, `book_id < 35`, beats the",
            "global copy-length context by `13.839` bits, ranks `2` among all",
            "one-cut boundaries, wins all `5/5` prefix-frozen future-suffix checks,",
            "and passes book-id permutation controls (`p=0.0033`). The best searched",
            "cutoff, `37`, is only `0.256` bits better than midpoint, so it is not",
            "promoted as a new boundary. This strengthens one learned mechanical",
            "component while leaving the full recipe and row0 origin unchanged.",
            f"See [27_copy_length_midpoint_context_gate.md]({copy_length_midpoint_context_gate_link}).",
            "",
            "## Row0 Origin Boundary",
            "",
            f"Row0 classification: `{result['row0_origin']['classification']}`",
            "",
            "### What Row0 Explains",
        ]
    )
    for item in result["row0_origin"]["what_row0_explains"]:
        lines.append(f"- {item}")
    lines.append("")
    lines.append("### What Remains Exogenous")
    for item in result["row0_origin"]["what_remains_exogenous"]:
        lines.append(f"- {item}")

    substrate = result["row0_origin"]["substrate_facts"]
    lines.extend(
        [
            "",
            "### Substrate Facts",
            "",
            f"- Books in committed digit corpus: `{substrate['book_count']}`",
            f"- Row0 symbols: `{substrate['row0_symbol_count']}`",
            f"- Class codes represented: `{substrate['class_code_count']}`",
            f"- Missing two-digit codes from class map: `{substrate['missing_two_digit_codes']}`",
            f"- Sources: [`occ_streams.json`]({audit_link_prefix}/homophone_channel/occ_streams.json), [`books_digits.json`]({audit_link_prefix}/books_digits.json)",
            "",
            "### Origin Hypotheses",
            "",
            "| Hypothesis | Status | Coverage | Cost | Contradictions / controls |",
            "|---|---|---|---:|---|",
        ]
    )
    for row in result["row0_origin"]["hypotheses"]:
        cost = row["descriptive_cost_bits"]
        cost_text = f"{cost:.3f}" if isinstance(cost, (int, float)) else str(cost)
        lines.append(
            f"| `{row['hypothesis']}` | `{row['status']}` | {row['coverage']} | "
            f"{cost_text} | {row['contradictions']}; controls `{row['negative_controls']}` |"
        )

    lines.extend(
        [
            "",
            "### Row0 Requirement Matrix Follow-Up",
            "",
            "A requirement-matrix follow-up forces all six requested row0-origin families",
            "through the same checklist: algorithm, descriptive cost, coverage,",
            "contradictions, negative controls, and random/permuted comparison. All six",
            "families have explicit entries; promoted row0-origin formulas remain `0`.",
            "Lookup baselines are `160.521` bits given inventory, `209.405` bits for the",
            "direct symbol alphabet, and `214.879` bits for the direct observed-label",
            "alphabet.",
            f"See [05_row0_hypothesis_requirement_audit.md]({row0_requirement_link}).",
            "",
            "## Decision",
            "",
            "- `8558.667` bits remains a frozen validation scope here, not a final authorial method.",
            "- The learned component signal survives prefix and block holdout but fails some family holdouts, so it is not promoted beyond partial predictive structure.",
            "- The full-corpus fixed-recipe limitation is partially reduced by deterministic reparse evidence; after same-coordinate address correction, public-bookcase family reparse beats or ties the active family recipe in `19/19` families, a no-test-carryover variant still beats raw in `19/19`, singleton leave-one-book-out reparsing beats raw in `70/70`, singleton copy sources are attributed, the signal survives book-bounded and same-family-excluded source constraints, the online previous-books-only frontier is positive after the bootstrap book, and a raw book-0 seed policy closes the remaining local failure but fails complete-formula promotion because literal-payload cost dominates and any exception signal would require negative cost.",
            "- Source-state simplification is rejected: canonicality is encoder-side only, and state-free source defaults lose to the active previous-copy source/length default in the full ledger and every tested prefix-frozen split.",
            "- Copy-length midpoint context is retained as a generalizing natural split; the searched cutoff `37` is rejected as ad-hoc for only `0.256` bits over midpoint.",
            "- All requested row0-origin hypothesis families have been checklist-audited; none passes as an origin formula.",
            "- `row0` continues exogenous: the active book generator assumes the table rather than deriving it.",
            "- No translation, plaintext, or case reopening is introduced.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    legacy_module = load_module(LEGACY_SCRIPT)
    legacy_module.main()
    legacy = load_json(LEGACY_RESULT)
    if abs(float(legacy["compression_bound_bits_confirmed"]) - SCOPE_COMPRESSION_BOUND_BITS) > 1e-6:
        raise RuntimeError("legacy audit no longer matches frozen 8558.667-bit scope")
    result = make_result(legacy)

    TEST_RESULTS.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    result_path = TEST_RESULTS / "01_prequential_and_row0_origin_audit.json"
    report_path = TEST_RESULTS / "01_prequential_and_row0_origin_audit.md"
    final_report_path = REPORTS / "prequential_and_row0_origin_audit.md"

    result_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report_path.write_text(
        render_markdown(
            result,
            audit_link_prefix="../../../audit_20260609",
            family_failure_link="02_family_holdout_failure_audit.md",
            component_selector_link="03_train_cv_component_selector_audit.md",
            recipe_externality_link="04_recipe_externality_audit.md",
            recipe_reparse_matrix_link="06_recipe_reparse_evidence_matrix.md",
            recipe_family_holdout_link="08_recipe_reparse_family_holdout.md",
            recipe_family_loss_decomposition_link="09_recipe_reparse_family_loss_decomposition.md",
            family_holdout_address_space_link="10_family_holdout_address_space_audit.md",
            family_holdout_address_corrected_scoreboard_link="11_family_holdout_address_corrected_scoreboard.md",
            family_holdout_no_test_carryover_link="12_family_holdout_no_test_carryover_audit.md",
            leave_one_book_out_no_self_link="13_leave_one_book_out_no_self_audit.md",
            leave_one_book_out_source_attribution_link=(
                "14_leave_one_book_out_source_attribution_audit.md"
            ),
            leave_one_book_out_book_bounded_source_link=(
                "15_leave_one_book_out_book_bounded_source_audit.md"
            ),
            leave_one_book_out_family_excluded_source_link=(
                "16_leave_one_book_out_family_excluded_source_audit.md"
            ),
            online_prefix_book_frontier_link="17_online_prefix_book_frontier_audit.md",
            online_bootstrap_seed_policy_link="18_online_bootstrap_seed_policy_audit.md",
            seeded_online_formula_rescore_link="19_seeded_online_formula_rescore_audit.md",
            seeded_rescore_loss_decomposition_link=(
                "20_seeded_rescore_loss_decomposition.md"
            ),
            seed_exception_signal_cost_link="21_seed_exception_signal_cost_audit.md",
            online_order_frontier_controls_link="22_online_order_frontier_controls.md",
            order_frontier_promotion_gate_link="23_order_frontier_promotion_gate.md",
            source_blocker_structural_context_gate_link=(
                "24_source_blocker_structural_context_gate.md"
            ),
            source_canonicality_decodability_gate_link=(
                "25_source_canonicality_decodability_gate.md"
            ),
            source_state_dependency_gate_link="26_source_state_dependency_gate.md",
            copy_length_midpoint_context_gate_link=(
                "27_copy_length_midpoint_context_gate.md"
            ),
            row0_requirement_link="05_row0_hypothesis_requirement_audit.md",
        ),
        encoding="utf-8",
    )
    final_report_path.write_text(
        render_markdown(
            result,
            audit_link_prefix="../../audit_20260609",
            family_failure_link="test_results/02_family_holdout_failure_audit.md",
            component_selector_link="test_results/03_train_cv_component_selector_audit.md",
            recipe_externality_link="test_results/04_recipe_externality_audit.md",
            recipe_reparse_matrix_link="test_results/06_recipe_reparse_evidence_matrix.md",
            recipe_family_holdout_link="test_results/08_recipe_reparse_family_holdout.md",
            recipe_family_loss_decomposition_link="test_results/09_recipe_reparse_family_loss_decomposition.md",
            family_holdout_address_space_link="test_results/10_family_holdout_address_space_audit.md",
            family_holdout_address_corrected_scoreboard_link=(
                "test_results/11_family_holdout_address_corrected_scoreboard.md"
            ),
            family_holdout_no_test_carryover_link=(
                "test_results/12_family_holdout_no_test_carryover_audit.md"
            ),
            leave_one_book_out_no_self_link="test_results/13_leave_one_book_out_no_self_audit.md",
            leave_one_book_out_source_attribution_link=(
                "test_results/14_leave_one_book_out_source_attribution_audit.md"
            ),
            leave_one_book_out_book_bounded_source_link=(
                "test_results/15_leave_one_book_out_book_bounded_source_audit.md"
            ),
            leave_one_book_out_family_excluded_source_link=(
                "test_results/16_leave_one_book_out_family_excluded_source_audit.md"
            ),
            online_prefix_book_frontier_link=(
                "test_results/17_online_prefix_book_frontier_audit.md"
            ),
            online_bootstrap_seed_policy_link=(
                "test_results/18_online_bootstrap_seed_policy_audit.md"
            ),
            seeded_online_formula_rescore_link=(
                "test_results/19_seeded_online_formula_rescore_audit.md"
            ),
            seeded_rescore_loss_decomposition_link=(
                "test_results/20_seeded_rescore_loss_decomposition.md"
            ),
            seed_exception_signal_cost_link=(
                "test_results/21_seed_exception_signal_cost_audit.md"
            ),
            online_order_frontier_controls_link=(
                "test_results/22_online_order_frontier_controls.md"
            ),
            order_frontier_promotion_gate_link=(
                "test_results/23_order_frontier_promotion_gate.md"
            ),
            source_blocker_structural_context_gate_link=(
                "test_results/24_source_blocker_structural_context_gate.md"
            ),
            source_canonicality_decodability_gate_link=(
                "test_results/25_source_canonicality_decodability_gate.md"
            ),
            source_state_dependency_gate_link=(
                "test_results/26_source_state_dependency_gate.md"
            ),
            copy_length_midpoint_context_gate_link=(
                "test_results/27_copy_length_midpoint_context_gate.md"
            ),
            row0_requirement_link="test_results/05_row0_hypothesis_requirement_audit.md",
        ),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
