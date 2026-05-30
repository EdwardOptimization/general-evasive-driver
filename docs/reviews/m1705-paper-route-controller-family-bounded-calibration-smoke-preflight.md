# m1705-paper-route-controller-family-bounded-calibration-smoke-preflight Research Review

## Summary

- Generated at UTC: 20260530T010906Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: controller_family_bounded_calibration_smoke_preflight_pass
- Decision reason: M1705 materializes the bounded calibration smoke subset with 6 base specs 72 calibration specs 864 cells zero contract violations and no rollout

## Hypothesis

The M1704 bounded calibration smoke subset can be materialized as a no-rollout 864-cell matrix with clean contract checks.

## Lineage

- parent_checkpoint: not_applicable_preflight
- parent_dataset: docs/m1704-paper-route-controller-family-bounded-calibration-smoke-design.md, runs/m1702_controller_family_task_quality_calibration_preflight/calibration_matrix.csv
- parent_config: experiments/manifests/m1704-paper-route-controller-family-bounded-calibration-smoke-design.json
- parent_objective: materialize no-rollout bounded calibration smoke subset
- derived_from: m1704-paper-route-controller-family-bounded-calibration-smoke-design
- blocked_by: need bounded smoke subset preflight before any execution
- supersedes: direct execution of the full M1702 10368-cell matrix
- invalidates: None

## Success Criteria

- runs/m1705_controller_family_bounded_calibration_smoke_preflight/summary.json exists
- bounded_smoke_matrix.csv exists and contains 864 rows
- selected_base_specs.csv contains 6 rows with 3 T4 and 3 T5 specs
- bounded_calibration_specs.csv contains 72 rows
- all 12 profiles appear for each selected calibration spec
- contract_violation_count == 0
- environment_rollout_started == false
- training replay PPO promotion private holdout actor-input changes and level3 claims remain blocked

## Failure Criteria

- selected subset does not match the M1704 scale
- required task family calibration axis or profile coverage is missing
- any env variant violates P0 contract
- environment rollout training replay PPO private holdout promotion or actor-input changes occur
- preflight claims controller-family ranking

## Evidence Gates

- M1705 must materialize a no-rollout 864-cell bounded smoke subset
- M1705 must select 6 source-diverse base specs with 3 T4 and 3 T5 specs
- M1705 must preserve all 12 calibration variants per selected base spec
- M1705 must preserve all 12 controller-family profiles per calibration spec
- M1705 must preserve P0 no-wheel no-oracle actor contract for every env variant
- M1705 must not execute rollout train replay PPO promote use private holdout or change actor inputs
- M1705 must not claim controller-family ranking, paper-level evidence, private-holdout evidence, or level3 self-ID

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run environment rollout
- do not train
- do not run replay
- do not run PPO
- do not promote a checkpoint
- do not use private holdout
- do not change actor inputs
- do not tune profiles
- do not claim controller-family ranking
- do not claim paper-level evidence
- do not claim level3 self-identification

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1705-paper-route-controller-family-bounded-calibration-smoke-preflight
- type: infrastructure
- checkpoint: runs/m1705_controller_family_bounded_calibration_smoke_preflight/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: controller_family_bounded_calibration_smoke_preflight_pass
- reason: M1705 materializes the bounded calibration smoke subset with 6 base specs 72 calibration specs 864 cells zero contract violations and no rollout

## Next Blocker

m1706-paper-route-controller-family-bounded-calibration-smoke-preflight-result-audit
