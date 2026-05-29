# m1483-paper-route-neighbor-viability-calibration-design Research Review

## Summary

- Generated at UTC: 20260529T055959Z
- Type: gate
- Gate tier: process
- Promotion decision: neighbor_viability_calibration_design_admit_implementation
- Decision reason: M1483 designs neighbor normal-viability calibration classes before another source-diverse replay attempt

## Hypothesis

A neighbor normal-viability calibration design can target source-diverse rows that are normal-viable and margin-gap-sensitive rather than replaying the original source surface.

## Lineage

- parent_checkpoint: runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt
- parent_dataset: runs/m1481_source_diverse_pressure_bounded_replay_smoke/actual_replay_rows.csv, runs/m1481_source_diverse_pressure_bounded_replay_smoke/history_positive_rows.csv, runs/m1481_source_diverse_pressure_bounded_replay_smoke/control_positive_rows.csv, docs/m1482-paper-route-source-diverse-pressure-replay-result-audit.md
- parent_config: experiments/manifests/m1482-paper-route-source-diverse-pressure-replay-result-audit.json
- parent_objective: design neighbor normal-viability calibration after source-diverse pressure replay positives remain source-singleton
- derived_from: m1482-paper-route-source-diverse-pressure-replay-result-audit
- blocked_by: M1481 neighbor-source replay rows did not become history-positive because normal viability and margin-gap pressure were not jointly calibrated
- supersedes: replaying M1481 source-diverse pressure rows unchanged
- invalidates: None

## Success Criteria

- docs/m1483-paper-route-neighbor-viability-calibration-design.md exists
- design separates original-source positives neighbor-source failures and controls
- design defines too_hard near_boundary and too_easy neighbor classes
- design blocks training PPO promotion private holdout corpus export and actor-input changes
- design routes to implementation or synthesis

## Failure Criteria

- design document is missing
- design replays original-source positives unchanged
- design ignores neighbor normal viability
- design starts replay training PPO promotion private holdout corpus export or actor-input change

## Evidence Gates

- M1483 must design neighbor-source calibration before another replay
- M1483 must separate original-source positives neighbor-source failures and controls
- M1483 must block replay training PPO promotion private holdout corpus export and actor-input changes

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
- do not replay M1481 rows unchanged
- do not treat source-singleton positives as source-diverse evidence

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1483-paper-route-neighbor-viability-calibration-design
- type: gate
- checkpoint: docs/m1483-paper-route-neighbor-viability-calibration-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: neighbor_viability_calibration_design_admit_implementation
- reason: M1483 designs neighbor normal-viability calibration classes before another source-diverse replay attempt

## Next Blocker

m1484-paper-route-neighbor-viability-calibration-implementation
