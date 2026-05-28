# m1315-paper-route-source-history-corpus-expansion-plan Research Review

## Summary

- Generated at UTC: 20260528T163020Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: source_history_corpus_expansion_plan_gap_reported_route_to_source_generator_update_design
- Decision reason: M1315 reports current source artifacts provide only 108 pairs 216 groups and 3 families so source generator updates are required

## Hypothesis

The existing source artifacts can support a deterministic expanded source-history corpus plan with materially broader fault-family and fold coverage before another objective run.

## Lineage

- parent_checkpoint: not_applicable
- parent_dataset: docs/m1314-paper-route-source-history-corpus-expansion-design.md, runs/m1273_four_wheel_source_corpus_export/summary.json, runs/m1280_four_wheel_source_response_history_materialization/summary.json
- parent_config: experiments/manifests/m1314-paper-route-source-history-corpus-expansion-design.json
- parent_objective: build no-policy source-history corpus expansion plan
- derived_from: m1314-paper-route-source-history-corpus-expansion-design
- blocked_by: M1314 admits no-policy expansion plan builder
- supersedes: further objective tuning on the current 38-pair source-history corpus
- invalidates: None

## Success Criteria

- runs/m1315_source_history_corpus_expansion_plan/summary.json exists
- focused tests pass
- planned_source_pairs >= 240 or unsupported coverage gaps are explicitly reported
- planned_pair_probe_groups >= 480 or unsupported coverage gaps are explicitly reported
- source_fault_family_count >= 6 or unsupported coverage gaps are explicitly reported
- pair_disjoint is true
- all_folds_nonempty is true
- pair_specific_weight_used is false
- no training, PPO, promotion, private holdout, threshold relaxation, or actor-input expansion occurs

## Failure Criteria

- run artifacts are missing
- focused tests fail
- coverage gaps are hidden
- pair-disjoint folds are violated
- pair-specific weights are used
- training, PPO, private holdout, promotion, threshold relaxation, or actor-input expansion occurs

## Evidence Gates

- M1315 must not train
- M1315 must not run PPO
- M1315 must not use private holdout
- M1315 must not promote
- M1315 must preserve actor input contract
- M1315 must output a deterministic expansion plan
- M1315 must report coverage gaps instead of fabricating unsupported families

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not promote
- do not use private holdout
- do not add actor inputs
- do not fabricate unsupported source families
- do not use pair-specific weights
- do not overclaim self-identification

## Failure Taxonomy

- scenario_sampling_failure

## Scoreboard

- milestone: m1315-paper-route-source-history-corpus-expansion-plan
- type: infrastructure
- checkpoint: runs/m1315_source_history_corpus_expansion_plan/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: source_history_corpus_expansion_plan_gap_reported_route_to_source_generator_update_design
- reason: M1315 reports current source artifacts provide only 108 pairs 216 groups and 3 families so source generator updates are required

## Next Blocker

m1316-paper-route-source-history-source-generator-update-design
