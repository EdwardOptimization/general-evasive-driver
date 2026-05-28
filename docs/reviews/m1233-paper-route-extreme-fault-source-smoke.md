# m1233-paper-route-extreme-fault-source-smoke Research Review

## Summary

- Generated at UTC: 20260528T082735Z
- Type: gate
- Gate tier: infrastructure
- Promotion decision: extreme_fault_source_smoke_reset_only_route_to_audit
- Decision reason: M1233 passes infrastructure smoke with 832 scenarios 3211 snapshots and 768 matched pairs but produces 0 wrong-history accepted rows and 58 reset-only rows so audit is required before scaling or training

## Hypothesis

The current paper-route L3 checkpoint can be smoke-run through the existing hidden capability-step/fault source generator while preserving the actor contract and producing matched cross-fault artifacts.

## Lineage

- parent_checkpoint: runs/m1212_corrected_profile_repeat/profile_runs/L3_online_gru/seed_111602/checkpoint.pt
- parent_dataset: docs/m1232-paper-route-extreme-fault-source-generation-design.md
- parent_config: experiments/manifests/m1232-paper-route-extreme-fault-source-generation-design.json, configs/m990_capability_step_fault_scenarios.json, src/autodrift/extreme_dynamics_scenario_corpus.py
- parent_objective: smoke current paper-route L3 checkpoint through existing hidden capability-step/fault source generator
- derived_from: m1232-paper-route-extreme-fault-source-generation-design
- blocked_by: M1232 admits only a bounded no-training smoke before larger source mining or training
- supersedes: continuing to grid-tune the M1226/M1230 source-collapsed public pool
- invalidates: None

## Success Criteria

- runs/m1233_paper_route_extreme_fault_source_smoke/summary.json exists
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
- private holdout remains unused
- no actor-input contract expansion occurs

## Failure Criteria

- checkpoint/config observation compatibility fails
- no snapshots or matched pairs are produced
- actor parameters change
- hidden fault/event labels enter actor observations
- model fidelity boundary is missing
- training or PPO starts
- promotion occurs

## Evidence Gates

- M1233 must preserve actor input contract
- M1233 must keep hidden fault labels as logging/pairing metadata only
- M1233 must write model fidelity limits
- M1233 must not train controllers
- M1233 must not run PPO
- M1233 must not use private holdout
- M1233 must not promote
- M1233 must not require accepted rows at smoke scale

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not use private holdout
- do not promote
- do not add fault labels or hidden parameters to actor inputs
- do not claim true per-wheel or asymmetric fault physics
- do not claim self-identification from smoke artifacts

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1233-paper-route-extreme-fault-source-smoke
- type: gate
- checkpoint: runs/m1233_paper_route_extreme_fault_source_smoke/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: extreme_fault_source_smoke_reset_only_route_to_audit
- reason: M1233 passes infrastructure smoke with 832 scenarios 3211 snapshots and 768 matched pairs but produces 0 wrong-history accepted rows and 58 reset-only rows so audit is required before scaling or training

## Next Blocker

m1234-paper-route-extreme-fault-source-smoke-audit
