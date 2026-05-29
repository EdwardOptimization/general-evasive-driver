# m1543-paper-route-terminal-boundary-task-sampling-calibration-design Research Review

## Summary

- Generated at UTC: 20260529T115521Z
- Type: gate
- Gate tier: process
- Promotion decision: terminal_boundary_task_sampling_calibration_design_admit_bounded_implementation
- Decision reason: M1543 designs bounded terminal-boundary task calibration targeting actual fixed-policy decision/post-decision margins before another history-intervention smoke

## Hypothesis

A bounded task-sampling calibration design can repair M1541's source-window miss by targeting actual fixed-policy terminal margins before another history-intervention run.

## Lineage

- parent_checkpoint: runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt
- parent_dataset: docs/m1542-paper-route-terminal-boundary-source-repair-result-audit.md, runs/m1541_terminal_boundary_source_repair_smoke/summary.json
- parent_config: experiments/manifests/m1542-paper-route-terminal-boundary-source-repair-result-audit.json
- parent_objective: design task-sampling calibration for terminal-boundary near-boundary rows before interventions
- derived_from: m1542-paper-route-terminal-boundary-source-repair-result-audit
- blocked_by: M1541 terminal_target_near_boundary_count is zero, M1541 history interventions are null and control dominated
- supersedes: rerunning terminal-boundary interventions on uncalibrated source rows
- invalidates: None

## Success Criteria

- docs/m1543-paper-route-terminal-boundary-task-sampling-calibration-design.md exists
- design defines calibration variables and pass/fail thresholds
- design separates decision-window and post-decision margin targets
- candidate materialization training PPO promotion private holdout actor-input changes and training-corpus export remain blocked
- follow-up implementation manifest exists

## Failure Criteria

- design document is missing
- design routes directly to interventions without calibrating actual margins
- design changes actor inputs or weakens self-ID evidence standards
- design routes directly to training promotion private holdout or materialization

## Evidence Gates

- M1543 must design calibration before rerunning interventions
- M1543 must target actual simulator decision/post-decision margins
- M1543 must preserve the P0 actor input contract
- M1543 must keep materialization and training blocked

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not promote
- do not use private holdout
- do not add actor inputs
- do not export training corpus
- do not materialize candidates
- do not claim level3 self-identification

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1543-paper-route-terminal-boundary-task-sampling-calibration-design
- type: gate
- checkpoint: docs/m1543-paper-route-terminal-boundary-task-sampling-calibration-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: terminal_boundary_task_sampling_calibration_design_admit_bounded_implementation
- reason: M1543 designs bounded terminal-boundary task calibration targeting actual fixed-policy decision/post-decision margins before another history-intervention smoke

## Next Blocker

m1544-paper-route-terminal-boundary-task-sampling-calibration-implementation
