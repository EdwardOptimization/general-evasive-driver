# m1273-paper-route-four-wheel-source-corpus-export Research Review

## Summary

- Generated at UTC: 20260528T124958Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: four_wheel_source_corpus_export_pass_route_to_result_audit
- Decision reason: M1273 exports 108 accepted rows plus 19 near-boundary 32 high-regret and 63 family-balanced rows with halfshaft logged as inactive

## Hypothesis

A stratified export can preserve M1271 accepted source rows while separating boundary-useful rows, high-regret rows, family-balanced rows, and inactive fault families.

## Lineage

- parent_checkpoint: not_applicable_no_checkpoint
- parent_dataset: docs/m1272-paper-route-four-wheel-source-viability-calibration-result-audit.md, runs/m1271_four_wheel_source_viability_calibration_smoke/accepted_separable_pairs.csv, runs/m1271_four_wheel_source_viability_calibration_smoke/matched_capability_pairs.csv
- parent_config: experiments/manifests/m1272-paper-route-four-wheel-source-viability-calibration-result-audit.json
- parent_objective: export stratified four-wheel source corpus from M1271 accepted rows
- derived_from: m1272-paper-route-four-wheel-source-viability-calibration-result-audit
- blocked_by: M1272 admits source-corpus export before actor/Gym integration
- supersedes: direct use of all 108 M1271 accepted rows as an unfiltered training/evaluation corpus
- invalidates: None

## Success Criteria

- runs/m1273_four_wheel_source_corpus_export/summary.json exists
- all_accepted_source_rows.csv exists
- near_boundary_source_rows.csv exists
- high_regret_source_rows.csv exists
- family_balanced_source_rows.csv exists
- inactive_fault_families.csv exists
- exported accepted row count equals 108
- no training, PPO, promotion, private holdout, threshold relaxation, or actor-input expansion occurs

## Failure Criteria

- run artifacts are missing
- accepted row count does not match M1271
- source subsets are missing
- export changes accepted-source semantics
- training, PPO, private holdout, promotion, threshold relaxation, or actor-input expansion occurs

## Evidence Gates

- M1273 must preserve actor input contract
- M1273 must not train controllers
- M1273 must not run PPO
- M1273 must not use private holdout
- M1273 must not promote
- M1273 must export all accepted rows and stratified boundary/high-regret/family-balanced subsets
- M1273 must log inactive fault families separately

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not use private holdout
- do not promote
- do not add per-wheel/fault labels to actor inputs
- do not lower accepted-source thresholds
- do not count horizon-only rows as success
- do not treat source-corpus rows as driver performance
- do not claim high-fidelity validation from the compact pilot

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1273-paper-route-four-wheel-source-corpus-export
- type: infrastructure
- checkpoint: runs/m1273_four_wheel_source_corpus_export/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: four_wheel_source_corpus_export_pass_route_to_result_audit
- reason: M1273 exports 108 accepted rows plus 19 near-boundary 32 high-regret and 63 family-balanced rows with halfshaft logged as inactive

## Next Blocker

m1274-paper-route-four-wheel-source-corpus-export-result-audit
