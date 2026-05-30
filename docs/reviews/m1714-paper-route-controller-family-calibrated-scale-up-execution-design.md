# m1714-paper-route-controller-family-calibrated-scale-up-execution-design Research Review

## Summary

- Generated at UTC: 20260530T015027Z
- Type: gate
- Gate tier: process
- Promotion decision: calibrated_scale_up_execution_design_admit_measured_execution
- Decision reason: M1714 designs 864-episode source-expanded scale-up execution protocol with variant aggregates and collision/off-track thresholds

## Hypothesis

A measured execution protocol can be designed for the M1712 scale-up subset without overclaiming or changing the actor contract.

## Lineage

- parent_checkpoint: runs/m1674_controller_family_one_seed_public_pilot/profile_runs/*/seed_167400/checkpoint.pt
- parent_dataset: docs/m1713-paper-route-controller-family-calibrated-scale-up-preflight-result-audit.md, runs/m1712_controller_family_calibrated_scale_up_preflight/scale_up_calibration_specs.json, runs/m1712_controller_family_calibrated_scale_up_preflight/scale_up_matrix.csv
- parent_config: experiments/manifests/m1713-paper-route-controller-family-calibrated-scale-up-preflight-result-audit.json
- parent_objective: design measured execution for source-expanded calibrated scale-up
- derived_from: m1713-paper-route-controller-family-calibrated-scale-up-preflight-result-audit
- blocked_by: need execution design before measured rollout over scale-up subset
- supersedes: direct calibrated scale-up execution after M1713
- invalidates: None

## Success Criteria

- docs/m1714-paper-route-controller-family-calibrated-scale-up-execution-design.md exists
- execution input and output artifacts are specified
- scale-up variant outcome and termination aggregates are required
- collision/off-track tradeoff audit thresholds are specified
- rollout execution training replay PPO promotion private holdout actor-input changes and level3 claims remain blocked

## Failure Criteria

- design executes rollout
- design ranks profiles directly
- design omits variant aggregates or tradeoff thresholds
- design changes actor inputs or profile configs
- training replay PPO private holdout promotion or level3 claims occur

## Evidence Gates

- M1714 must design execution over the M1712 864-cell scale-up matrix without running it
- M1714 must require scale-up variant outcome and termination aggregates
- M1714 must pre-register collision/off-track tradeoff audit thresholds
- M1714 must keep task-quality scale-up separate from controller-family ranking
- M1714 must not train replay PPO promote use private holdout or change actor inputs

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

- milestone: m1714-paper-route-controller-family-calibrated-scale-up-execution-design
- type: gate
- checkpoint: docs/m1714-paper-route-controller-family-calibrated-scale-up-execution-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: calibrated_scale_up_execution_design_admit_measured_execution
- reason: M1714 designs 864-episode source-expanded scale-up execution protocol with variant aggregates and collision/off-track thresholds

## Next Blocker

m1715-paper-route-controller-family-calibrated-scale-up-execution
