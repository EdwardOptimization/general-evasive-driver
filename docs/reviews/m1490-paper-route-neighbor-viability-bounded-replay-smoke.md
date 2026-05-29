# m1490-paper-route-neighbor-viability-bounded-replay-smoke Research Review

## Summary

- Generated at UTC: 20260529T065049Z
- Type: infrastructure
- Gate tier: proof
- Promotion decision: neighbor_viability_bounded_replay_positive_source_singleton_route_to_audit
- Decision reason: M1490 replay is positive with 7 history positives but all positives and 12 controls remain one source family

## Hypothesis

A bounded replay smoke over M1487 calibrated candidates can test whether neighbor viability calibration transfers to outcome-sensitive replay rows.

## Lineage

- parent_checkpoint: runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt
- parent_dataset: runs/m1487_neighbor_viability_preflight_smoke/selected_candidate_rows.csv, docs/m1489-paper-route-neighbor-viability-bounded-replay-design.md
- parent_config: configs/m1419_warmup_gate_invasiveness_retune_source_wave.json, experiments/manifests/m1489-paper-route-neighbor-viability-bounded-replay-design.json
- parent_objective: run bounded replay smoke over calibrated neighbor-viability preflight-pass candidates
- derived_from: m1489-paper-route-neighbor-viability-bounded-replay-design
- blocked_by: bounded replay has not yet been run on M1487 calibrated preflight-pass candidates
- supersedes: preflight-only evidence as outcome-sensitive replay evidence
- invalidates: None

## Success Criteria

- runs/m1490_neighbor_viability_bounded_replay_smoke/summary.json exists
- summary candidate_step_column equals source_step
- geometry_aware_selector true
- selected_candidate_rows >= 32
- actual_replay_rows > 0
- replay_started true
- training_started false
- ppo_used false
- promoted false
- private_holdout_used false
- training_corpus_exported false
- actor_input_contract_changed false

## Failure Criteria

- summary missing
- candidate_step_column is not source_step
- actual_replay_rows is zero
- run starts training PPO promotion private holdout corpus export or actor-input change

## Evidence Gates

- M1490 must run bounded replay with --candidate-step-column source_step
- M1490 must use --geometry-aware-selector
- M1490 must not train run PPO promote use private holdout export corpus or change actor inputs
- M1490 must report actual replay rows history positives control positives normal failures source diversity and viability-class counts

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not promote
- do not use private holdout
- do not add actor inputs
- do not export corpus
- do not treat one public replay smoke as paper-level evidence
- do not claim level3 self-identification from one public replay smoke

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1490-paper-route-neighbor-viability-bounded-replay-smoke
- type: infrastructure
- checkpoint: runs/m1490_neighbor_viability_bounded_replay_smoke/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: neighbor_viability_bounded_replay_positive_source_singleton_route_to_audit
- reason: M1490 replay is positive with 7 history positives but all positives and 12 controls remain one source family

## Next Blocker

m1491-paper-route-neighbor-viability-replay-result-audit
