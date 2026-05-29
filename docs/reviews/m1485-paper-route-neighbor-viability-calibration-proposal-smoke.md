# m1485-paper-route-neighbor-viability-calibration-proposal-smoke Research Review

## Summary

- Generated at UTC: 20260529T061253Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: neighbor_viability_calibration_proposal_smoke_pass_route_to_preflight_design
- Decision reason: M1485 selects 112 calibrated candidates including 88 neighbor-source rows across 5 seeds 6 capability pairs 6 reveal buckets and zero duplicate keys

## Hypothesis

The neighbor viability calibration generator can produce a calibrated source-diverse candidate pool from M1481 artifacts without replay or training.

## Lineage

- parent_checkpoint: runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt
- parent_dataset: runs/m1481_source_diverse_pressure_bounded_replay_smoke/actual_replay_rows.csv, runs/m1481_source_diverse_pressure_bounded_replay_smoke/history_positive_rows.csv, runs/m1481_source_diverse_pressure_bounded_replay_smoke/control_positive_rows.csv, docs/m1484-paper-route-neighbor-viability-calibration-implementation.md
- parent_config: experiments/manifests/m1484-paper-route-neighbor-viability-calibration-implementation.json
- parent_objective: run neighbor viability calibration proposal smoke without preflight or replay
- derived_from: m1484-paper-route-neighbor-viability-calibration-implementation
- blocked_by: neighbor viability calibration generator has not yet been run on M1481 artifacts
- supersedes: implementation-only evidence as proposal-count evidence
- invalidates: None

## Success Criteria

- runs/m1485_neighbor_viability_calibration_proposal_smoke/summary.json exists
- selected_candidate_rows >= 32
- selected_source_group_counts.neighbor_source > 0
- selected_duplicate_neighbor_viability_key_rows == 0
- candidate_step_column == source_step
- source_preflight_started false
- replay_started false
- training_started false
- ppo_used false
- promoted false
- private_holdout_used false
- training_corpus_exported false
- actor_input_contract_changed false

## Failure Criteria

- summary missing
- selected_candidate_rows < 32
- neighbor source candidates are missing
- duplicate neighbor viability keys remain
- run starts preflight replay training PPO promotion private holdout corpus export or actor-input change

## Evidence Gates

- M1485 must run proposal generation only
- M1485 must not run preflight replay train PPO promote use private holdout export corpus or change actor inputs
- M1485 must report selected rows source-group counts viability-class counts source diversity duplicate keys and guardrails

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
- do not treat proposal counts as replay evidence

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1485-paper-route-neighbor-viability-calibration-proposal-smoke
- type: infrastructure
- checkpoint: runs/m1485_neighbor_viability_calibration_proposal_smoke/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: neighbor_viability_calibration_proposal_smoke_pass_route_to_preflight_design
- reason: M1485 selects 112 calibrated candidates including 88 neighbor-source rows across 5 seeds 6 capability pairs 6 reveal buckets and zero duplicate keys

## Next Blocker

m1486-paper-route-neighbor-viability-preflight-design
