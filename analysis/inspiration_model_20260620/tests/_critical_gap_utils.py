from __future__ import annotations

import hashlib
import json
import random
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean, pstdev

from _common import HERE, ROOT, write_result

RNG = random.Random(46920260620)
CONTROL_TRIALS = 2000
ANCHORS = ["3478", "486486", "486", "74032", "45331", "43153", "34784", "469", "99", "1", "0"]


def load_json(rel: str):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def load_books() -> dict[str, str]:
    return load_json("analysis/audit_20260609/books_digits.json")


def load_tape() -> dict:
    return load_json("analysis/generator_search_20260618/tape_based_formula_469.json")


def numeric_book_ids(books: dict[str, str]) -> list[str]:
    return sorted(books, key=lambda x: int(x))


def find_all(text: str, needle: str) -> list[int]:
    if not needle:
        return []
    out: list[int] = []
    start = 0
    while True:
        idx = text.find(needle, start)
        if idx < 0:
            return out
        out.append(idx)
        start = idx + 1


def parse_codes(anchor: str) -> list[dict]:
    parses: list[dict] = []
    for phase in (0, 1):
        prefix = anchor[:phase]
        rest = anchor[phase:]
        codes = [rest[i : i + 2] for i in range(0, len(rest) - 1, 2)]
        suffix = rest[len(codes) * 2 :]
        parses.append({"phase": phase, "prefix": prefix, "codes": codes, "suffix": suffix})
    return parses


def project_codes(codes: list[str], code_to_symbol: dict[str, str]) -> dict:
    projected = [code_to_symbol.get(code) for code in codes]
    return {
        "codes": codes,
        "symbols": projected,
        "known_codes": sum(sym is not None for sym in projected),
        "unknown_codes": [code for code, sym in zip(codes, projected) if sym is None],
        "touches_zero": any("0" in code for code in codes),
        "touches_missing_39": "39" in codes,
        "touches_orphan_93": "93" in codes,
    }


def recipe_spans(recipe: list[dict]) -> list[dict]:
    spans: list[dict] = []
    cursor = 0
    for item in recipe:
        length = int(item.get("length", 0))
        spans.append({"start": cursor, "end": cursor + length, "item": item})
        cursor += length
    return spans


def locate_recipe_item(recipe: list[dict], start: int, end: int) -> dict | None:
    for span in recipe_spans(recipe):
        if start >= span["start"] and end <= span["end"]:
            item = span["item"]
            return {
                "type": item.get("type"),
                "module_id": item.get("id"),
                "component_id": item.get("component_id"),
                "item_start": span["start"],
                "item_end": span["end"],
            }
    return None


def pct_rank_ge(observed: float, values: list[float]) -> float:
    return (sum(v >= observed for v in values) + 1) / (len(values) + 1)


def summarize_controls(observed: float, values: list[float]) -> dict:
    return {
        "observed": observed,
        "control_mean": mean(values) if values else 0.0,
        "control_sd": pstdev(values) if len(values) > 1 else 0.0,
        "control_min": min(values) if values else 0.0,
        "control_max": max(values) if values else 0.0,
        "p_ge": pct_rank_ge(observed, values),
    }


def random_digits(length: int, weights: Counter[str]) -> str:
    digits = list(weights)
    total = sum(weights.values())
    cumulative: list[tuple[float, str]] = []
    acc = 0
    for digit in digits:
        acc += weights[digit]
        cumulative.append((acc / total, digit))
    out = []
    for _ in range(length):
        x = RNG.random()
        for threshold, digit in cumulative:
            if x <= threshold:
                out.append(digit)
                break
    return "".join(out)


def write_standard(name: str, title: str, result: dict, body: list[str]) -> None:
    lines = [
        f"# {title}",
        "",
        f"Verdict: `{result['classification']}`. Translation delta: `{result['translation_delta']}`.",
        "",
    ]
    lines.extend(body)
    write_result(name, result, lines)


