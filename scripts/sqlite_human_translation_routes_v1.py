#!/usr/bin/env python3
"""Register human-translation search routes without promoting prose gloss.

The canonical decode layer remains structural/function-only. This script adds a
shadow operating layer for plausible human readings, grounded first in in-game
anchors and secondarily in public/official-adjacent references.
"""

from __future__ import annotations

import datetime as dt
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "bonelord_operational.sqlite"


SOURCES = [
    {
        "source_id": "FANDOM_469_STATUS",
        "source_url": "https://tibia.fandom.com/wiki/469",
        "source_label": "TibiaWiki Fandom 469",
        "source_kind": "PUBLIC_GAME_WIKI",
        "in_game_anchor": "Hellgate Library and Isle of the Kings 469 books",
        "finding": "469 is Bonelord language; public translation claims are not solid proof.",
        "translation_use": "status guard and corpus locator",
        "risk": "secondary wiki; not exact plaintext",
        "gloss_allowed": 0,
    },
    {
        "source_id": "WRINKLED_BONELORD_TRANSCRIPT",
        "source_url": "https://tibia.fandom.com/wiki/A_Wrinkled_Bonelord/Transcripts",
        "source_label": "A Wrinkled Bonelord transcript",
        "source_kind": "NPC_TRANSCRIPT",
        "in_game_anchor": "Hellgate librarian NPC",
        "finding": "NPC anchors 486486, Tibia=1, 0 taboo, numbers, mathemagic, and name-as-formula.",
        "translation_use": "primary semantic constraint, not a book translation",
        "risk": "transcript source is secondary, but content is in-game dialogue",
        "gloss_allowed": 0,
    },
    {
        "source_id": "TIBIAWIKI_BR_469_SYNTHESIS",
        "source_url": "https://www.tibiawiki.com.br/469",
        "source_label": "TibiaWiki BR 469",
        "source_kind": "PUBLIC_GAME_WIKI_SYNTHESIS",
        "in_game_anchor": "Knightmare, Chayenne, Avar Tar, Wyrdin, A Prisoner, Hellgate matrix, Great Calculator",
        "finding": "Collects several in-game and interview-style 469/Bonelord anchors useful for shadow testing.",
        "translation_use": "source inventory for cross-corpus comparison",
        "risk": "mixed provenance; each anchor must be verified before promotion",
        "gloss_allowed": 0,
    },
    {
        "source_id": "PARADOX_TOWER_MATHEMAGICS",
        "source_url": "https://www.tibia-wiki.net/wiki/Paradox_Tower_Quest/Spoiler",
        "source_label": "Paradox Tower Quest spoiler",
        "source_kind": "QUEST_TRANSCRIPT",
        "in_game_anchor": "Riddler, Mintwallin prisoner, Hellgate detour, mathemagics lesson",
        "finding": "The quest binds surreal numbers, mathemagics, and variable 1+1 answers to a concrete in-game puzzle.",
        "translation_use": "mathemagic operator constraints and quest-context bridge",
        "risk": "spoiler/wiki transcription; result varies per player",
        "gloss_allowed": 0,
    },
    {
        "source_id": "YOU_CANNOT_EVEN_IMAGINE",
        "source_url": "https://www.tibiawiki.com.br/wiki/You_Cannot_Even_Imagine_%28Book%29",
        "source_label": "You Cannot Even Imagine book",
        "source_kind": "BOOK_TEXT",
        "in_game_anchor": "Translated book in Tibia libraries",
        "finding": "Mentions helping the Great Calculator gather the Bonelord language.",
        "translation_use": "lore hypothesis: corpus may be gathered/compiled rather than single prose message",
        "risk": "translated wiki page; still not a 469 plaintext key",
        "gloss_allowed": 0,
    },
    {
        "source_id": "HONEMINAS_FORMULA",
        "source_url": "https://www.tibiawiki.com.br/Honeminas_Formula",
        "source_label": "Honeminas Formula",
        "source_kind": "BOOK_OR_LORE_FORMULA",
        "in_game_anchor": "Demona, magical web formula",
        "finding": "Tibia lore includes explicit formula notation linked to magic and creation structure.",
        "translation_use": "parallel formula grammar for ritual/math language",
        "risk": "not Bonelord-specific unless bridged by in-game evidence",
        "gloss_allowed": 0,
    },
    {
        "source_id": "TIBIAQA_AVAR_TAR_POEM",
        "source_url": "https://www.tibiaqa.com/20625/which-npcs-are-speaking-bonelord-469-language",
        "source_label": "TibiaQA Avar Tar answer",
        "source_kind": "FANSITE_QA",
        "in_game_anchor": "Avar Tar response to Bonelord language keyword",
        "finding": "Avar Tar gives a long numeric poem plus an English framing sentence.",
        "translation_use": "out-of-book style comparator and poem/register candidate",
        "risk": "fansite answer; not Hellgate corpus; not exact meaning",
        "gloss_allowed": 0,
    },
    {
        "source_id": "TIBIAQA_MATH_HINTS",
        "source_url": "https://www.tibiaqa.com/9729/how-to-speak-bonelord-language-469",
        "source_label": "TibiaQA 469 math discussion",
        "source_kind": "FANSITE_QA",
        "in_game_anchor": "community summary of cryptography, eyes/binary, Hellgate skull matrix",
        "finding": "Useful only as a checklist of math/cryptography hypotheses already circulating.",
        "translation_use": "anti-repeat backlog and weak hypothesis catalog",
        "risk": "community speculation",
        "gloss_allowed": 0,
    },
]


