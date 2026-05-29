# m1448-paper-route-source-step-preflight-smoke Research Review

## Summary

- Generated at UTC: 20260529T041837Z
- Type: infrastructure
- Gate tier: proof
- Promotion decision: source_step_preflight_schema_failure_route_to_margin_gap_optional_repair
- Decision reason: M1448 failed before source preflight because M1445 candidate rows lack margin_gap; no replay training promotion or actor-input changes occurred

## Hypothesis

M1445 selected candidates remain forward, unclipped, source-diverse when preflight reconstructs the trace at source_step.

## Lineage

- parent_checkpoint: runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt
- parent_dataset: runs/m1445_forward_geometry_source_miner_smoke/selected_candidate_rows.csv, docs/m1447-paper-route-source-step-preflight-support-implementation.md
- parent_config: configs/m1419_warmup_gate_invasiveness_retune_source_wave.json, experiments/manifests/m1447-paper-route-source-step-preflight-support-implementation.json
- parent_objective: run source-step-aware preflight-only smoke on M1445 selected candidate rows
- derived_from: m1447-paper-route-source-step-preflight-support-implementation
- blocked_by: source-step preflight support is implemented but M1445 selected rows have not been preflighted at source_step
- supersedes: running reveal-step preflight on M1445 source-step candidates
- invalidates: None

## Success Criteria

- runs/m1448_source_step_preflight_smoke/summary.json exists
- summary candidate_step_column equals source_step
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
- candidate_step_column is not source_step
- geometry or diversity gates fail
- preflight rows are counted as replay evidence
- run starts replay training PPO promotion private holdout corpus export or actor-input change

## Evidence Gates

- M1448 must run --preflight-only with --candidate-step-column source_step
- M1448 must not run bounded replay train PPO promote use private holdout export corpus or change actor inputs
- M1448 must report source-step preflight rows selected rows clipping share and diversity

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

- lineage_invalid

## Scoreboard

- milestone: m1448-paper-route-source-step-preflight-smoke
- type: infrastructure
- checkpoint: docs/m1448-paper-route-source-step-preflight-smoke.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: source_step_preflight_schema_failure_route_to_margin_gap_optional_repair
- reason: M1448 failed before source preflight because M1445 candidate rows lack margin_gap; no replay training promotion or actor-input changes occurred

## Next Blocker

m1449-paper-route-source-step-preflight-schema-repair-implementation
