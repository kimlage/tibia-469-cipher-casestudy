# Lexicon Confidence Report

Verdict: `confidence_labels_ready`. Translation delta: `NONE`.

The comparanda front uses confidence labels rather than a flat vocabulary. This
is required because Tibia language material mixes game-function evidence,
community inference, uncertain glosses, and fan claims.

Promotion policy:

| Label family | 469 semantic promotion |
|---|---|
| `official_gt` | allowed in principle, absent here |
| `in_game_functional` | no; benchmark only |
| `reciprocal_dialogue_confirmed` | no; partial-lexicon control only |
| `context_deduced` / `probable` | no; uncertainty calibration only |
| `uncertain` / `fan_claim` | no; rejected or low-confidence control |
| `community_reconstruction` | no; validation-only shadow candidate |

The seed TSV files are deliberately small. They preserve benchmark anchors and
confidence classes without pretending to be complete corpora.