def boundary_safe_anchor_audit() -> None:
    books = load_books()
    tape = load_tape()
    book_ids = numeric_book_ids(books)
    raw_corpus = "".join(books[bid] for bid in book_ids)
    spans = []
    cursor = 0
    for bid in book_ids:
        text = books[bid]
        spans.append({"book": bid, "start": cursor, "end": cursor + len(text)})
        cursor += len(text)

    tape_text = "".join(component["text"] for component in tape["tape_components"])
    module_texts = {m["id"]: tape["tape_components"][int(m["component_id"][1:])]["text"][m["start"] : m["end"]] for m in tape["module_slices"]}

    rows = []
    for anchor in ANCHORS:
        per_book = {bid: find_all(books[bid], anchor) for bid in book_ids}
        safe_hits = sum(len(v) for v in per_book.values())
        raw_hits = find_all(raw_corpus, anchor)
        cross = []
        for pos in raw_hits:
            end = pos + len(anchor)
            owner = next((span for span in spans if pos >= span["start"] and end <= span["end"]), None)
            if owner is None:
                cross.append({"start": pos, "end": end})
        rows.append({
            "anchor": anchor,
            "boundary_safe_hits": safe_hits,
            "books_hit": sum(1 for hits in per_book.values() if hits),
            "raw_concatenated_hits": len(raw_hits),
            "cross_book_false_hits": len(cross),
            "tape_hits": len(find_all(tape_text, anchor)),
            "module_hits": sum(len(find_all(text, anchor)) for text in module_texts.values()),
            "hit_offset_mod2": dict(Counter(pos % 2 for hits in per_book.values() for pos in hits)),
            "sample_hits": [
                {"book": bid, "offset": pos}
                for bid, hits in per_book.items()
                for pos in hits[:3]
            ][:12],
        })

    result = {
        "schema": "critical_gap_audit.v1",
        "test": "boundary_safe_anchor_audit",
        "classification": "rejected_control",
        "translation_delta": "NONE",
        "anchors": rows,
        "cross_book_false_hit_total": sum(row["cross_book_false_hits"] for row in rows),
        "scope_note": "Exact lore/source anchor hits are counted inside book boundaries and compared with raw concatenation.",
    }
    body = [
        "This replaces raw `''.join(book_strings)` anchor counting with per-book",
        "counts and an explicit cross-boundary false-hit check.",
        "",
        "| Anchor | Book-safe hits | Books hit | Raw concat hits | Cross-book false hits | Tape hits | Module hits |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        body.append(
            f"| `{row['anchor']}` | {row['boundary_safe_hits']} | {row['books_hit']} | "
            f"{row['raw_concatenated_hits']} | {row['cross_book_false_hits']} | {row['tape_hits']} | {row['module_hits']} |"
        )
    body += [
        "",
        "Stop rule: boundary-safe substring presence alone is not a formula,",
        "codebook, plaintext, or semantic promotion.",
    ]
    write_standard("boundary_safe_anchor_audit", "Boundary-Safe Anchor Audit", result, body)


def aligned_numeric_anchor_audit() -> None:
    books = load_books()
    tape = load_tape()
    code_to_symbol = tape["code_to_symbol"]
    rows = []
    for anchor in ANCHORS:
        parses = []
        for parsed in parse_codes(anchor):
            projected = project_codes(parsed["codes"], code_to_symbol)
            parses.append({**parsed, **projected})
        hits = []
        for bid in numeric_book_ids(books):
            for pos in find_all(books[bid], anchor):
                context = locate_recipe_item(tape["book_recipes"].get(bid, []), pos, pos + len(anchor))
                hits.append({
                    "book": bid,
                    "offset": pos,
                    "offset_mod2": pos % 2,
                    "zero_left": pos > 0 and books[bid][pos - 1] == "0",
                    "zero_right": pos + len(anchor) < len(books[bid]) and books[bid][pos + len(anchor)] == "0",
                    "recipe_context": context,
                })
        rows.append({
            "anchor": anchor,
            "hit_count": len(hits),
            "offset_mod2": dict(Counter(hit["offset_mod2"] for hit in hits)),
            "parses": parses,
            "sample_hits": hits[:12],
            "classification": "absent_or_blocked" if not hits else "structural_overlap_not_key",
        })

    result = {
        "schema": "critical_gap_audit.v1",
        "test": "aligned_numeric_anchor_audit",
        "classification": "rejected_control",
        "translation_delta": "NONE",
        "anchors": rows,
        "scope_note": "Every anchor is checked against 2-digit row0 alignment and local tape/module context.",
    }
    body = [
        "Exact numeric hits are projected into 2-digit row0/code space before",
        "any interpretation. Odd-length seeds are kept as partially unpaired,",
        "not silently promoted to valid code sequences.",
        "",
        "| Anchor | Hits | Offset mod 2 | Status |",
        "|---|---:|---|---|",
    ]
    for row in rows:
        body.append(f"| `{row['anchor']}` | {row['hit_count']} | `{row['offset_mod2']}` | `{row['classification']}` |")
    body += [
        "",
        "Stop rule: a seed that cannot become a boundary-aligned lower-cost",
        "mechanical formula remains a source/lore anchor only.",
    ]
    write_standard("aligned_numeric_anchor_audit", "Aligned Numeric Anchor Audit", result, body)


