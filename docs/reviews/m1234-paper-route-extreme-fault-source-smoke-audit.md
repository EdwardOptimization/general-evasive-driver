# m1234-paper-route-extreme-fault-source-smoke-audit Research Review

## Summary

- Generated at UTC: 20260528T083001Z
- Type: gate
- Gate tier: process
- Promotion decision: extreme_fault_source_smoke_audit_route_to_timing_repair_design
- Decision reason: M1234 audits M1233 as infrastructure pass but cross-fault wrong-history negative with normal-failure-dominated reset-only source shape and routes to timing/horizon normal-survival repair design

## Hypothesis

M1233 should be treated as an infrastructure pass but a cross-fault wrong-history negative result; an audit can decide whether the next route is timing repair, sequence intervention, or larger source mining.

## Lineage

- parent_checkpoint: runs/m1212_corrected_profile_repeat/profile_runs/L3_online_gru/seed_111602/checkpoint.pt
- parent_dataset: runs/m1233_paper_route_extreme_fault_source_smoke/summary.json, runs/m1233_paper_route_extreme_fault_source_smoke/matched_cross_fault_pairs.csv, runs/m1233_paper_route_extreme_fault_source_smoke/reset_only_rows.csv, runs/m1233_paper_route_extreme_fault_source_smoke/rejected_rows.csv
- parent_config: experiments/manifests/m1233-paper-route-extreme-fault-source-smoke.json, configs/m990_capability_step_fault_scenarios.json
- parent_objective: audit M1233 cross-fault reset-only source shape before any larger source wave or training
- derived_from: m1233-paper-route-extreme-fault-source-smoke
- blocked_by: M1233 produced zero wrong-history accepted rows and reset-only rows concentrated in two seeds
- supersedes: directly scaling or training from M1233 reset-only rows
- invalidates: claiming M1233 as cross-fault wrong-history proof

## Success Criteria

- docs/m1234-paper-route-extreme-fault-source-smoke-audit.md exists
- M1233 cross-fault wrong-history result is classified
- M1233 reset-only and normal-failed patterns are classified
- next route is selected
- private holdout remains unused
- no training, PPO, promotion, private holdout, profile tuning, or actor-input contract expansion occurs

## Failure Criteria

- M1234 trains or tunes profiles
- private holdout is used
- M1233 is claimed as self-ID proof
- reset-only rows are counted as wrong-history positives
- next route is left vague

## Evidence Gates

- M1234 must audit M1233 before any training or larger source wave
- M1234 must preserve actor input contract
- M1234 must not train controllers
- M1234 must not run PPO
- M1234 must not use private holdout
- M1234 must not promote
- M1234 must not count reset-only rows as self-identification proof
- M1234 must select a concrete next route

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not use private holdout
- do not promote
- do not add hidden or oracle actor inputs
- do not claim wrong-history proof from zero accepted rows
- do not claim true per-wheel or asymmetric fault physics

## Failure Taxonomy

- scenario_sampling_failure

## Scoreboard

- milestone: m1234-paper-route-extreme-fault-source-smoke-audit
- type: gate
- checkpoint: docs/m1234-paper-route-extreme-fault-source-smoke-audit.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: extreme_fault_source_smoke_audit_route_to_timing_repair_design
- reason: M1234 audits M1233 as infrastructure pass but cross-fault wrong-history negative with normal-failure-dominated reset-only source shape and routes to timing/horizon normal-survival repair design

## Next Blocker

m1235-paper-route-extreme-fault-timing-repair-design
