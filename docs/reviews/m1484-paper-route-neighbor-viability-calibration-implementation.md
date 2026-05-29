# m1484-paper-route-neighbor-viability-calibration-implementation Research Review

## Summary

- Generated at UTC: 20260529T060838Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: neighbor_viability_calibration_generator_implemented_admit_proposal_smoke
- Decision reason: M1484 implements neighbor viability calibration generation with focused tests and no preflight replay training or corpus export

## Hypothesis

A no-training generator can calibrate M1481 neighbor rows into normal-viable source-diverse candidates while keeping controls separate.

## Lineage

- parent_checkpoint: runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt
- parent_dataset: docs/m1483-paper-route-neighbor-viability-calibration-design.md, runs/m1481_source_diverse_pressure_bounded_replay_smoke/actual_replay_rows.csv, runs/m1481_source_diverse_pressure_bounded_replay_smoke/history_positive_rows.csv, runs/m1481_source_diverse_pressure_bounded_replay_smoke/control_positive_rows.csv
- parent_config: experiments/manifests/m1483-paper-route-neighbor-viability-calibration-design.json
- parent_objective: implement no-training neighbor normal-viability calibration generator
- derived_from: m1483-paper-route-neighbor-viability-calibration-design
- blocked_by: neighbor normal-viability calibration generator is not yet implemented
- supersedes: manual calibration of M1481 neighbor rows
- invalidates: None

## Success Criteria

- neighbor viability calibration generator is implemented
- focused tests pass for original-source separation
- focused tests pass for too_hard near_boundary and too_easy classification
- focused tests pass for source_step preservation
- focused tests pass for control-positive separation
- focused tests pass for source-diverse selection caps
- docs/m1484-paper-route-neighbor-viability-calibration-implementation.md exists
- no preflight replay training PPO promotion private holdout corpus export or actor-input change occurs

## Failure Criteria

- implementation is missing
- tests do not cover source_step or control separation
- implementation starts preflight replay training PPO promotion private holdout corpus export or actor-input change

## Evidence Gates

- M1484 must implement candidate generation only
- M1484 must separate original-source positives neighbor-source failures and controls
- M1484 must preserve source_step and candidate_step_column == source_step
- M1484 must not run preflight replay train PPO promote use private holdout export corpus or change actor inputs

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not run source preflight
- do not run bounded replay
- do not run outcome interventions
- do not promote
- do not use private holdout
- do not add actor inputs
- do not export corpus
- do not replay original-source positives unchanged

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1484-paper-route-neighbor-viability-calibration-implementation
- type: infrastructure
- checkpoint: docs/m1484-paper-route-neighbor-viability-calibration-implementation.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: neighbor_viability_calibration_generator_implemented_admit_proposal_smoke
- reason: M1484 implements neighbor viability calibration generation with focused tests and no preflight replay training or corpus export

## Next Blocker

m1485-paper-route-neighbor-viability-calibration-proposal-smoke
