# m990-v4-public-base-capability-step-fault-smoke Research Review

## Summary

- Generated at UTC: 20260526T131203Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: capability_step_fault_smoke_pass_route_to_source_wave
- Decision reason: M990 smoke passes with 768 matched pairs 2 accepted wrong-history rows and 132 reset-only rows; signal is nonzero but source-narrow

## Hypothesis

The existing fault-event corpus harness can be run against the M974 public-gate base with a small current-base capability-step config while preserving the P0 actor contract.

## Lineage

- parent_checkpoint: runs/m974_exact_repair_from_base_s40_seed5974/candidate_checkpoint.pt
- parent_dataset: docs/m989-v4-public-base-capability-step-fault-design.md
- parent_config: experiments/manifests/m989-v4-public-base-capability-step-fault-design.json, src/autodrift/extreme_dynamics_scenario_corpus.py, configs/extreme_fault_distribution_v4_scenarios.json
- parent_objective: validate current-base compatibility for hidden capability-step fault-event source mining
- derived_from: m989-v4-public-base-capability-step-fault-design, m988-v4-public-base-extreme-scenario-family-synthesis
- blocked_by: M989 admits only a small no-training smoke before source mining or training
- supersedes: None
- invalidates: None

## Success Criteria

- configs/m990_capability_step_fault_scenarios.json exists
- summary.json exists
- scenario_count > 0
- snapshot_count > 0
- matched_pair_count > 0
- scenario_summary.csv exists
- matched_cross_fault_pairs.csv exists
- intervention_rollouts.csv exists
- model_fidelity_limits.md exists
- actor_parameters_changed == false
- training_started == false
- ppo_used == false
- promoted == false

## Failure Criteria

- checkpoint/config observation compatibility fails
- no snapshots or matched pairs are produced
- actor parameters change
- hidden fault/event labels enter actor observations
- model fidelity boundary is missing
- training or PPO starts
- promotion occurs

## Evidence Gates

- M990 must not run PPO
- M990 must not promote
- M990 must not change actor inputs
- M990 must keep hidden fault labels as logging/pairing metadata only
- M990 must report model fidelity limits
- M990 must not require accepted rows at smoke scale

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not add hidden event labels to actor observations
- do not train or optimize
- do not use private holdout
- do not claim true per-wheel/asymmetric faults
- do not promote any checkpoint

## Failure Taxonomy

- none

## Scoreboard

- milestone: m990-v4-public-base-capability-step-fault-smoke
- type: infrastructure
- checkpoint: runs/m990_v4_public_base_capability_step_fault_smoke/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: capability_step_fault_smoke_pass_route_to_source_wave
- reason: M990 smoke passes with 768 matched pairs 2 accepted wrong-history rows and 132 reset-only rows; signal is nonzero but source-narrow

## Next Blocker

m991-v4-public-base-capability-step-fault-source-wave
