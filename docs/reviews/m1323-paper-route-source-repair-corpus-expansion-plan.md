# m1323-paper-route-source-repair-corpus-expansion-plan Research Review

## Summary

- Generated at UTC: 20260528T171455Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: source_repair_corpus_expansion_plan_gap_reported_route_to_result_audit
- Decision reason: M1323 plans 216 source pairs and 7 families with good fold balance but remains below 240 target

## Hypothesis

The M1322 source repair corpus can support a materially broader source-history expansion plan while preserving the global-friction blocker and avoiding stale materialized-history matches.

## Lineage

- parent_checkpoint: not_applicable
- parent_dataset: docs/m1322-paper-route-source-repair-corpus-export.md, runs/m1322_source_repair_corpus_export/summary.json
- parent_config: experiments/manifests/m1322-paper-route-source-repair-corpus-export.json
- parent_objective: plan source-history corpus expansion using the M1322 source repair corpus
- derived_from: m1322-paper-route-source-repair-corpus-export
- blocked_by: M1322 exports a new seven-family source corpus candidate that needs fold planning
- supersedes: planning from the old M1273 source corpus
- invalidates: None

## Success Criteria

- runs/m1323_source_repair_corpus_expansion_plan/summary.json exists
- planned_source_pairs >= 216
- planned_pair_probe_groups >= 432
- source_fault_family_count >= 7
- pair_disjoint is true
- all_folds_nonempty is true
- materialized_source_pair_count == 0
- global friction is reported as missing or inactive
- no training, PPO, promotion, private holdout, threshold relaxation, or actor-input expansion occurs

## Failure Criteria

- run artifacts are missing
- stale materialized histories are counted
- global friction gap is hidden
- pair-disjoint folds are violated
- training, PPO, private holdout, promotion, threshold relaxation, or actor-input expansion occurs

## Evidence Gates

- M1323 must not train
- M1323 must not run PPO
- M1323 must not use private holdout
- M1323 must not promote
- M1323 must preserve actor input contract
- M1323 must use the M1322 source corpus
- M1323 must avoid false materialized-history matches from pair-id collision
- M1323 must report coverage gaps instead of fabricating global friction

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not promote
- do not use private holdout
- do not add actor inputs
- do not fabricate global friction coverage
- do not use stale M1280 materialized history by pair id
- do not overclaim self-identification

## Failure Taxonomy

- scenario_sampling_failure

## Scoreboard

- milestone: m1323-paper-route-source-repair-corpus-expansion-plan
- type: infrastructure
- checkpoint: runs/m1323_source_repair_corpus_expansion_plan/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: source_repair_corpus_expansion_plan_gap_reported_route_to_result_audit
- reason: M1323 plans 216 source pairs and 7 families with good fold balance but remains below 240 target

## Next Blocker

m1324-paper-route-source-repair-corpus-plan-result-audit
