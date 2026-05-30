# m1727-paper-route-task-quality-scenario-taxonomy-design Research Review

## Summary

- Generated at UTC: 20260530T025740Z
- Type: gate
- Gate tier: process
- Promotion decision: scenario_taxonomy_design_admit_no_rollout_preflight
- Decision reason: M1727 designs 6-family 72-spec 864-cell scenario taxonomy and admits no-rollout materialization preflight

## Hypothesis

A paper-route scenario taxonomy can be designed to replace narrow public off-track repair with structured task-quality distributions before controller-family comparison.

## Lineage

- parent_checkpoint: not_applicable_design_only
- parent_dataset: docs/m1726-paper-route-controller-family-task-quality-repair-branch-synthesis.md, docs/m1725-paper-route-controller-family-off-track-repair-panel-result-audit.md, runs/m1724_off_track_repair_panel_execution/summary.json, runs/m1724_off_track_repair_panel_execution/repair_variant_aggregate.csv
- parent_config: experiments/manifests/m1726-paper-route-controller-family-task-quality-repair-branch-synthesis.json
- parent_objective: design scenario taxonomy after task-quality repair branch synthesis
- derived_from: m1726-paper-route-controller-family-task-quality-repair-branch-synthesis
- blocked_by: need scenario taxonomy before another repair panel or controller-family comparison
- supersedes: direct second off-track repair panel, direct controller-family comparison on off-track-dominated public tasks
- invalidates: None

## Success Criteria

- docs/m1727-paper-route-task-quality-scenario-taxonomy-design.md exists
- taxonomy includes ordinary avoidance AEB-infeasible stable AES drift-required avoidance unavoidable mitigation off-track boundary stress and hidden-dynamics stress
- no-rollout materialization inputs and outputs are specified
- preflight pass/fail checks are specified
- human-view actor input and controller-family controls remain unchanged
- rollout execution training replay PPO promotion private holdout actor-input changes ranking and level3 claims remain blocked

## Failure Criteria

- design document is missing
- taxonomy is just another local repair axis
- taxonomy omits pass/fail preflight checks
- taxonomy ranks profiles or changes actor inputs
- environment rollout training replay PPO private holdout promotion or actor-input changes occur

## Evidence Gates

- M1727 must design a scenario taxonomy after M1726 without running rollout
- M1727 must separate ordinary avoidance, AEB-infeasible stable AES, drift-required avoidance, unavoidable mitigation, off-track boundary stress, and hidden-dynamics stress
- M1727 must define no-rollout materialization artifacts and pass/fail preflight checks for the next milestone
- M1727 must preserve human-view/no-privileged actor input contract and controller-family controls
- M1727 must not train replay PPO promote use private holdout or rank controller families

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
- do not rank controller families
- do not claim paper-level evidence
- do not claim level3 self-identification

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1727-paper-route-task-quality-scenario-taxonomy-design
- type: gate
- checkpoint: docs/m1727-paper-route-task-quality-scenario-taxonomy-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: scenario_taxonomy_design_admit_no_rollout_preflight
- reason: M1727 designs 6-family 72-spec 864-cell scenario taxonomy and admits no-rollout materialization preflight

## Next Blocker

m1728-paper-route-task-quality-scenario-taxonomy-preflight
