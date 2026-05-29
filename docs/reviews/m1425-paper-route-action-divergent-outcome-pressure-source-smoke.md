# m1425-paper-route-action-divergent-outcome-pressure-source-smoke Research Review

## Summary

- Generated at UTC: 20260529T021038Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: action_divergent_outcome_pressure_proxy_no_history_positive_route_to_audit
- Decision reason: M1425 finds 256 candidates and 846 proxy pressure rows but 0 history-positive rows so replay and training remain blocked pending audit

## Hypothesis

The M1424 constructor can find enough source-diverse action-divergent proxy pressure rows in M1421 public outcome artifacts to justify a later replay probe.

## Lineage

- parent_checkpoint: runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt
- parent_dataset: runs/m1421_m1419_source_collision_stratified_outcome_probe/outcome_rows.csv, docs/m1424-paper-route-action-divergent-outcome-pressure-source-implementation.md
- parent_config: experiments/manifests/m1424-paper-route-action-divergent-outcome-pressure-source-implementation.json
- parent_objective: run no-training constructor source smoke on M1421 outcome rows
- derived_from: m1424-paper-route-action-divergent-outcome-pressure-source-implementation
- blocked_by: M1424 implementation must be run on public M1421 rows before any closed-loop replay probe
- supersedes: manual selection of action-critical rows, training directly from M1421 rows
- invalidates: None

## Success Criteria

- runs/m1425_action_divergent_outcome_pressure_source_smoke/summary.json exists
- candidate_rows >= 128
- outcome_pressure_rows >= 32
- history_positive_rows >= 16
- history_positive_unique_source_seeds >= 6
- history_positive_unique_capability_pairs >= 6
- history_positive_unique_reveal_buckets >= 4
- summary marks proxy_only true and requires_replay true
- training_started false
- ppo_used false
- promoted false
- private_holdout_used false
- training_corpus_exported false
- actor_input_contract_changed false

## Failure Criteria

- summary is missing
- candidate rows or pressure rows are sparse
- history-positive rows are control-only or not source-diverse
- outputs are not marked proxy_only and requires_replay
- run starts closed-loop replay training PPO promotion private holdout corpus export or actor-input changes

## Evidence Gates

- M1425 must use the M1424 constructor on public M1421 outcome rows only
- M1425 must report candidate_rows outcome_pressure_rows and history_positive proxy rows separately
- M1425 must keep proxy_only and requires_replay flags explicit
- M1425 must not run closed-loop replay outcome interventions train run PPO promote use private holdout export training corpus or change actor inputs

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
- do not export a training corpus
- do not count reset or zero-current as history-positive
- do not claim proxy rows as closed-loop evidence

## Failure Taxonomy

- scenario_sampling_failure

## Scoreboard

- milestone: m1425-paper-route-action-divergent-outcome-pressure-source-smoke
- type: infrastructure
- checkpoint: runs/m1425_action_divergent_outcome_pressure_source_smoke/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: action_divergent_outcome_pressure_proxy_no_history_positive_route_to_audit
- reason: M1425 finds 256 candidates and 846 proxy pressure rows but 0 history-positive rows so replay and training remain blocked pending audit

## Next Blocker

m1426-paper-route-action-divergent-pressure-result-audit
