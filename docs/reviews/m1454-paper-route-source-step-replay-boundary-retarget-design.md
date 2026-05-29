# m1454-paper-route-source-step-replay-boundary-retarget-design Research Review

## Summary

- Generated at UTC: 20260529T043256Z
- Type: gate
- Gate tier: process
- Promotion decision: source_step_replay_boundary_retarget_design_route_to_branch_synthesis
- Decision reason: M1454 designs normal-viable near-boundary retargeting from M1452 replay diagnostics and routes to synthesis before implementation

## Hypothesis

M1452 failed to produce history positives because replay pressure was not normal-viable near-boundary enough, so a boundary retarget design is the next admissible step.

## Lineage

- parent_checkpoint: runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt
- parent_dataset: runs/m1452_source_step_bounded_replay_smoke/actual_replay_rows.csv, docs/m1453-paper-route-source-step-bounded-replay-result-audit.md
- parent_config: experiments/manifests/m1453-paper-route-source-step-bounded-replay-result-audit.json
- parent_objective: design boundary retargeting after source-step replay smoke found zero history positives and many normal failures
- derived_from: m1453-paper-route-source-step-bounded-replay-result-audit
- blocked_by: M1452 replay pressure is not normal-viable near-boundary enough
- supersedes: training from M1452 zero-positive replay rows
- invalidates: None

## Success Criteria

- docs/m1454-paper-route-source-step-replay-boundary-retarget-design.md exists
- design uses M1452 actual replay diagnostics
- design includes normal viability filters
- design blocks training and corpus export

## Failure Criteria

- design document is missing
- design ignores normal_failed_rows
- design routes directly to training PPO promotion private holdout corpus export or actor-input change

## Evidence Gates

- M1454 must design normal-viable near-boundary retargeting before any replay rerun
- M1454 must use M1452 actual replay diagnostics
- M1454 must not run replay train PPO promote use private holdout export corpus or change actor inputs

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not run replay
- do not promote
- do not use private holdout
- do not add actor inputs
- do not export corpus

## Failure Taxonomy

- scenario_sampling_failure

## Scoreboard

- milestone: m1454-paper-route-source-step-replay-boundary-retarget-design
- type: gate
- checkpoint: docs/m1454-paper-route-source-step-replay-boundary-retarget-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: source_step_replay_boundary_retarget_design_route_to_branch_synthesis
- reason: M1454 designs normal-viable near-boundary retargeting from M1452 replay diagnostics and routes to synthesis before implementation

## Next Blocker

m1455-paper-route-forward-source-preflight-validation-branch-synthesis
