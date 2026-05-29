# m1470-paper-route-positive-neighborhood-preflight-smoke Research Review

## Summary

- Generated at UTC: 20260529T051949Z
- Type: infrastructure
- Gate tier: proof
- Promotion decision: positive_neighborhood_preflight_pass_route_to_bounded_replay_design
- Decision reason: M1470 passes preflight with 192 geometry-pass rows 171 selected rows zero clipping and 171 unique positive-neighborhood keys

## Hypothesis

M1468 deduplicated positive-neighborhood candidates remain forward, unclipped, source-diverse, unique-key preserved, and source_step anchored when reconstructed by preflight.

## Lineage

- parent_checkpoint: runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt
- parent_dataset: runs/m1468_positive_neighborhood_dedup_smoke/positive_neighborhood_candidate_rows.csv, docs/m1469-paper-route-positive-neighborhood-preflight-design.md
- parent_config: configs/m1419_warmup_gate_invasiveness_retune_source_wave.json, experiments/manifests/m1469-paper-route-positive-neighborhood-preflight-design.json
- parent_objective: run preflight-only validation on M1468 deduplicated positive-neighborhood candidates
- derived_from: m1469-paper-route-positive-neighborhood-preflight-design
- blocked_by: deduplicated positive-neighborhood candidates have not yet passed source-step preflight
- supersedes: bounded replay directly from M1468 proposal rows
- invalidates: None

## Success Criteria

- runs/m1470_positive_neighborhood_preflight_smoke/summary.json exists
- summary candidate_step_column equals source_step
- geometry_pass_rows >= 64
- selected_candidate_rows >= 64
- selected_diversity.unique_source_seeds >= 2
- selected_diversity.unique_capability_pairs >= 2
- selected_diversity.max_single_seed_share <= 0.40
- relocation_clipped_share <= 0.10
- source_body_x_min >= 4.0
- replay_started false
- training_started false
- ppo_used false
- promoted false
- private_holdout_used false
- training_corpus_exported false
- actor_input_contract_changed false

## Failure Criteria

- summary missing
- candidate_step_column is not source_step
- geometry or diversity gates fail
- preflight rows are counted as replay evidence
- run starts replay training PPO promotion private holdout corpus export or actor-input change

## Evidence Gates

- M1470 must run --preflight-only with --candidate-step-column source_step
- M1470 must not run bounded replay train PPO promote use private holdout export corpus or change actor inputs
- M1470 must report geometry pass rows selected rows clipping share diversity and unique-key retention

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not run closed-loop replay
- do not run outcome interventions
- do not promote
- do not use private holdout
- do not add actor inputs
- do not export corpus
- do not mutate reveal_step values
- do not count preflight rows as replay or history-positive evidence

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1470-paper-route-positive-neighborhood-preflight-smoke
- type: infrastructure
- checkpoint: runs/m1470_positive_neighborhood_preflight_smoke/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: positive_neighborhood_preflight_pass_route_to_bounded_replay_design
- reason: M1470 passes preflight with 192 geometry-pass rows 171 selected rows zero clipping and 171 unique positive-neighborhood keys

## Next Blocker

m1471-paper-route-positive-neighborhood-bounded-replay-design
