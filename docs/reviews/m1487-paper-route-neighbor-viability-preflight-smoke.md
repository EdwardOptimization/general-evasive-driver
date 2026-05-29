# m1487-paper-route-neighbor-viability-preflight-smoke Research Review

## Summary

- Generated at UTC: 20260529T063944Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: neighbor_viability_preflight_pass_route_to_branch_synthesis
- Decision reason: M1487 passes preflight with 96 selected rows 88 neighbor-source rows 5 seeds 6 capability pairs zero clipping and zero duplicate keys

## Hypothesis

M1485 calibrated neighbor-viability candidates will pass geometry preflight without clipping or diversity collapse.

## Lineage

- parent_checkpoint: runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt
- parent_dataset: runs/m1485_neighbor_viability_calibration_proposal_smoke/neighbor_viability_candidate_rows.csv, runs/m1485_neighbor_viability_calibration_proposal_smoke/summary.json, docs/m1486-paper-route-neighbor-viability-preflight-design.md
- parent_config: configs/m1419_warmup_gate_invasiveness_retune_source_wave.json, experiments/manifests/m1486-paper-route-neighbor-viability-preflight-design.json
- parent_objective: run preflight-only validation for M1485 calibrated neighbor-viability candidates
- derived_from: m1486-paper-route-neighbor-viability-preflight-design
- blocked_by: M1485 calibrated neighbor-viability candidates have not yet passed geometry preflight
- supersedes: proposal-only evidence as geometry validation
- invalidates: None

## Success Criteria

- runs/m1487_neighbor_viability_preflight_smoke/summary.json exists
- candidate_step_column == source_step
- geometry_pass_rows >= 64
- selected_candidate_rows >= 64
- selected_diversity.unique_source_seeds >= 3
- selected_diversity.unique_capability_pairs >= 4
- selected_diversity.unique_reveal_buckets >= 3
- relocation_clipped_share <= 0.10
- source_preflight_started true
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
- geometry_pass_rows < 64
- selected_candidate_rows < 64
- run starts replay training PPO promotion private holdout corpus export or actor-input change

## Evidence Gates

- M1487 must run preflight-only with --candidate-step-column source_step
- M1487 must not run replay train PPO promote use private holdout export corpus or change actor inputs
- M1487 must report geometry rows selected rows clipping diversity source_group viability_class and duplicate neighbor viability keys

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not run bounded replay
- do not run outcome interventions
- do not promote
- do not use private holdout
- do not add actor inputs
- do not export corpus
- do not treat preflight result as replay evidence

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1487-paper-route-neighbor-viability-preflight-smoke
- type: infrastructure
- checkpoint: runs/m1487_neighbor_viability_preflight_smoke/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: neighbor_viability_preflight_pass_route_to_branch_synthesis
- reason: M1487 passes preflight with 96 selected rows 88 neighbor-source rows 5 seeds 6 capability pairs zero clipping and zero duplicate keys

## Next Blocker

m1488-paper-route-source-diverse-pressure-validation-synthesis
