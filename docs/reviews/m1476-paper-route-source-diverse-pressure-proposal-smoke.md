# m1476-paper-route-source-diverse-pressure-proposal-smoke Research Review

## Summary

- Generated at UTC: 20260529T053947Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: source_diverse_pressure_proposal_smoke_pass_route_to_branch_synthesis
- Decision reason: M1476 proposal smoke selected 120 source-diverse candidates including 96 neighbor-source rows across 5 seeds and 7 capability pairs with zero duplicate pressure keys

## Hypothesis

The source-diverse pressure generator can produce a source-diverse candidate pool from M1472 artifacts without replay or training.

## Lineage

- parent_checkpoint: runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt
- parent_dataset: runs/m1472_positive_neighborhood_bounded_replay_smoke/actual_replay_rows.csv, runs/m1472_positive_neighborhood_bounded_replay_smoke/history_positive_rows.csv, runs/m1472_positive_neighborhood_bounded_replay_smoke/control_positive_rows.csv, runs/m1470_positive_neighborhood_preflight_smoke/selected_candidate_rows.csv, docs/m1475-paper-route-source-diverse-pressure-implementation.md
- parent_config: experiments/manifests/m1475-paper-route-source-diverse-pressure-implementation.json
- parent_objective: run source-diverse pressure proposal smoke without preflight or replay
- derived_from: m1475-paper-route-source-diverse-pressure-implementation
- blocked_by: source-diverse pressure generator has not yet been run on M1472 artifacts
- supersedes: implementation-only evidence as proposal-count evidence
- invalidates: None

## Success Criteria

- runs/m1476_source_diverse_pressure_proposal_smoke/summary.json exists
- selected_candidate_rows >= 32
- selected_source_group_counts.neighbor_source > 0
- selected_duplicate_pressure_key_rows == 0
- candidate_step_column == source_step
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
- selected_candidate_rows < 32
- neighbor source candidates are missing
- duplicate pressure keys remain
- run starts preflight replay training PPO promotion private holdout corpus export or actor-input change

## Evidence Gates

- M1476 must run proposal generation only
- M1476 must not run preflight replay train PPO promote use private holdout export corpus or change actor inputs
- M1476 must report selected rows source-group counts source diversity duplicate pressure keys and guardrails

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
- do not treat proposal counts as replay evidence

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1476-paper-route-source-diverse-pressure-proposal-smoke
- type: infrastructure
- checkpoint: runs/m1476_source_diverse_pressure_proposal_smoke/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: source_diverse_pressure_proposal_smoke_pass_route_to_branch_synthesis
- reason: M1476 proposal smoke selected 120 source-diverse candidates including 96 neighbor-source rows across 5 seeds and 7 capability pairs with zero duplicate pressure keys

## Next Blocker

m1477-paper-route-boundary-retarget-validation-synthesis
