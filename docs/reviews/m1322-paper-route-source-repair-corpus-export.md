# m1322-paper-route-source-repair-corpus-export Research Review

## Summary

- Generated at UTC: 20260528T171119Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: source_repair_corpus_export_pass_route_to_expansion_plan
- Decision reason: M1322 exports 216 accepted rows and keeps global friction blocker visible

## Hypothesis

The M1320 source repair run can be exported into stratified source-corpus artifacts while preserving accepted-family coverage and the global-friction inactive blocker.

## Lineage

- parent_checkpoint: not_applicable
- parent_dataset: docs/m1321-paper-route-source-repair-result-audit.md, runs/m1320_inactive_source_family_repair_smoke/summary.json, runs/m1320_inactive_source_family_repair_smoke/accepted_separable_pairs.csv, runs/m1320_inactive_source_family_repair_smoke/inactive_fault_families.csv
- parent_config: experiments/manifests/m1321-paper-route-source-repair-result-audit.json
- parent_objective: export the M1320 seven-family source corpus candidate with global-friction blocker retained
- derived_from: m1321-paper-route-source-repair-result-audit
- blocked_by: M1321 admits updated source corpus export before source-history materialization
- supersedes: using M1273 narrow source corpus for the next source-history expansion
- invalidates: None

## Success Criteria

- focused export tests pass
- runs/m1322_source_repair_corpus_export/summary.json exists
- exported_accepted_rows == 216
- accepted family count is 7
- inactive_fault_families includes global_friction_step->global_friction_step
- all accepted, near-boundary, high-regret, family-balanced, and inactive-family CSVs exist
- no training, PPO, promotion, private holdout, threshold relaxation, or actor-input expansion occurs

## Failure Criteria

- focused export tests fail
- export artifacts are missing
- accepted rows are dropped unexpectedly
- global friction blocker is hidden
- training, PPO, private holdout, promotion, threshold relaxation, or actor-input expansion occurs

## Evidence Gates

- M1322 must not train
- M1322 must not run PPO
- M1322 must not use private holdout
- M1322 must not promote
- M1322 must preserve actor input contract
- M1322 must export all accepted near-boundary high-regret family-balanced and inactive-family rows
- M1322 must keep global friction blocker visible

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not promote
- do not use private holdout
- do not add actor inputs
- do not relax source thresholds
- do not hide global friction inactivity
- do not overclaim self-identification

## Failure Taxonomy

- scenario_sampling_failure

## Scoreboard

- milestone: m1322-paper-route-source-repair-corpus-export
- type: infrastructure
- checkpoint: runs/m1322_source_repair_corpus_export/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: source_repair_corpus_export_pass_route_to_expansion_plan
- reason: M1322 exports 216 accepted rows and keeps global friction blocker visible

## Next Blocker

m1323-paper-route-source-repair-corpus-expansion-plan