ROUTES = [
    {
        "route_id": "R1_INGAME_CONTEXT_CORPUS",
        "priority": 1,
        "route_name": "In-game context corpus",
        "hypothesis": "Human readings should start from the entire in-game context around a 469 item, not from a free-form English decoder.",
        "anchor_rule": "Every candidate must cite book/NPC/quest/location provenance before prose is drafted.",
        "next_probe": "Import/verify all Bonelord, Hellgate, Paradox, Mathemagics, Avar Tar, Wyrdin, Knightmare, Chayenne, and Great Calculator texts as source rows.",
        "acceptance_gate": "A shadow reading is allowed only with explicit source anchors and a contradiction note.",
        "rejection_gate": "Reject if prose can be produced without mentioning its in-game anchor.",
        "output_layer": "SHADOW_HUMAN_READING_ONLY",
    },
    {
        "route_id": "R2_NPC_PHRASE_STYLE_COMPARATOR",
        "priority": 2,
        "route_name": "NPC phrase style comparator",
        "hypothesis": "Avar Tar, Chayenne, Knightmare, and book strings may share register/shape even when they do not share direct plaintext.",
        "anchor_rule": "Use exact numeric phrases as comparator corpus; never coerce them into book plaintext.",
        "next_probe": "Tokenize NPC/interview phrases with row0 rules and compare motif/register against row0_variant_book_tokens.",
        "acceptance_gate": "Accept only if a repeated shape predicts an unseen book/register or reduces contradictions.",
        "rejection_gate": "Reject if a match is substring-only, source-only, or depends on post-hoc wording.",
        "output_layer": "STYLE_OR_REGISTER_SHADOW",
    },
    {
        "route_id": "R3_MATHEMAGIC_OPERATOR_GRID",
        "priority": 3,
        "route_name": "Mathemagic operator grid",
        "hypothesis": "Mathemagics should be tested as operators/selectors over books, slots, and variants, not as a direct dictionary.",
        "anchor_rule": "Paradox/Mintwallin 1+1, keys 1/13/49/94, Honeminas formula, and Hellgate matrix are operator constraints.",
        "next_probe": "Build a grid for +49 mod70, 94->24, delta13, 4x4 matrix, zero/one inversion, and formula composition against alive frontier books.",
        "acceptance_gate": "Accept if an operator predicts a functional role on held-out books better than current baseline.",
        "rejection_gate": "Reject if it only creates plausible prose or improves no held-out classification.",
        "output_layer": "OPERATOR_SHADOW",
    },
    {
        "route_id": "R4_NAME_AS_FORMULA",
        "priority": 4,
        "route_name": "Names as formulas",
        "hypothesis": "Bonelord/beholder/race names may be dynamic formulas for a viewer, so fixed-word searches for Bonelord can mislead.",
        "anchor_rule": "Use 486486, 3478, 4378, 469, 1, and 0 as numeric lore constraints, not lexical translations.",
        "next_probe": "Audit all proper-name hypotheses and split fixed names from formula-name behavior.",
        "acceptance_gate": "Accept only if a name hypothesis explains multiple named anchors without forcing fixed English.",
        "rejection_gate": "Reject if it maps one number to one modern name without handling subjective/formula wording.",
        "output_layer": "LORE_CONSTRAINT_SHADOW",
    },
    {
        "route_id": "R5_PLAUSIBLE_PROSE_SHADOW",
        "priority": 5,
        "route_name": "Plausible prose shadow",
        "hypothesis": "We can draft human-readable paraphrases as research artifacts if they are marked non-canonical and tied to functional tags.",
        "anchor_rule": "Each draft must list functional tags, in-game context, confidence, and contradiction risks.",
        "next_probe": "Create one-page shadow readings for 6-10 frontier books: theme, likely speech act, possible prose, blocked claims.",
        "acceptance_gate": "A draft is useful if it creates a falsifiable next question or source search.",
        "rejection_gate": "Reject if it reads like final translation or hides unknown slots.",
        "output_layer": "PLAUSIBLE_HUMAN_PARAPHRASE_SHADOW",
    },
    {
        "route_id": "R6_LOCATION_ROLE_ALIGNMENT",
        "priority": 6,
        "route_name": "Location and shelf role alignment",
        "hypothesis": "Physical placement and cross-library duplicates may encode role/context that helps human interpretation.",
        "anchor_rule": "Only use shelf/library/location if verified from in-game or reliable library pages.",
        "next_probe": "Map Hellgate, Isle of the Kings shelf 21/39, duplicated books, and external library copies to functional clusters.",
        "acceptance_gate": "Accept if a location grouping predicts a tag cluster or resolves a book-family ambiguity.",
        "rejection_gate": "Reject if location is guessed or imported from unverified screenshots only.",
        "output_layer": "CONTEXT_LAYOUT_SHADOW",
    },
    {
        "route_id": "R7_GREAT_CALCULATOR_LINEAGE",
        "priority": 7,
        "route_name": "Great Calculator lineage",
        "hypothesis": "The 469 library may be a gathered/compiled corpus, explaining formula families, repeats, and non-linear order.",
        "anchor_rule": "Tie this only to the in-game book mentioning the Great Calculator and Bonelord language gathering.",
        "next_probe": "Compare contigs/repeats against anthology/compilation behavior instead of single continuous prose.",
        "acceptance_gate": "Accept if it explains contig breaks or repeated formula clusters better than linear text assumptions.",
        "rejection_gate": "Reject if it becomes a generic lore story with no row0/contig effect.",
        "output_layer": "CORPUS_STRUCTURE_SHADOW",
    },
    {
        "route_id": "R8_MINOTAUR_MAGE_TRUTH_BRIDGE",
        "priority": 8,
        "route_name": "Minotaur mage truth bridge",
        "hypothesis": "The Wrinkled Bonelord's minotaur-mage remark may bridge Bonelord math with Mintwallin/Paradox mathemagics.",
        "anchor_rule": "Bridge requires both Hellgate dialogue and Mintwallin/Paradox evidence.",
        "next_probe": "Search/import Minotaur Mage, Mintwallin prisoner, Wyrdin, and Noodles Academy lines before making any semantic claim.",
        "acceptance_gate": "Accept if the bridge predicts a specific operator or source family.",
        "rejection_gate": "Reject if it only says minotaurs are relevant without a mechanical test.",
        "output_layer": "BRIDGE_HYPOTHESIS_SHADOW",
    },
    {
        "route_id": "R9_ZERO_ONE_TABOO_INVERSION",
        "priority": 9,
        "route_name": "Zero/one taboo and inversion",
        "hypothesis": "Tibia=1 and 0 taboo may encode a world/null/inversion boundary important for segmentation and not just vocabulary.",
        "anchor_rule": "Use only explicit Wrinkled Bonelord dialogue and row0 leading-zero/code-symbol evidence.",
        "next_probe": "Contrast omitted leading-zero codes, star boundaries, 0/1-like markers, and formula tails.",
        "acceptance_gate": "Accept if zero/one behavior predicts boundary placement or taboo/formula contexts.",
        "rejection_gate": "Reject any simple 0=bad/1=Tibia gloss unless it predicts book-internal behavior.",
        "output_layer": "BOUNDARY_OPERATOR_SHADOW",
    },
    {
        "route_id": "R10_EXTERNAL_EXACT_GLOSS_ROUTE",
        "priority": 10,
        "route_name": "Exact external gloss route",
        "hypothesis": "External sources remain useful only when they attest exact sequence plus meaning/provenance.",
        "anchor_rule": "Official/in-game sources outrank fansites; fansites can suggest searches but not promote translations.",
        "next_probe": "Continue exact searches for full numeric phrases and source-author statements, especially archived official forum/interviews.",
        "acceptance_gate": "Accept exact phrase plus explicit meaning and provenance.",
        "rejection_gate": "Reject paraphrase, fan key, or claimed solved method without exact attestation.",
        "output_layer": "EXTERNAL_ATTESTATION_GATE",
    },
]


