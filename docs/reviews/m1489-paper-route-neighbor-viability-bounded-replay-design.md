# m1489-paper-route-neighbor-viability-bounded-replay-design Research Review

## Summary

- Generated at UTC: 20260529T064647Z
- Type: gate
- Gate tier: process
- Promotion decision: neighbor_viability_bounded_replay_design_admit_smoke
- Decision reason: M1489 designs one calibrated bounded replay over M1487 selected rows with mandatory audit and no training or corpus export

## Hypothesis

A bounded replay smoke over M1487 preflight-pass calibrated candidates can test whether neighbor viability calibration transfers to outcome-sensitive replay rows.

## Lineage

- parent_checkpoint: runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt
- parent_dataset: runs/m1487_neighbor_viability_preflight_smoke/selected_candidate_rows.csv, runs/m1487_neighbor_viability_preflight_smoke/summary.json, docs/m1488-paper-route-source-diverse-pressure-validation-synthesis.md
- parent_config: configs/m1419_warmup_gate_invasiveness_retune_source_wave.json, experiments/manifests/m1488-paper-route-source-diverse-pressure-validation-synthesis.json
- parent_objective: design one calibrated bounded replay smoke over M1487 preflight-pass candidates
- derived_from: m1488-paper-route-source-diverse-pressure-validation-synthesis
- blocked_by: bounded replay has not yet been designed for M1487 calibrated preflight-pass candidates
- supersedes: preflight-only evidence as outcome-sensitive replay evidence
- invalidates: None

## Success Criteria

- docs/m1489-paper-route-neighbor-viability-bounded-replay-design.md exists
- design uses runs/m1487_neighbor_viability_preflight_smoke/selected_candidate_rows.csv
- design uses --geometry-aware-selector
- design uses candidate_step_column source_step
- design blocks training PPO promotion private holdout corpus export and actor-input changes
- design routes to bounded replay smoke followed by mandatory audit

## Failure Criteria

- design document is missing
- design starts replay
- design does not use source_step
- design starts training PPO promotion private holdout corpus export or actor-input change

## Evidence Gates

- M1489 must design bounded replay only
- M1489 must use M1487 selected candidate rows with --candidate-step-column source_step
- M1489 must use --geometry-aware-selector
- M1489 must block training PPO promotion private holdout corpus export and actor-input changes
- M1489 must require replay result audit immediately after the replay run

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not run bounded replay in this design milestone
- do not run outcome interventions outside the future replay command
- do not promote
- do not use private holdout
- do not add actor inputs
- do not export corpus
- do not treat preflight result as history-positive evidence

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1489-paper-route-neighbor-viability-bounded-replay-design
- type: gate
- checkpoint: docs/m1489-paper-route-neighbor-viability-bounded-replay-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: neighbor_viability_bounded_replay_design_admit_smoke
- reason: M1489 designs one calibrated bounded replay over M1487 selected rows with mandatory audit and no training or corpus export

## Next Blocker

m1490-paper-route-neighbor-viability-bounded-replay-smoke
