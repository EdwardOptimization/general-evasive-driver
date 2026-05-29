# m1465-paper-route-positive-neighborhood-expansion-smoke Research Review

## Summary

- Generated at UTC: 20260529T050846Z
- Type: infrastructure
- Gate tier: proof
- Promotion decision: positive_neighborhood_expansion_smoke_counts_pass_duplicate_key_repair_required
- Decision reason: M1465 produces 24960 proposals and 192 selected candidates but selected count is inflated by 172 duplicate positive_neighborhood_key rows

## Hypothesis

The M1464 generator can expand M1461's live singleton boundary into a source-step anchored candidate pool with controls separated.

## Lineage

- parent_checkpoint: runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt
- parent_dataset: runs/m1461_retargeted_source_step_bounded_replay_smoke/history_positive_rows.csv, runs/m1461_retargeted_source_step_bounded_replay_smoke/control_positive_rows.csv, runs/m1459_retargeted_source_step_preflight_smoke/selected_candidate_rows.csv, docs/m1464-paper-route-positive-neighborhood-expansion-implementation.md
- parent_config: experiments/manifests/m1464-paper-route-positive-neighborhood-expansion-implementation.json
- parent_objective: run positive-neighborhood expansion proposal generator
- derived_from: m1464-paper-route-positive-neighborhood-expansion-implementation
- blocked_by: positive-neighborhood expansion generator has not yet been run
- supersedes: manual expansion of M1461 singleton positive rows
- invalidates: None

## Success Criteria

- runs/m1465_positive_neighborhood_expansion_smoke/summary.json exists
- proposal_rows >= 64
- selected_candidate_rows >= 64
- selected_diversity.unique_source_seeds >= 2
- selected_diversity.unique_capability_pairs >= 2
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
- selected candidate rows are sparse or singleton
- candidate_step_column is not source_step
- run starts preflight replay training PPO promotion private holdout corpus export or actor-input change

## Evidence Gates

- M1465 must run proposal generation only
- M1465 must preserve source_step and keep zero-current controls separate
- M1465 must not run preflight replay train PPO promote use private holdout export corpus or change actor inputs
- M1465 must report proposal rows selected rows source groups and diversity

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

- metric_artifact

## Scoreboard

- milestone: m1465-paper-route-positive-neighborhood-expansion-smoke
- type: infrastructure
- checkpoint: runs/m1465_positive_neighborhood_expansion_smoke/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: positive_neighborhood_expansion_smoke_counts_pass_duplicate_key_repair_required
- reason: M1465 produces 24960 proposals and 192 selected candidates but selected count is inflated by 172 duplicate positive_neighborhood_key rows

## Next Blocker

m1466-paper-route-boundary-retarget-validation-synthesis
