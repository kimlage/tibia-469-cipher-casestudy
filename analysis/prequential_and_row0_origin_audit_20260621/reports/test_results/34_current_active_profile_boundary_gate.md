# Current Active Profile Boundary Gate

Classification: `active_8177_profile_validated_recipe_discovery_blocked`
Translation delta: `NONE`

## Purpose

This gate consolidates the default/exception layer into the current
mechanical ledger. It distinguishes the active compression bound and
component-level holdout validation from the still-open recipe-discovery
problem caused by path-dependent copy-source state.

## Summary

- Active compression bound: `8177.317` bits.
- Copy-length default/exception formula: `8206.178` bits, gain `136.884`.
- Copy-source default/exception formula: `8177.317` bits, gain `28.862`.
- Learned component streams: `7157.317` bits (`87.526%`).
- Fixed recipe/declaration remainder: `1020.000` bits (`12.474%`).
- Active prefix frozen min gain: `62.103` bits.
- Active block frozen min gain: `50.361` bits.
- Active family frozen min gain: `6.269` bits.
- Active family frozen nonpositive failures: `0`.
- Default/exception-only family frozen nonpositive failures before full active profile: `2`.
- Recipe discovery proved: `False`.
- Required active reparse state: `(book_pos, previous_item, previous_copy_source, previous_copy_length)`.
- Old reparse state: `(book_pos, previous_item)`.
- Cutoff-10 state proxy: `302879952` versus old state count `28881`.
- Best state-free source default: `state_free_back_current_length`, `15.186` bits worse.

## Interpretation

`8177.317` bits is retained as the current active mechanical
compression bound. Unlike the default/exception-only validation, the
full active learned stream profile has positive frozen gain in every
tested prefix, block, and public-bookcase family holdout. That
strengthens component-level predictive validation, but it still does
not prove recipe discovery: the active recipe rows are extracted before
splitting, and exact active reparsing requires previous-copy source and
length state. The best state-free replacement is worse, so this boundary
remains a real blocker rather than a solved generator.

## Boundary

- No new compression bound is introduced by this gate.
- The current active bound is consolidated as `8177.317` bits.
- Recipe discovery remains unproved and path-state-bound.
- Row0 origin remains unchanged and exogenous.
- No plaintext, translation, semantic reading, or case reopening is introduced.
