# m1544-paper-route-terminal-boundary-task-sampling-calibration-implementation Research Review

## Summary

- Generated at UTC: 20260529T120224Z
- Type: infrastructure
- Gate tier: process
- Promotion decision: terminal_boundary_task_sampling_calibration_smoke_pass_route_to_audit
- Decision reason: M1544 calibration smoke found 8 accepted calibrated rows across 4 terminal families with decision hits 4 post-decision hits 5 max family share 0.25 and clean guardrails

## Hypothesis

A bounded calibration implementation can generate actual fixed-policy terminal target rows in decision/post-decision near-boundary windows without changing actor inputs or materializing candidates.

## Lineage

- parent_checkpoint: runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt
- parent_dataset: docs/m1543-paper-route-terminal-boundary-task-sampling-calibration-design.md, docs/m1542-paper-route-terminal-boundary-source-repair-result-audit.md
- parent_config: experiments/manifests/m1543-paper-route-terminal-boundary-task-sampling-calibration-design.json
- parent_objective: implement bounded terminal-boundary task-sampling calibration before history interventions
- derived_from: m1543-paper-route-terminal-boundary-task-sampling-calibration-design
- blocked_by: M1541 terminal target traces missed the near-boundary decision window
- supersedes: direct rerun of terminal-boundary history interventions on uncalibrated rows
- invalidates: None

## Success Criteria

- terminal-boundary task-sampling calibration module exists
- focused tests cover calibration grid guardrails and summary schema
- runs/m1544_terminal_boundary_task_sampling_calibration_smoke/summary.json exists
- candidate materialization training PPO promotion private holdout actor-input changes and training-corpus export remain blocked
- follow-up result audit manifest exists

## Failure Criteria

- calibration module or smoke artifacts are missing
- implementation changes actor inputs or uses private holdout
- implementation materializes candidates exports a training corpus or starts training/PPO
- implementation claims level3 self-identification

## Evidence Gates

- M1544 must implement bounded calibration before interventions
- M1544 must measure actual simulator decision/post-decision margins
- M1544 must preserve P0 actor input contract
- M1544 must keep materialization and training blocked

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

- milestone: m1544-paper-route-terminal-boundary-task-sampling-calibration-implementation
- type: infrastructure
- checkpoint: runs/m1544_terminal_boundary_task_sampling_calibration_smoke/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: terminal_boundary_task_sampling_calibration_smoke_pass_route_to_audit
- reason: M1544 calibration smoke found 8 accepted calibrated rows across 4 terminal families with decision hits 4 post-decision hits 5 max family share 0.25 and clean guardrails

## Next Blocker

m1545-paper-route-terminal-boundary-task-sampling-calibration-result-audit
