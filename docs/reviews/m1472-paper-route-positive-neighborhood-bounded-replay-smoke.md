# m1472-paper-route-positive-neighborhood-bounded-replay-smoke Research Review

## Summary

- Generated at UTC: 20260529T052605Z
- Type: infrastructure
- Gate tier: proof
- Promotion decision: positive_neighborhood_bounded_replay_positive_local_surface_route_to_audit
- Decision reason: M1472 expands the M1461 singleton into 8 history positives across 7 relocation keys but still only 1 source and 12 zero-current controls

## Hypothesis

A bounded replay smoke over M1470 deduplicated positive-neighborhood candidates can test whether the M1461 singleton expands to a broader outcome-sensitive surface.

## Lineage

- parent_checkpoint: runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt
- parent_dataset: runs/m1470_positive_neighborhood_preflight_smoke/selected_candidate_rows.csv, docs/m1471-paper-route-positive-neighborhood-bounded-replay-design.md
- parent_config: configs/m1419_warmup_gate_invasiveness_retune_source_wave.json, experiments/manifests/m1471-paper-route-positive-neighborhood-bounded-replay-design.json
- parent_objective: run positive-neighborhood bounded replay smoke on M1470 selected candidates
- derived_from: m1471-paper-route-positive-neighborhood-bounded-replay-design
- blocked_by: bounded replay has not yet been run on positive-neighborhood preflight-pass candidates
- supersedes: preflight-only evidence as final outcome evidence
- invalidates: None

## Success Criteria

- runs/m1472_positive_neighborhood_bounded_replay_smoke/summary.json exists
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

- M1472 must run bounded replay with --candidate-step-column source_step
- M1472 must not train run PPO promote use private holdout export corpus or change actor inputs
- M1472 must report selected candidate rows actual replay rows history positives control positives normal failures and unique-key diagnostics

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not promote
- do not use private holdout
- do not add actor inputs
- do not export corpus
- do not treat a smoke positive as promotion evidence
- do not claim level3 self-identification from one public replay smoke

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1472-paper-route-positive-neighborhood-bounded-replay-smoke
- type: infrastructure
- checkpoint: runs/m1472_positive_neighborhood_bounded_replay_smoke/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: positive_neighborhood_bounded_replay_positive_local_surface_route_to_audit
- reason: M1472 expands the M1461 singleton into 8 history positives across 7 relocation keys but still only 1 source and 12 zero-current controls

## Next Blocker

m1473-paper-route-positive-neighborhood-replay-result-audit
