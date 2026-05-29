# m1486-paper-route-neighbor-viability-preflight-design Research Review

## Summary

- Generated at UTC: 20260529T063636Z
- Type: gate
- Gate tier: process
- Promotion decision: neighbor_viability_preflight_design_admit_smoke
- Decision reason: M1486 designs source-step preflight-only validation over 112 M1485 calibrated candidates before branch synthesis and any replay

## Hypothesis

A source-step preflight-only design over M1485 calibrated candidates can validate geometry viability before another bounded replay attempt.

## Lineage

- parent_checkpoint: runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt
- parent_dataset: runs/m1485_neighbor_viability_calibration_proposal_smoke/neighbor_viability_candidate_rows.csv, runs/m1485_neighbor_viability_calibration_proposal_smoke/summary.json, docs/m1485-paper-route-neighbor-viability-calibration-proposal-smoke.md
- parent_config: experiments/manifests/m1485-paper-route-neighbor-viability-calibration-proposal-smoke.json
- parent_objective: design preflight-only validation over M1485 calibrated neighbor-viability candidates
- derived_from: m1485-paper-route-neighbor-viability-calibration-proposal-smoke
- blocked_by: source preflight has not yet been designed for M1485 calibrated candidates
- supersedes: proposal counts as geometry viability evidence
- invalidates: None

## Success Criteria

- docs/m1486-paper-route-neighbor-viability-preflight-design.md exists
- design uses runs/m1485_neighbor_viability_calibration_proposal_smoke/neighbor_viability_candidate_rows.csv
- design uses candidate_step_column source_step
- design blocks replay training PPO promotion private holdout corpus export and actor-input changes
- design routes to preflight smoke or synthesis

## Failure Criteria

- design document is missing
- design starts preflight
- design does not use source_step
- design starts replay training PPO promotion private holdout corpus export or actor-input change

## Evidence Gates

- M1486 must design source preflight only
- M1486 must use M1485 neighbor_viability_candidate_rows.csv
- M1486 must use candidate_step_column == source_step
- M1486 must block replay training PPO promotion private holdout corpus export and actor-input changes

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not run source preflight in this design milestone
- do not run bounded replay
- do not run outcome interventions
- do not promote
- do not use private holdout
- do not add actor inputs
- do not export corpus
- do not treat proposal rows as geometry-pass evidence

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1486-paper-route-neighbor-viability-preflight-design
- type: gate
- checkpoint: docs/m1486-paper-route-neighbor-viability-preflight-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: neighbor_viability_preflight_design_admit_smoke
- reason: M1486 designs source-step preflight-only validation over 112 M1485 calibrated candidates before branch synthesis and any replay

## Next Blocker

m1487-paper-route-neighbor-viability-preflight-smoke
