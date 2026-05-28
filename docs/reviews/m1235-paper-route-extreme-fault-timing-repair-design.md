# m1235-paper-route-extreme-fault-timing-repair-design Research Review

## Summary

- Generated at UTC: 20260528T083240Z
- Type: gate
- Gate tier: process
- Promotion decision: extreme_fault_timing_repair_design_admit_smoke
- Decision reason: M1235 designs normal-survival-first timing horizon source-window repair with target normal_surviving_fraction >= 0.35 and admits bounded no-training M1236 smoke

## Hypothesis

A normal-survival-first timing/horizon repair is higher leverage than scaling M1233 because most rejected source rows fail under normal history.

## Lineage

- parent_checkpoint: runs/m1212_corrected_profile_repeat/profile_runs/L3_online_gru/seed_111602/checkpoint.pt
- parent_dataset: runs/m1233_paper_route_extreme_fault_source_smoke/summary.json, docs/m1234-paper-route-extreme-fault-source-smoke-audit.md
- parent_config: experiments/manifests/m1234-paper-route-extreme-fault-source-smoke-audit.json, configs/m990_capability_step_fault_scenarios.json
- parent_objective: design timing/horizon/normal-success repair for extreme/fault source generation
- derived_from: m1234-paper-route-extreme-fault-source-smoke-audit
- blocked_by: M1233 rejected rows are dominated by normal_failed_rejected, M1233 reset-only rows are seed-collapsed and cannot be used as proof
- supersedes: directly scaling the current M1233 smoke config
- invalidates: training from reset-only M1233 rows

## Success Criteria

- docs/m1235-paper-route-extreme-fault-timing-repair-design.md exists
- normal-survival repair levers are specified
- source-shape gates are specified
- first bounded repair implementation step is selected
- private holdout remains unused
- no training, PPO, promotion, private holdout, profile tuning, or actor-input contract expansion occurs

## Failure Criteria

- M1235 trains or tunes profiles
- private holdout is used
- repair design depends on hidden labels as actor inputs
- normal-survival gates are left vague
- next route is left vague

## Evidence Gates

- M1235 may design source timing repair only
- M1235 must preserve actor input contract
- M1235 must not train controllers
- M1235 must not run PPO
- M1235 must not use private holdout
- M1235 must not promote
- M1235 must define normal-survival gates before accepted-row gates
- M1235 must select a bounded first repair implementation step

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not use private holdout
- do not promote
- do not add hidden fault labels or hidden parameters to actor inputs
- do not weaken proof thresholds to count reset-only rows as positives
- do not claim true per-wheel or asymmetric fault physics

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1235-paper-route-extreme-fault-timing-repair-design
- type: gate
- checkpoint: docs/m1235-paper-route-extreme-fault-timing-repair-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: extreme_fault_timing_repair_design_admit_smoke
- reason: M1235 designs normal-survival-first timing horizon source-window repair with target normal_surviving_fraction >= 0.35 and admits bounded no-training M1236 smoke

## Next Blocker

m1236-paper-route-extreme-fault-timing-repair-smoke
