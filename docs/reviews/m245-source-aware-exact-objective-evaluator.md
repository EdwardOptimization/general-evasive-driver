# m245-source-aware-exact-objective-evaluator Research Review

## Summary

- Generated at UTC: 20260522T142301Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: admit_source_balanced_outcome_loss_design
- Decision reason: M245 adds exact source matching/reporting for outcome_intervention_eval and reproduces M244 source deltas exactly; no PPO and no driver promotion

## Hypothesis

Source-aware exact objective reporting should make the M244 audit durable and prevent future PPO gates from hiding protected-key regressions behind M223 improvements.

## Lineage

- parent_checkpoint: runs/m239_m224_to_m237_interpolation/checkpoints/alpha_0_5.pt, runs/m243_m239_to_raw_interpolation/checkpoints/alpha_0_1.pt, runs/m243_m239_to_raw_interpolation/checkpoints/alpha_0_25.pt, runs/m243_m239_to_raw_interpolation/checkpoints/alpha_0_5.pt, runs/m243_m239_to_raw_interpolation/checkpoints/alpha_0_75.pt, runs/m243_m239_to_raw_interpolation/checkpoints/alpha_1.pt
- parent_dataset: runs/m232_combined_m223_m231_snippet_anchor/outcome_intervention_snippets.npz, runs/m223_m219_boundary_outcome_corpus_seed10060/boundary_outcome_corpus.npz, runs/m231_protected_key_snippet_surface/protected_key_snippets.npz
- parent_config: src/autodrift/outcome_intervention_eval.py
- parent_objective: source-aware exact M232 objective reporting, lexicographic protected-key non-regression gate support
- derived_from: m244-m243-protected-key-objective-conflict-audit
- blocked_by: m244-m243-protected-key-objective-conflict-audit
- supersedes: None
- invalidates: None

## Success Criteria

- add evaluator support for named source NPZ files in exact mode
- emit per-row and per-source exact objective artifacts
- verify source matching uses the same observation hidden and action rows as the combined corpus
- reproduce the M244 M223/protected-key decomposition from the evaluator
- add focused tests for source matching and clamped-denominator source reporting

## Failure Criteria

- source reporting disagrees with the aggregate exact M232 loss
- source matching silently ignores unmatched rows
- tests fail
- run PPO or modify actor inputs

## Evidence Gates

- source-aware exact evaluator tests
- M244 source decomposition reproduction
- research validator

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run PPO in M245
- do not change actor inputs
- do not normalize source deltas with a formula different from weighted_mean
- do not promote a driver checkpoint

## Failure Taxonomy

- none

## Scoreboard

- milestone: m245-source-aware-exact-objective-evaluator
- type: infrastructure
- checkpoint: None
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: admit_source_balanced_outcome_loss_design
- reason: M245 adds exact source matching/reporting for outcome_intervention_eval and reproduces M244 source deltas exactly; no PPO and no driver promotion

## Next Blocker

Design source-balanced outcome-loss repair before more PPO.