def physical_library_topology_audit() -> None:
    manifest_candidates = [
        HERE / "physical_library_topology_manifest.yaml",
        HERE / "physical_library_topology_manifest.json",
        ROOT / "data" / "physical_library_topology_manifest.yaml",
        ROOT / "data" / "physical_library_topology_manifest.json",
    ]
    found = [path for path in manifest_candidates if path.exists()]
    required_fields = [
        "book_id",
        "source_location",
        "room_or_library",
        "shelf_or_container",
        "tile_or_position",
        "read_order",
        "capture_source_url_or_commit",
        "verification_date",
    ]
    result = {
        "schema": "critical_gap_audit.v1",
        "test": "physical_library_topology_audit",
        "classification": "blocked_waiting_for_physical_metadata" if not found else "watchlist_only",
        "translation_delta": "NONE",
        "manifest_candidates": [str(path.relative_to(ROOT)) for path in manifest_candidates],
        "found_manifests": [str(path.relative_to(ROOT)) for path in found],
        "required_fields": required_fields,
        "blocker": None if found else "No committed, authoritative per-book physical topology/order manifest is present.",
    }
    body = [
        "This audit intentionally does not infer shelf order from filenames,",
        "book ids, source prose, or community lore.",
        "",
        "| Candidate manifest | Present |",
        "|---|---:|",
    ]
    for path in manifest_candidates:
        body.append(f"| `{path.relative_to(ROOT)}` | `{path.exists()}` |")
    body += [
        "",
        "Required manifest fields:",
        "",
    ]
    body.extend(f"- `{field}`" for field in required_fields)
    if not found:
        body += ["", "Blocker: no physical/topological metadata is committed, so topology tests remain blocked."]
    write_standard("physical_library_topology_audit", "Physical Library Topology Audit", result, body)


