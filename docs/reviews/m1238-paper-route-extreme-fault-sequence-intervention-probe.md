# m1238-paper-route-extreme-fault-sequence-intervention-probe Research Review

## Summary

- Generated at UTC: 20260528T084531Z
- Type: gate
- Gate tier: generalization
- Promotion decision: extreme_fault_sequence_probe_no_signal_route_to_negative_audit
- Decision reason: M1238 probe is valid with 384 source rows 6912 intervention rows and 6 variants but result is sequence_no_signal with zero accepted sequence rows and zero action-critical rows

## Hypothesis

Sequence-level command-response interventions over M1236 normal-surviving rows will expose stronger temporal-history dependence than single hidden-state swaps.

## Lineage

- parent_checkpoint: runs/m1212_corrected_profile_repeat/profile_runs/L3_online_gru/seed_111602/checkpoint.pt
- parent_dataset: runs/m1236_extreme_fault_timing_repair_smoke/rejected_rows.csv, docs/m1237-paper-route-extreme-fault-sequence-intervention-design.md
- parent_config: experiments/manifests/m1237-paper-route-extreme-fault-sequence-intervention-design.json, configs/m1236_extreme_fault_timing_repair_smoke.json
- parent_objective: run no-training sequence-level command-response interventions over M1236 normal-surviving rows
- derived_from: m1237-paper-route-extreme-fault-sequence-intervention-design
- blocked_by: M1236 single hidden-state swaps are history-insensitive
- supersedes: continuing single hidden-swap tuning on M1236
- invalidates: None

## Success Criteria

- runs/m1238_extreme_fault_sequence_intervention_probe/summary.json exists
- selected_source_rows > 0
- intervention_rows > 0
- variant_count >= 6
- normal_failed_rows < intervention_rows
- actor_parameters_changed == false
- training_started == false
- ppo_used == false
- promoted == false
- private holdout remains unused
- no actor-input contract expansion occurs

## Failure Criteria

- trace reconstruction fails for all rows
- normal-failed rows dominate all interventions
- actor parameters change
- hidden fault/event labels enter actor observations
- training or PPO starts
- promotion occurs

## Evidence Gates

- M1238 must preserve actor input contract
- M1238 must not train controllers
- M1238 must not run PPO
- M1238 must not use private holdout
- M1238 must not promote
- M1238 must report normal, cross-fault, temporal, reset/warm, zero-command, action-only, and normal-failed outcomes separately
- M1238 must not claim self-identification without a separate audit

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not use private holdout
- do not promote
- do not add hidden fault labels or hidden parameters to actor inputs
- do not count temporal-only positives as cross-fault positives
- do not count action-only rows as outcome evidence
- do not claim true per-wheel or asymmetric fault physics

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1238-paper-route-extreme-fault-sequence-intervention-probe
- type: gate
- checkpoint: runs/m1238_extreme_fault_sequence_intervention_probe/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: extreme_fault_sequence_probe_no_signal_route_to_negative_audit
- reason: M1238 probe is valid with 384 source rows 6912 intervention rows and 6 variants but result is sequence_no_signal with zero accepted sequence rows and zero action-critical rows

## Next Blocker

m1239-paper-route-extreme-fault-sequence-negative-audit
