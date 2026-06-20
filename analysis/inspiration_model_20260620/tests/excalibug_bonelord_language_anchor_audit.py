from __future__ import annotations

from _common import blocked


def main() -> None:
    blocked(
        "excalibug_bonelord_language_anchor_audit",
        "Knightmare/Excalibug is a scoped keyword-gate clue, but no official Bonelord-language Excalibug prompt/answer pair or gloss was found in the current corpus.",
        classification="blocked_waiting_for_official_source",
    )


if __name__ == "__main__":
    main()