def assembly_path_inference_audit() -> None:
    tape = load_tape()
    manifest = load_json("analysis/generator_search_20260618/generator_holdout_manifest.json")
    recipes = tape["book_recipes"]

    def token(item: dict) -> str:
        if item.get("type") == "literal":
            return f"LITERAL:{item.get('length')}:{item.get('text')}"
        return f"{item.get('component_id')}:{item.get('id')}"

    sequences = {bid: [token(item) for item in recipe] for bid, recipe in recipes.items()}
    transition_counts: Counter[tuple[str, str]] = Counter()
    for seq in sequences.values():
        transition_counts.update(zip(seq, seq[1:]))

    train_books = set(manifest["book_training"])
    holdout_books = set(manifest["book_holdouts"])
    train_transitions: dict[str, Counter[str]] = defaultdict(Counter)
    for bid, seq in sequences.items():
        if bid not in train_books:
            continue
        for a, b in zip(seq, seq[1:]):
            train_transitions[a][b] += 1
    majority_next = {a: counts.most_common(1)[0][0] for a, counts in train_transitions.items()}
    holdout_pairs = [(a, b) for bid, seq in sequences.items() if bid in holdout_books for a, b in zip(seq, seq[1:])]
    observed_correct = sum(1 for a, b in holdout_pairs if majority_next.get(a) == b)
    observed_acc = observed_correct / len(holdout_pairs) if holdout_pairs else 0.0
    labels = [b for _, b in holdout_pairs]
    controls = []
    for _ in range(CONTROL_TRIALS):
        shuffled = labels[:]
        RNG.shuffle(shuffled)
        controls.append(sum(1 for (a, _), b in zip(holdout_pairs, shuffled) if majority_next.get(a) == b) / len(holdout_pairs) if holdout_pairs else 0.0)

    result = {
        "schema": "critical_gap_audit.v1",
        "test": "assembly_path_inference_audit",
        "classification": "rejected_control",
        "translation_delta": "NONE",
        "sequence_count": len(sequences),
        "distinct_tokens": len({tok for seq in sequences.values() for tok in seq}),
        "distinct_transitions": len(transition_counts),
        "top_transitions": [{"from": a, "to": b, "count": c} for (a, b), c in transition_counts.most_common(15)],
        "holdout_transition_accuracy": summarize_controls(observed_acc, controls),
        "scope_note": "Assembly transitions describe the accepted tape reconstruction but do not improve semantic formula discovery.",
    }
    body = [
        "This audits whether the tape recipe path itself provides an independent",
        "predictive formula direction. The test uses existing generator holdouts",
        "and transition controls.",
        "",
        f"- Distinct recipe tokens: `{result['distinct_tokens']}`",
        f"- Distinct transitions: `{result['distinct_transitions']}`",
        f"- Holdout transition accuracy: `{observed_acc:.4f}`",
        f"- Control p_ge: `{result['holdout_transition_accuracy']['p_ge']:.4f}`",
        "",
        "Stop rule: assembly regularity is retained as reconstruction mechanics,",
        "not as plaintext or a new semantic decoder.",
    ]
    write_standard("assembly_path_inference_audit", "Assembly Path Inference Audit", result, body)


def numeric_identity_graph_motif_real() -> None:
    tape = load_tape()
    code_to_symbol = tape["code_to_symbol"]
    weights = Counter("".join(load_books().values()))
    motif_codes = {"00", "33", "34", "39", "66", "78", "93", "86", "48", "64"}

    def score(seed: str) -> float:
        best = 0.0
        for parsed in parse_codes(seed):
            codes = parsed["codes"]
            if not codes:
                continue
            projected = project_codes(codes, code_to_symbol)
            known = projected["known_codes"] / len(codes)
            motif = sum(code in motif_codes for code in codes) / len(codes)
            zero = 0.25 if projected["touches_zero"] else 0.0
            best = max(best, known + motif + zero)
        return best

    rows = []
    for seed in ANCHORS:
        observed = score(seed)
        controls = [score(random_digits(len(seed), weights)) for _ in range(CONTROL_TRIALS)]
        summary = summarize_controls(observed, controls)
        rows.append({
            "seed": seed,
            "score": observed,
            "control_summary": summary,
            "parses": [{**p, **project_codes(p["codes"], code_to_symbol)} for p in parse_codes(seed)],
            "classification": "weak_clue" if summary["p_ge"] <= 0.01 and observed > 0 else "rejected_control",
        })

    result = {
        "schema": "critical_gap_audit.v1",
        "test": "numeric_identity_graph_motif_real",
        "classification": "rejected_control",
        "translation_delta": "NONE",
        "seeds": rows,
        "motif_codes": sorted(motif_codes),
    }
    body = [
        "This replaces loose identity-number discussion with a code-graph motif",
        "score and same-length digit controls.",
        "",
        "| Seed | Score | p_ge | Classification |",
        "|---|---:|---:|---|",
    ]
    for row in rows:
        body.append(
            f"| `{row['seed']}` | {row['score']:.3f} | "
            f"{row['control_summary']['p_ge']:.4f} | `{row['classification']}` |"
        )
    body += ["", "Stop rule: local motif enrichment is not a symbol-letter or word-code mapping."]
    write_standard("numeric_identity_graph_motif_real", "Numeric Identity Graph Motif Audit", result, body)


