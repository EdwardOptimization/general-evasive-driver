# m1236-paper-route-extreme-fault-timing-repair-smoke Research Review

## Summary

- Generated at UTC: 20260528T083748Z
- Type: gate
- Gate tier: infrastructure
- Promotion decision: extreme_fault_timing_repair_pass_route_to_sequence_intervention_design
- Decision reason: M1236 passes timing repair with normal_surviving_fraction 0.7213541667 but single hidden-swap interventions remain history_insensitive_too_mild with 0 accepted and 0 reset-only rows

## Hypothesis

Reducing continuation horizon and widening the earlier obstacle source window will improve normal-history survivability enough to make later fault-source intervention tests interpretable.

## Lineage

- parent_checkpoint: runs/m1212_corrected_profile_repeat/profile_runs/L3_online_gru/seed_111602/checkpoint.pt
- parent_dataset: runs/m1233_paper_route_extreme_fault_source_smoke/summary.json, docs/m1235-paper-route-extreme-fault-timing-repair-design.md
- parent_config: experiments/manifests/m1235-paper-route-extreme-fault-timing-repair-design.json, configs/m990_capability_step_fault_scenarios.json
- parent_objective: run bounded normal-survival-first timing repair smoke for extreme/fault source generation
- derived_from: m1235-paper-route-extreme-fault-timing-repair-design
- blocked_by: M1233 normal-surviving fraction is only 0.171875
- supersedes: scaling M1233 without normal-survival repair
- invalidates: None

## Success Criteria

- configs/m1236_extreme_fault_timing_repair_smoke.json exists
- runs/m1236_extreme_fault_timing_repair_smoke/summary.json exists
- scenario_count > 0
- snapshot_count > 0
- matched_pair_count > 0
- matched fault-family pairs >= 10
- matched seeds >= 12
- normal_surviving_fraction >= 0.35
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
- normal_surviving_fraction remains below 0.35
- actor parameters change
- hidden fault/event labels enter actor observations
- model fidelity boundary is missing
- training or PPO starts
- promotion occurs

## Evidence Gates

- M1236 must preserve actor input contract
- M1236 must keep hidden fault labels as logging/pairing metadata only
- M1236 must write model fidelity limits
- M1236 must not train controllers
- M1236 must not run PPO
- M1236 must not use private holdout
- M1236 must not promote
- M1236 must evaluate normal-survival before accepted-row claims

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not use private holdout
- do not promote
- do not add fault labels or hidden parameters to actor inputs
- do not claim reset-only rows as self-identification proof
- do not claim true per-wheel or asymmetric fault physics

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1236-paper-route-extreme-fault-timing-repair-smoke
- type: gate
- checkpoint: runs/m1236_extreme_fault_timing_repair_smoke/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: extreme_fault_timing_repair_pass_route_to_sequence_intervention_design
- reason: M1236 passes timing repair with normal_surviving_fraction 0.7213541667 but single hidden-swap interventions remain history_insensitive_too_mild with 0 accepted and 0 reset-only rows

## Next Blocker

m1237-paper-route-extreme-fault-sequence-intervention-design
