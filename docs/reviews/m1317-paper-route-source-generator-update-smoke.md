# m1317-paper-route-source-generator-update-smoke Research Review

## Summary

- Generated at UTC: 20260528T164857Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: source_generator_update_smoke_partial_coverage_route_to_result_audit
- Decision reason: M1317 is source-positive with 128 accepted rows and 5 accepted families but 3 inactive families require audit

## Hypothesis

Selectable expanded fault, scenario, and action profiles can produce broader strict no-policy source coverage without actor-input expansion or threshold relaxation.

## Lineage

- parent_checkpoint: not_applicable
- parent_dataset: docs/m1316-paper-route-source-history-source-generator-update-design.md, runs/m1315_source_history_corpus_expansion_plan/summary.json, runs/m1315_source_history_corpus_expansion_plan/requires_source_generator_update.csv
- parent_config: experiments/manifests/m1316-paper-route-source-history-source-generator-update-design.json
- parent_objective: implement and smoke-test expanded no-policy source generator profiles
- derived_from: m1316-paper-route-source-history-source-generator-update-design
- blocked_by: M1316 admits selectable source generator profiles before corpus materialization
- supersedes: using the M1273/M1280 narrow source-history corpus for more objective tuning
- invalidates: None

## Success Criteria

- focused tests pass
- runs/m1317_source_generator_update_smoke/summary.json exists
- accepted_separable_pairs >= 160 or explicit coverage gaps are reported
- accepted_fault_family_pairs >= 5 or explicit family blockers are reported
- inactive families are exported separately
- strict source acceptance thresholds are preserved
- labels_enter_actor_input is false
- no training, PPO, promotion, private holdout, threshold relaxation, or actor-input expansion occurs

## Failure Criteria

- focused tests fail
- run artifacts are missing
- new families are relabeled without dynamics
- accepted thresholds are relaxed
- inactive families are hidden
- training, PPO, private holdout, promotion, threshold relaxation, or actor-input expansion occurs

## Evidence Gates

- M1317 must not train
- M1317 must not run PPO
- M1317 must not use private holdout
- M1317 must not promote
- M1317 must preserve actor input contract
- M1317 must keep strict source acceptance thresholds
- M1317 must export accepted and inactive family diagnostics
- M1317 must report coverage gaps rather than accepting fake labels

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not promote
- do not use private holdout
- do not add actor inputs
- do not relax source acceptance thresholds
- do not accept non-divergent families
- do not claim high-fidelity tire blowout or drivetrain validation
- do not overclaim self-identification

## Failure Taxonomy

- scenario_sampling_failure

## Scoreboard

- milestone: m1317-paper-route-source-generator-update-smoke
- type: infrastructure
- checkpoint: runs/m1317_source_generator_update_smoke/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: source_generator_update_smoke_partial_coverage_route_to_result_audit
- reason: M1317 is source-positive with 128 accepted rows and 5 accepted families but 3 inactive families require audit

## Next Blocker

m1318-paper-route-source-generator-update-result-audit