def official_source_snapshot_audit() -> None:
    text = (HERE / "source_registry.yaml").read_text(encoding="utf-8")
    sources = []
    current: dict[str, str] = {}
    for raw in text.splitlines():
        line = raw.strip()
        if line.startswith("- id: "):
            if current:
                sources.append(current)
            current = {"id": line.split(": ", 1)[1]}
        elif current and ": " in line:
            key, value = line.split(": ", 1)
            current[key] = value.strip('"')
    if current:
        sources.append(current)

    required = ["text_presence", "officiality", "interpretation_risk", "semantic_authority"]
    rows = []
    for source in sources:
        url = source.get("source_url", "")
        rows.append({
            "id": source.get("id"),
            "source_url_sha256": hashlib.sha256(url.encode("utf-8")).hexdigest() if url else None,
            "has_normalized_fields": all(field in source for field in required),
            "text_presence": source.get("text_presence"),
            "officiality": source.get("officiality"),
            "semantic_authority": source.get("semantic_authority"),
        })
    result = {
        "schema": "critical_gap_audit.v1",
        "test": "official_source_snapshot_audit",
        "classification": "source_registry",
        "translation_delta": "NONE",
        "required_normalized_fields": required,
        "source_count": len(rows),
        "sources_with_normalized_fields": sum(row["has_normalized_fields"] for row in rows),
        "sources": rows,
        "scope_note": "Snapshot hashes URLs and verifies registry field separation; it does not claim live source retrieval.",
    }
    body = [
        "This audit separates text presence, source officiality, interpretation",
        "risk, and semantic authority from the older `CONFIRMED_SOURCE` label.",
        "",
        "| Source | Normalized fields | Officiality | Semantic authority | URL sha256 prefix |",
        "|---|---:|---|---|---|",
    ]
    for row in rows:
        digest = row["source_url_sha256"][:12] if row["source_url_sha256"] else ""
        body.append(
            f"| `{row['id']}` | `{row['has_normalized_fields']}` | "
            f"`{row['officiality']}` | `{row['semantic_authority']}` | `{digest}` |"
        )
    write_standard("official_source_snapshot_audit", "Official Source Snapshot Audit", result, body)


def dnd_central_eye_formal_model() -> None:
    paths = [
        "analysis/generator_search_20260618/zero_compact_rule_results.json",
        "analysis/generator_search_20260618/zero_omission_rule_explainer_results.json",
        "analysis/generator_search_20260618/shared_e_zero_predicate_results.json",
    ]
    inputs = {}
    for path in paths:
        p = ROOT / path
        inputs[path] = json.loads(p.read_text(encoding="utf-8")) if p.exists() else None
    result = {
        "schema": "critical_gap_audit.v1",
        "test": "dnd_central_eye_formal_model",
        "classification": "weak_clue",
        "translation_delta": "NONE",
        "formal_hypotheses": [
            "central_eye_as_zero",
            "central_eye_as_omitted_zero",
            "central_eye_as_missing_39_or_orphan_93",
            "central_eye_as_render_suppression_context",
        ],
        "input_reports_present": {path: value is not None for path, value in inputs.items()},
        "scope_note": "Formalizes the D&D central-eye analogy against existing zero/render reports only.",
    }
    body = [
        "Central-eye hypotheses are formalized as zero/omission/render variants.",
        "Existing zero reports are present, but none provides official text or a",
        "lower-cost semantic decoder.",
        "",
        "| Input | Present |",
        "|---|---:|",
    ]
    for path, present in result["input_reports_present"].items():
        body.append(f"| `{path}` | `{present}` |")
    body += ["", "Stop rule: D&D analogy remains mechanism inspiration only."]
    write_standard("dnd_central_eye_formal_model", "D&D Central Eye Formal Model", result, body)


def dnd_eye_ray_order_model() -> None:
    fixed_order = HERE / "dnd_eye_ray_order_fixed.yaml"
    result = {
        "schema": "critical_gap_audit.v1",
        "test": "dnd_eye_ray_order_model",
        "classification": "blocked_waiting_for_fixed_external_order",
        "translation_delta": "NONE",
        "required_input": str(fixed_order.relative_to(ROOT)),
        "required_fields": ["source_url", "edition", "ray_order", "extraction_date"],
        "blocker": "No committed fixed external eye-ray order source is present.",
    }
    body = [
        "This test is intentionally blocked unless a fixed external D&D ray order",
        "is committed before fitting. Fitting an order from row0 would leak the",
        "target and create a pareidolia route.",
        "",
        f"Required input: `{fixed_order.relative_to(ROOT)}`",
    ]
    write_standard("dnd_eye_ray_order_model", "D&D Eye-Ray Order Model", result, body)


