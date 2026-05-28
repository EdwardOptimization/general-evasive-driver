# m1231-paper-route-short-horizon-partial-positive-audit Research Review

## Summary

- Generated at UTC: 20260528T081637Z
- Type: gate
- Gate tier: process
- Promotion decision: short_horizon_partial_positive_pivot_to_extreme_fault_source_generation
- Decision reason: M1231 classifies M1230 as real but source-collapsed short-horizon materialization and pivots to extreme fault source-generation design before any training or public-pool grid tuning

## Hypothesis

M1230 is a useful partial positive signal but is too source-collapsed for proof or training, so the next step should expand or re-mine source diversity rather than train.

## Lineage

- parent_checkpoint: runs/m1212_corrected_profile_repeat/profile_runs/L3_online_gru/seed_111602/checkpoint.pt
- parent_dataset: runs/m1230_short_horizon_relocation_smoke/summary.json, runs/m1230_short_horizon_relocation_smoke/balanced_accepted_wrong_history_rows.csv, docs/m1230-paper-route-short-horizon-relocation-smoke.md
- parent_config: experiments/manifests/m1230-paper-route-short-horizon-relocation-smoke.json, configs/paper_route_corrected_profiles/m1207_l3_online_gru.json
- parent_objective: audit partial short-horizon materialization signal and select next source-diversity route
- derived_from: m1230-paper-route-short-horizon-relocation-smoke
- blocked_by: M1230 accepted rows collapse to one target, two left steps, one checkpoint, and one margin bucket
- supersedes: training directly from M1230 accepted rows
- invalidates: claiming M1230 as source-diverse proof

## Success Criteria

- docs/m1231-paper-route-short-horizon-partial-positive-audit.md exists
- M1230 source-collapse pattern is classified
- next expansion or pivot route is selected
- private holdout remains unused
- no training, PPO, promotion, private holdout, profile tuning, or actor-input contract expansion occurs

## Failure Criteria

- M1231 trains or tunes profiles
- private holdout is used
- M1230 is claimed as a proof pass
- source-collapse gates are weakened
- next route is left vague

## Evidence Gates

- M1231 must audit M1230 before any new training or relocation expansion
- M1231 must preserve actor input contract
- M1231 must not train controllers
- M1231 must not run PPO
- M1231 must not use private holdout
- M1231 must not promote
- M1231 must classify the source-collapse pattern and select a concrete next route
- M1231 must not claim self-identification

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not use private holdout
- do not promote
- do not add hidden or oracle actor inputs
- do not use M1230 as a proof pass
- do not claim long-horizon performance from M1230

## Failure Taxonomy

- scenario_sampling_failure

## Scoreboard

- milestone: m1231-paper-route-short-horizon-partial-positive-audit
- type: gate
- checkpoint: docs/m1231-paper-route-short-horizon-partial-positive-audit.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: short_horizon_partial_positive_pivot_to_extreme_fault_source_generation
- reason: M1231 classifies M1230 as real but source-collapsed short-horizon materialization and pivots to extreme fault source-generation design before any training or public-pool grid tuning

## Next Blocker

m1232-paper-route-extreme-fault-source-generation-design
