# m1704-paper-route-controller-family-bounded-calibration-smoke-design Research Review

## Summary

- Generated at UTC: 20260530T010406Z
- Type: gate
- Gate tier: process
- Promotion decision: bounded_calibration_smoke_design_admit_no_rollout_subset_preflight
- Decision reason: M1704 designs a 6-base-spec 72-calibration-spec 864-cell bounded calibration smoke and routes to no-rollout subset preflight

## Hypothesis

A bounded diagnostic calibration smoke can be designed from M1702 to test whether calibration axes reduce off-track dominance without ranking controllers.

## Lineage

- parent_checkpoint: not_applicable_design_only
- parent_dataset: docs/m1703-paper-route-controller-family-task-quality-calibration-preflight-result-audit.md, runs/m1702_controller_family_task_quality_calibration_preflight/summary.json, runs/m1702_controller_family_task_quality_calibration_preflight/calibration_matrix.csv
- parent_config: experiments/manifests/m1703-paper-route-controller-family-task-quality-calibration-preflight-result-audit.json
- parent_objective: design a bounded public calibration smoke before any measured execution
- derived_from: m1703-paper-route-controller-family-task-quality-calibration-preflight-result-audit
- blocked_by: need bounded smoke protocol before executing any calibration subset
- supersedes: direct full 10368-cell calibration rollout
- invalidates: None

## Success Criteria

- docs/m1704-paper-route-controller-family-bounded-calibration-smoke-design.md exists
- bounded smoke scale is explicitly smaller than the full 10368-cell matrix
- required controller controls are retained
- task-quality metrics and outcome buckets are specified
- rollout execution training replay PPO promotion private holdout actor-input changes and level3 claims remain blocked

## Failure Criteria

- design routes directly to full 10368-cell rollout
- design drops required controls
- design tunes profiles or ranks controllers
- design omits outcome-conditional task-quality metrics
- environment rollout training replay PPO private holdout promotion or actor-input changes occur

## Evidence Gates

- M1704 must design a bounded calibration smoke subset from M1702 without execution
- M1704 must keep L1, L2-current-tiled, L3-online, and L3-reset controls together
- M1704 must separate task-quality calibration from controller-family ranking
- M1704 must not execute rollout train replay PPO promote use private holdout or change actor inputs
- M1704 must not claim controller-family ranking, paper-level evidence, private-holdout evidence, or level3 self-ID

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

- milestone: m1704-paper-route-controller-family-bounded-calibration-smoke-design
- type: gate
- checkpoint: docs/m1704-paper-route-controller-family-bounded-calibration-smoke-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: bounded_calibration_smoke_design_admit_no_rollout_subset_preflight
- reason: M1704 designs a 6-base-spec 72-calibration-spec 864-cell bounded calibration smoke and routes to no-rollout subset preflight

## Next Blocker

m1705-paper-route-controller-family-bounded-calibration-smoke-preflight