def quest_mechanism_feature_matrix() -> None:
    files = [
        HERE / "quest_mechanism_ontology.yaml",
        HERE / "knightmare_design_corpus.yaml",
        HERE / "dnd_beholder_mechanism_registry.yaml",
    ]
    features = ["key", "lever", "door", "keyword", "teleport", "vocation", "faction", "dream", "library", "entity", "calculator", "magic web", "zero", "dice"]
    rows = []
    for path in files:
        text = path.read_text(encoding="utf-8").lower() if path.exists() else ""
        rows.append({
            "file": str(path.relative_to(ROOT)),
            "present": path.exists(),
            "feature_hits": {feature: text.count(feature) for feature in features},
        })
    result = {
        "schema": "critical_gap_audit.v1",
        "test": "quest_mechanism_feature_matrix",
        "classification": "watchlist_only",
        "translation_delta": "NONE",
        "feature_matrix": rows,
        "blocker": "Feature corpus exists, but no committed per-book feature alignment target exists.",
    }
    body = [
        "Quest features are counted as a corpus matrix, not as a decoder.",
        "",
        "| Corpus file | Present | Nonzero feature count |",
        "|---|---:|---:|",
    ]
    for row in rows:
        body.append(f"| `{row['file']}` | `{row['present']}` | {sum(1 for v in row['feature_hits'].values() if v)} |")
    body += ["", "Stop rule: without book-level feature targets, this remains ontology/watchlist only."]
    write_standard("quest_mechanism_feature_matrix", "Quest Mechanism Feature Matrix", result, body)


def expanded_negative_control_suite() -> None:
    books = load_books()
    manifest = load_json("analysis/generator_search_20260618/generator_holdout_manifest.json")
    substring_sets = set()
    for text in books.values():
        for length in range(5, 13):
            for i in range(0, max(0, len(text) - length + 1)):
                substring_sets.add(text[i : i + length])
    weights = Counter("".join(books.values()))
    controls = {
        "avar_tar": "".join(manifest["negative_controls"]["avar_tar"]),
        "your_true_colour": "".join(manifest["external_holdouts"]["your_true_colour"]),
        "secret_library_74032_45331": "7403245331",
        "honeminas_vectors": "4315334784",
        "spirit_grounds_gate_keeper": None,
        "paradox_mirror": None,
        "evil_mastermind_dictionary": None,
    }

    def coverage(s: str) -> float:
        if not s:
            return 0.0
        covered = [False] * len(s)
        for length in range(12, 4, -1):
            for i in range(0, len(s) - length + 1):
                if s[i : i + length] in substring_sets:
                    for j in range(i, i + length):
                        covered[j] = True
        return sum(covered) / len(s)

    rows = []
    for name, digits in controls.items():
        if digits is None:
            rows.append({"name": name, "status": "blocked_missing_numeric_source", "coverage": None, "control_summary": None})
            continue
        observed = coverage(digits)
        randoms = [coverage(random_digits(len(digits), weights)) for _ in range(500)]
        rows.append({"name": name, "status": "tested", "coverage": observed, "control_summary": summarize_controls(observed, randoms)})
    result = {
        "schema": "critical_gap_audit.v1",
        "test": "expanded_negative_control_suite",
        "classification": "partial_negative_control_suite",
        "translation_delta": "NONE",
        "controls": rows,
        "scope_note": "Available numeric controls are tested; lore-only controls stay blocked until numeric sources are committed.",
    }
    body = [
        "This expands the negative-control inventory and refuses to fabricate",
        "numeric strings for lore-only controls.",
        "",
        "| Control | Status | Coverage | p_ge |",
        "|---|---|---:|---:|",
    ]
    for row in rows:
        pge = row["control_summary"]["p_ge"] if row["control_summary"] else None
        cov = f"{row['coverage']:.3f}" if row["coverage"] is not None else ""
        body.append(f"| `{row['name']}` | `{row['status']}` | {cov} | {'' if pge is None else f'{pge:.4f}'} |")
    body += ["", "Stop rule: control overlap never becomes positive semantic evidence."]
    write_standard("expanded_negative_control_suite", "Expanded Negative Control Suite", result, body)
