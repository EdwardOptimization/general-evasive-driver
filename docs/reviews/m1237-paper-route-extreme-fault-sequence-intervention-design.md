# m1237-paper-route-extreme-fault-sequence-intervention-design Research Review

## Summary

- Generated at UTC: 20260528T084046Z
- Type: gate
- Gate tier: process
- Promotion decision: extreme_fault_sequence_intervention_design_admit_probe
- Decision reason: M1237 designs bounded no-training delayed cross-fault command-response mismatch sequence intervention over M1236 normal-surviving history-insensitive rows and admits M1238 probe

## Hypothesis

M1236 normal-surviving but history-insensitive rows are better tested by sequence-level command-response interventions than by further single hidden-state swaps.

## Lineage

- parent_checkpoint: runs/m1212_corrected_profile_repeat/profile_runs/L3_online_gru/seed_111602/checkpoint.pt
- parent_dataset: runs/m1236_extreme_fault_timing_repair_smoke/summary.json, runs/m1236_extreme_fault_timing_repair_smoke/rejected_rows.csv, docs/m1236-paper-route-extreme-fault-timing-repair-smoke.md
- parent_config: experiments/manifests/m1236-paper-route-extreme-fault-timing-repair-smoke.json, configs/m1236_extreme_fault_timing_repair_smoke.json
- parent_objective: design sequence-level temporal intervention probe over M1236 normal-surviving rows
- derived_from: m1236-paper-route-extreme-fault-timing-repair-smoke
- blocked_by: M1236 repairs normal survival but single cross-fault hidden swaps remain history-insensitive
- supersedes: more single hidden-swap tuning on M1236
- invalidates: training from M1236 because normal survival alone is not self-ID evidence

## Success Criteria

- docs/m1237-paper-route-extreme-fault-sequence-intervention-design.md exists
- source-row filtering rule is specified
- sequence intervention variants are specified
- first bounded probe command is specified
- private holdout remains unused
- no training, PPO, promotion, private holdout, profile tuning, or actor-input contract expansion occurs

## Failure Criteria

- M1237 trains or tunes profiles
- private holdout is used
- design depends on hidden labels as actor inputs
- normal-surviving rows are treated as self-ID evidence
- next route is left vague

## Evidence Gates

- M1237 may design sequence intervention only
- M1237 must preserve actor input contract
- M1237 must not train controllers
- M1237 must not run PPO
- M1237 must not use private holdout
- M1237 must not promote
- M1237 must distinguish cross-fault sequence evidence from temporal/reset variants
- M1237 must select a bounded first implementation step

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not use private holdout
- do not promote
- do not add hidden fault labels or hidden parameters to actor inputs
- do not count normal-survival repair as self-ID evidence
- do not count reset-only rows as wrong-history positives
- do not claim true per-wheel or asymmetric fault physics

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1237-paper-route-extreme-fault-sequence-intervention-design
- type: gate
- checkpoint: docs/m1237-paper-route-extreme-fault-sequence-intervention-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: extreme_fault_sequence_intervention_design_admit_probe
- reason: M1237 designs bounded no-training delayed cross-fault command-response mismatch sequence intervention over M1236 normal-surviving history-insensitive rows and admits M1238 probe

## Next Blocker

m1238-paper-route-extreme-fault-sequence-intervention-probe
