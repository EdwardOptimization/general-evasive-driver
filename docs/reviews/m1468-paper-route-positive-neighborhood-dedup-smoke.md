# m1468-paper-route-positive-neighborhood-dedup-smoke Research Review

## Summary

- Generated at UTC: 20260529T051536Z
- Type: infrastructure
- Gate tier: proof
- Promotion decision: positive_neighborhood_dedup_smoke_pass_route_to_preflight_design
- Decision reason: M1468 verifies dedup repair with 192 selected candidates 192 unique keys 0 duplicate rows and source-diverse coverage

## Hypothesis

After M1467, positive-neighborhood proposal selection contains no duplicate positive_neighborhood_key rows.

## Lineage

- parent_checkpoint: runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt
- parent_dataset: runs/m1461_retargeted_source_step_bounded_replay_smoke/history_positive_rows.csv, runs/m1461_retargeted_source_step_bounded_replay_smoke/control_positive_rows.csv, runs/m1459_retargeted_source_step_preflight_smoke/selected_candidate_rows.csv, docs/m1467-paper-route-positive-neighborhood-dedup-repair.md
- parent_config: experiments/manifests/m1467-paper-route-positive-neighborhood-dedup-repair.json
- parent_objective: rerun positive-neighborhood expansion proposal smoke after duplicate-key repair
- derived_from: m1467-paper-route-positive-neighborhood-dedup-repair
- blocked_by: dedup repair has not yet been validated on M1461/M1459 inputs
- supersedes: m1465 duplicated selected candidates
- invalidates: None

## Success Criteria

- runs/m1468_positive_neighborhood_dedup_smoke/summary.json exists
- proposal_rows >= 64
- selected_candidate_rows >= 16
- selected_unique_positive_neighborhood_keys == selected_candidate_rows
- selected_duplicate_positive_neighborhood_key_rows == 0
- candidate_step_column equals source_step
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
- duplicate selected keys remain
- selected candidate rows are sparse
- candidate_step_column is not source_step
- run starts preflight replay training PPO promotion private holdout corpus export or actor-input change

## Evidence Gates

- M1468 must run proposal generation only
- M1468 must report selected_unique_positive_neighborhood_keys and selected_duplicate_positive_neighborhood_key_rows
- M1468 must not run preflight replay train PPO promote use private holdout export corpus or change actor inputs

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
- do not treat proposal rows as replay evidence

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1468-paper-route-positive-neighborhood-dedup-smoke
- type: infrastructure
- checkpoint: runs/m1468_positive_neighborhood_dedup_smoke/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: positive_neighborhood_dedup_smoke_pass_route_to_preflight_design
- reason: M1468 verifies dedup repair with 192 selected candidates 192 unique keys 0 duplicate rows and source-diverse coverage

## Next Blocker

m1469-paper-route-positive-neighborhood-preflight-design
