# m1712-paper-route-controller-family-calibrated-scale-up-preflight Research Review

## Summary

- Generated at UTC: 20260530T014005Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: controller_family_calibrated_scale_up_preflight_pass
- Decision reason: M1712 materializes 18 base specs 72 scale-up calibration specs and 864 matrix cells with zero contract violations and no rollout

## Hypothesis

The M1711 source-expanded calibrated scale-up subset can be materialized as a no-rollout 864-cell matrix with clean contract checks.

## Lineage

- parent_checkpoint: not_applicable_preflight
- parent_dataset: docs/m1711-paper-route-controller-family-calibrated-scale-up-design.md, runs/m1702_controller_family_task_quality_calibration_preflight/calibration_specs.json, runs/m1702_controller_family_task_quality_calibration_preflight/calibration_matrix.csv, runs/m1705_controller_family_bounded_calibration_smoke_preflight/selected_base_specs.csv
- parent_config: experiments/manifests/m1711-paper-route-controller-family-calibrated-scale-up-design.json
- parent_objective: materialize source-expanded no-rollout calibrated scale-up subset
- derived_from: m1711-paper-route-controller-family-calibrated-scale-up-design
- blocked_by: need no-rollout scale-up subset before audit or execution design
- supersedes: direct execution of M1708 best variant only, direct calibrated scale-up execution after M1711
- invalidates: None

## Success Criteria

- runs/m1712_controller_family_calibrated_scale_up_preflight/summary.json exists
- scale_up_matrix.csv exists and contains 864 rows
- selected_base_specs.csv contains 18 rows with T4=9 and T5=9
- scale_up_calibration_specs.csv contains 72 rows
- all 12 profiles appear for each selected calibration spec
- contract_violation_count == 0
- environment_rollout_started == false
- training replay PPO promotion private holdout actor-input changes and level3 claims remain blocked

## Failure Criteria

- selected subset does not match the M1711 scale
- required task family variant or profile coverage is missing
- any env variant violates P0 contract
- environment rollout training replay PPO private holdout promotion or actor-input changes occur
- preflight claims controller-family ranking

## Evidence Gates

- M1712 must materialize a no-rollout 864-cell calibrated scale-up subset
- M1712 must select 18 base specs with T4=9 and T5=9
- M1712 must preserve the four M1711 calibration variants for each base spec
- M1712 must preserve all 12 controller-family profiles per calibration spec
- M1712 must preserve P0 no-wheel no-oracle actor contract for every env variant
- M1712 must not execute rollout train replay PPO promote use private holdout or change actor inputs

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

- milestone: m1712-paper-route-controller-family-calibrated-scale-up-preflight
- type: infrastructure
- checkpoint: runs/m1712_controller_family_calibrated_scale_up_preflight/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: controller_family_calibrated_scale_up_preflight_pass
- reason: M1712 materializes 18 base specs 72 scale-up calibration specs and 864 matrix cells with zero contract violations and no rollout

## Next Blocker

m1713-paper-route-controller-family-calibrated-scale-up-preflight-result-audit