def now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def ensure_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS human_translation_route_v1_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            decision TEXT NOT NULL,
            source_count INTEGER NOT NULL,
            route_count INTEGER NOT NULL,
            frontier_book_count INTEGER NOT NULL,
            accepted_canonical_gloss_count INTEGER NOT NULL,
            payload_json TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS human_translation_route_v1_sources (
            run_id INTEGER NOT NULL,
            source_id TEXT NOT NULL,
            source_url TEXT NOT NULL,
            source_label TEXT NOT NULL,
            source_kind TEXT NOT NULL,
            in_game_anchor TEXT NOT NULL,
            finding TEXT NOT NULL,
            translation_use TEXT NOT NULL,
            risk TEXT NOT NULL,
            gloss_allowed INTEGER NOT NULL,
            PRIMARY KEY (run_id, source_id)
        );

        CREATE TABLE IF NOT EXISTS human_translation_route_v1_routes (
            run_id INTEGER NOT NULL,
            route_id TEXT NOT NULL,
            priority INTEGER NOT NULL,
            route_name TEXT NOT NULL,
            hypothesis TEXT NOT NULL,
            anchor_rule TEXT NOT NULL,
            next_probe TEXT NOT NULL,
            acceptance_gate TEXT NOT NULL,
            rejection_gate TEXT NOT NULL,
            output_layer TEXT NOT NULL,
            PRIMARY KEY (run_id, route_id)
        );

        CREATE TABLE IF NOT EXISTS human_translation_route_v1_frontier_books (
            run_id INTEGER NOT NULL,
            rank INTEGER NOT NULL,
            bookid TEXT NOT NULL,
            source_frontier_status TEXT NOT NULL,
            anchor_bookid TEXT NOT NULL,
            anchor_role TEXT NOT NULL,
            math_relation_status TEXT NOT NULL,
            human_route_focus TEXT NOT NULL,
            next_action TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            PRIMARY KEY (run_id, bookid)
        );
        """
    )


def current_v19_by_book(conn: sqlite3.Connection) -> dict[str, dict[str, object]]:
    rows = conn.execute(
        """
        SELECT bookid, functional_tags_json, honest_text, evidence_json
        FROM final_honest_reading_v19_books
        WHERE run_id=(SELECT max(run_id) FROM final_honest_reading_v19_books)
        """
    ).fetchall()
    return {
        str(row["bookid"]): {
            "functional_tags_json": row["functional_tags_json"],
            "honest_text": row["honest_text"],
            "evidence_json": row["evidence_json"],
        }
        for row in rows
    }


def frontier_books(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return conn.execute(
        """
        SELECT rank, bookid, best_anchor_bookid, best_anchor_role,
               math_relation_status, post_math_status, next_action, evidence_json
        FROM post_mathemagic_frontier_selection_v1_items
        WHERE run_id=(SELECT max(run_id) FROM post_mathemagic_frontier_selection_v1_items)
        ORDER BY rank
        LIMIT 20
        """
    ).fetchall()


def focus_for(status: str) -> str:
    if status == "ALIVE_NON_C86_FRONTIER":
        return "R5 shadow prose candidate after R1/R3 anchor checks"
    if status.startswith("HOLD"):
        return "hold until non-circular in-game evidence exists"
    if status.startswith("DEMOTE"):
        return "audit/control only; do not draft prose first"
    return "review before any human paraphrase"


def main() -> None:
    conn = sqlite3.connect(DB, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=30000")
    ensure_tables(conn)

    v19 = current_v19_by_book(conn)
    frontier = frontier_books(conn)
    eligible_frontier = [row for row in frontier if row["post_math_status"] == "ALIVE_NON_C86_FRONTIER"]

    payload = {
        "canonical_policy": "no canonical prose gloss is promoted by this route registry",
        "human_layer": "plausible human readings are allowed only as shadow artifacts with anchors and risks",
        "eligible_frontier_books": [row["bookid"] for row in eligible_frontier],
        "source_priority": ["in-game book/NPC/quest", "official source", "promoted fansite transcript", "community speculation"],
    }
    cur = conn.execute(
        """
        INSERT INTO human_translation_route_v1_runs
        (created_at, decision, source_count, route_count, frontier_book_count,
         accepted_canonical_gloss_count, payload_json)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            now(),
            "HUMAN_TRANSLATION_ROUTES_READY_SHADOW_ONLY",
            len(SOURCES),
            len(ROUTES),
            len(eligible_frontier),
            0,
            json.dumps(payload, ensure_ascii=False, sort_keys=True),
        ),
    )
    run_id = int(cur.lastrowid)

    for source in SOURCES:
        conn.execute(
            """
            INSERT INTO human_translation_route_v1_sources
            (run_id, source_id, source_url, source_label, source_kind, in_game_anchor,
             finding, translation_use, risk, gloss_allowed)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                source["source_id"],
                source["source_url"],
                source["source_label"],
                source["source_kind"],
                source["in_game_anchor"],
                source["finding"],
                source["translation_use"],
                source["risk"],
                source["gloss_allowed"],
            ),
        )

    for route in ROUTES:
        conn.execute(
            """
            INSERT INTO human_translation_route_v1_routes
            (run_id, route_id, priority, route_name, hypothesis, anchor_rule,
             next_probe, acceptance_gate, rejection_gate, output_layer)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                route["route_id"],
                route["priority"],
                route["route_name"],
                route["hypothesis"],
                route["anchor_rule"],
                route["next_probe"],
                route["acceptance_gate"],
                route["rejection_gate"],
                route["output_layer"],
            ),
        )

    for row in frontier:
        book_state = v19.get(str(row["bookid"]), {})
        evidence = {
            "post_mathemagic": json.loads(row["evidence_json"]),
            "final_honest_v19": {
                "functional_tags_json": book_state.get("functional_tags_json"),
                "honest_text": book_state.get("honest_text"),
            },
        }
        conn.execute(
            """
            INSERT INTO human_translation_route_v1_frontier_books
            (run_id, rank, bookid, source_frontier_status, anchor_bookid, anchor_role,
             math_relation_status, human_route_focus, next_action, evidence_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                row["rank"],
                row["bookid"],
                row["post_math_status"],
                row["best_anchor_bookid"],
                row["best_anchor_role"],
                row["math_relation_status"],
                focus_for(row["post_math_status"]),
                row["next_action"],
                json.dumps(evidence, ensure_ascii=False, sort_keys=True),
            ),
        )

    conn.commit()
    print(
        json.dumps(
            {
                "run_id": run_id,
                "decision": "HUMAN_TRANSLATION_ROUTES_READY_SHADOW_ONLY",
                "source_count": len(SOURCES),
                "route_count": len(ROUTES),
                "eligible_frontier_books": [row["bookid"] for row in eligible_frontier],
                "accepted_canonical_gloss_count": 0,
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
