# m1435-paper-route-geometry-aware-preflight-smoke Research Review

## Summary

- Generated at UTC: 20260529T030633Z
- Type: infrastructure
- Gate tier: proof
- Promotion decision: geometry_aware_preflight_no_forward_rows_route_to_audit
- Decision reason: M1435 preflight-only run found 0 geometry-pass and 0 selected rows across 846 M1425 pressure rows with source_body_x max 3.908 so route to audit

## Hypothesis

The M1425 pressure rows contain enough forward unclipped source-diverse geometry to justify a later bounded relocation replay design.

## Lineage

- parent_checkpoint: runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt
- parent_dataset: runs/m1425_action_divergent_outcome_pressure_source_smoke/outcome_pressure_rows.csv, docs/m1434-paper-route-geometry-preflight-only-command-implementation.md
- parent_config: configs/m1419_warmup_gate_invasiveness_retune_source_wave.json, experiments/manifests/m1434-paper-route-geometry-preflight-only-command-implementation.json
- parent_objective: run public geometry-aware preflight-only smoke before bounded replay
- derived_from: m1434-paper-route-geometry-preflight-only-command-implementation
- blocked_by: M1434 implemented preflight-only command but source viability has not been measured
- supersedes: running bounded replay before geometry-aware preflight smoke
- invalidates: None

## Success Criteria

- runs/m1435_geometry_aware_preflight_smoke/summary.json exists
- geometry_pass_rows >= 64
- selected_candidate_rows >= 64
- selected_diversity.unique_source_seeds >= 6
- selected_diversity.unique_capability_pairs >= 8
- selected_diversity.unique_reveal_buckets >= 6
- selected_diversity.unique_variants >= 2
- selected_diversity.max_single_seed_share <= 0.35
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
- geometry or diversity gates fail
- preflight rows are counted as replay evidence
- run starts replay training PPO promotion private holdout corpus export or actor-input changes

## Evidence Gates

- M1435 must run --preflight-only on public M1425 rows
- M1435 must report forward geometry rows selected rows clipping share and source diversity
- M1435 must not run bounded replay train PPO promote use private holdout export corpus or change actor inputs
- M1435 must route to audit if geometry/source gates fail

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
- do not lower geometry gates after seeing the result
- do not count preflight rows as actual replay or history-positive evidence

## Failure Taxonomy

- scenario_sampling_failure

## Scoreboard

- milestone: m1435-paper-route-geometry-aware-preflight-smoke
- type: infrastructure
- checkpoint: runs/m1435_geometry_aware_preflight_smoke/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: geometry_aware_preflight_no_forward_rows_route_to_audit
- reason: M1435 preflight-only run found 0 geometry-pass and 0 selected rows across 846 M1425 pressure rows with source_body_x max 3.908 so route to audit

## Next Blocker

m1436-paper-route-geometry-preflight-result-audit
