# m1320-paper-route-inactive-source-family-repair-smoke Research Review

## Summary

- Generated at UTC: 20260528T170520Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: inactive_source_family_repair_smoke_strong_partial_route_to_result_audit
- Decision reason: M1320 activates steering and load families improves halfshaft and leaves only global friction inactive

## Hypothesis

Family-specific source_repair_v1 profiles can activate at least one previously inactive or undercovered family without actor-input expansion or source-threshold relaxation.

## Lineage

- parent_checkpoint: not_applicable
- parent_dataset: docs/m1319-paper-route-inactive-source-family-repair-design.md, runs/m1317_source_generator_update_smoke/summary.json, runs/m1317_source_generator_update_smoke/inactive_fault_families.csv
- parent_config: experiments/manifests/m1319-paper-route-inactive-source-family-repair-design.json
- parent_objective: implement and smoke-test family-specific no-policy source repair profiles
- derived_from: m1319-paper-route-inactive-source-family-repair-design
- blocked_by: M1319 admits source_repair_v1 no-policy repair smoke
- supersedes: corpus export from the M1317 partial active-family subset
- invalidates: None

## Success Criteria

- focused tests pass
- runs/m1320_inactive_source_family_repair_smoke/summary.json exists
- accepted_separable_pairs >= 160 or explicit family blockers are reported
- accepted_fault_family_pairs >= 6 or explicit family blockers are reported
- at least one previously inactive family becomes active or all inactive families are classified as simulator/search-blocked
- halfshaft accepted rows > 4 or halfshaft undercoverage blocker is reported
- inactive families are exported separately
- strict source acceptance thresholds are preserved
- no training, PPO, promotion, private holdout, threshold relaxation, or actor-input expansion occurs

## Failure Criteria

- focused tests fail
- run artifacts are missing
- source thresholds are relaxed
- inactive families are hidden
- training, PPO, private holdout, promotion, threshold relaxation, or actor-input expansion occurs

## Evidence Gates

- M1320 must not train
- M1320 must not run PPO
- M1320 must not use private holdout
- M1320 must not promote
- M1320 must preserve actor input contract
- M1320 must keep strict source acceptance thresholds
- M1320 must export active and inactive family diagnostics

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not promote
- do not use private holdout
- do not add actor inputs
- do not relax source thresholds
- do not hide inactive families
- do not overclaim self-identification

## Failure Taxonomy

- scenario_sampling_failure

## Scoreboard

- milestone: m1320-paper-route-inactive-source-family-repair-smoke
- type: infrastructure
- checkpoint: runs/m1320_inactive_source_family_repair_smoke/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: inactive_source_family_repair_smoke_strong_partial_route_to_result_audit
- reason: M1320 activates steering and load families improves halfshaft and leaves only global friction inactive

## Next Blocker

m1321-paper-route-source-repair-result-audit
