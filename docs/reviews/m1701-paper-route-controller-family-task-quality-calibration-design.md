# m1701-paper-route-controller-family-task-quality-calibration-design Research Review

## Summary

- Generated at UTC: 20260530T005028Z
- Type: gate
- Gate tier: process
- Promotion decision: task_quality_calibration_design_admit_no_rollout_preflight
- Decision reason: M1701 designs outcome-conditional task-quality calibration axes and routes to no-rollout matrix preflight before execution

## Hypothesis

A task-quality calibration plan can define outcome-conditional metrics and workload checks that avoid ranking controllers on off-track dominated raw success.

## Lineage

- parent_checkpoint: runs/m1674_controller_family_one_seed_public_pilot/profile_runs/*/seed_167400/checkpoint.pt
- parent_dataset: docs/m1700-paper-route-controller-family-outcome-semantics-branch-synthesis.md, runs/m1698_controller_family_instrumented_full_rollout/outcome_aggregate.csv, runs/m1698_controller_family_instrumented_full_rollout/profile_outcome_aggregate.csv
- parent_config: experiments/manifests/m1700-paper-route-controller-family-outcome-semantics-branch-synthesis.json
- parent_objective: design calibrated task-quality route after off-track dominated instrumented rerun
- derived_from: m1700-paper-route-controller-family-outcome-semantics-branch-synthesis
- blocked_by: M1700 pivots to task-quality calibration because current workload is off-track dominated
- supersedes: direct controller-family ranking from M1698, direct profile tuning from M1698
- invalidates: None

## Success Criteria

- docs/m1701-paper-route-controller-family-task-quality-calibration-design.md exists
- design specifies outcome-conditional metrics
- design specifies corridor/boundary and finish semantics checks
- design specifies source/spec stratification or filters
- design preserves P0 actor input contract and no-tuning boundary
- rollout execution training replay PPO promotion private holdout actor-input changes and level3 claims remain blocked

## Failure Criteria

- design ignores off-track dominance
- design allows ranking from raw success
- design changes actor inputs or profile configs
- design routes directly to training or profile tuning
- rollout execution training replay PPO private holdout promotion or actor-input changes occur

## Evidence Gates

- M1701 must design but not execute the calibrated task-quality route
- M1701 must separate off-track, collision, obstacle pass, and max-step noncompletion metrics
- M1701 must preserve P0 actor input contract and no profile-specific tuning
- M1701 must specify source/spec/corridor/finish semantics checks before any rerun
- M1701 must not claim controller-family ranking, paper-level evidence, private-holdout evidence, or level3 self-ID

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

- milestone: m1701-paper-route-controller-family-task-quality-calibration-design
- type: gate
- checkpoint: docs/m1701-paper-route-controller-family-task-quality-calibration-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: task_quality_calibration_design_admit_no_rollout_preflight
- reason: M1701 designs outcome-conditional task-quality calibration axes and routes to no-rollout matrix preflight before execution

## Next Blocker

m1702-paper-route-controller-family-task-quality-calibration-preflight
