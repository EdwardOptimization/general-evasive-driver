# m1429-paper-route-bounded-relocation-replay-smoke Research Review

## Summary

- Generated at UTC: 20260529T023506Z
- Type: infrastructure
- Gate tier: proof
- Promotion decision: bounded_relocation_replay_no_history_positive_route_to_geometry_audit
- Decision reason: M1429 runs 384 actual replay rows with 0 history-positive rows and reveals source geometry clipping plus seed concentration so routes to audit

## Hypothesis

Actual bounded relocation replay can reveal history-positive terminal-margin sensitivity that the M1425 shared-margin proxy could not show.

## Lineage

- parent_checkpoint: runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt
- parent_dataset: runs/m1425_action_divergent_outcome_pressure_source_smoke/outcome_pressure_rows.csv, docs/m1428-paper-route-bounded-relocation-replay-implementation.md
- parent_config: experiments/manifests/m1428-paper-route-bounded-relocation-replay-implementation.json
- parent_objective: run no-training bounded relocation replay smoke on M1425 pressure rows
- derived_from: m1428-paper-route-bounded-relocation-replay-implementation
- blocked_by: M1428 implementation must be exercised in a separately registered public replay smoke
- supersedes: proxy-only interpretation of M1425 rows
- invalidates: None

## Success Criteria

- runs/m1429_bounded_relocation_replay_smoke/summary.json exists
- selected_candidate_rows >= 64
- actual_replay_rows >= 192
- history_positive_rows >= 8
- history_positive_unique_source_seeds >= 3
- history_positive_unique_capability_pairs >= 3
- history_positive_unique_reveal_buckets >= 2
- control_positive_rows reported separately
- training_started false
- ppo_used false
- promoted false
- private_holdout_used false
- training_corpus_exported false
- actor_input_contract_changed false

## Failure Criteria

- summary missing
- selected or replay rows are sparse
- history-positive rows are zero or not source-diverse
- control positives are mixed into history positives
- run starts training PPO promotion private holdout corpus export or actor-input changes

## Evidence Gates

- M1429 must run no-training bounded relocation replay on public M1425 pressure rows
- M1429 must count history-positive only from actual replay rows
- M1429 must report reset and zero-current controls separately
- M1429 must not train run PPO promote use private holdout export corpus or change actor inputs

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not promote
- do not use private holdout
- do not add actor inputs
- do not export a training corpus
- do not count proxy rows as replay evidence
- do not count reset or zero-current controls as history-positive

## Failure Taxonomy

- scenario_sampling_failure

## Scoreboard

- milestone: m1429-paper-route-bounded-relocation-replay-smoke
- type: infrastructure
- checkpoint: runs/m1429_bounded_relocation_replay_smoke/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: bounded_relocation_replay_no_history_positive_route_to_geometry_audit
- reason: M1429 runs 384 actual replay rows with 0 history-positive rows and reveals source geometry clipping plus seed concentration so routes to audit

## Next Blocker

m1430-paper-route-bounded-relocation-replay-result-audit
