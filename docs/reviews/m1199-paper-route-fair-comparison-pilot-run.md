# m1199-paper-route-fair-comparison-pilot-run Research Review

## Summary

- Generated at UTC: 20260528T053827Z
- Type: gate
- Gate tier: infrastructure
- Promotion decision: fair_comparison_pilot_completed_route_to_result_audit
- Decision reason: M1199 completes all 24 fixed public pilot seed runs with finite metrics; L2 finite-window profiles show the strongest public pilot trend while L2 window-equivalence and L3 reset-parity require audit before longer training or stronger claims

## Hypothesis

A fixed-protocol public pilot can produce useful L0/L1/L2/L3 trend evidence without per-profile tuning or claim expansion.

## Lineage

- parent_checkpoint: runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt
- parent_dataset: docs/m1198-paper-route-fair-comparison-pilot-design.md, runs/m1197_profile_training_smoke_stage_b/summary.json, configs/paper_route_profiles
- parent_config: experiments/manifests/m1198-paper-route-fair-comparison-pilot-design.json
- parent_objective: run the first fair public L0/L1/L2/L3 comparison pilot with fixed seeds budgets and claim scope
- derived_from: m1198-paper-route-fair-comparison-pilot-design
- blocked_by: M1198 pre-registers the comparison protocol but no fair multi-seed pilot has run
- supersedes: using M1196 or M1197 smoke metrics as comparison evidence
- invalidates: claiming profile trends without fixed seeds budgets and eval protocol

## Success Criteria

- docs/m1199-paper-route-fair-comparison-pilot-run.md exists
- runs/m1199_fair_comparison_pilot/summary.json exists
- profile_seed_rows.csv exists
- profile_aggregate.csv exists
- all selected profile seed runs complete or failures are recorded
- private holdout remains unused
- no promotion or actor-input contract change occurs
- claims are limited to public pilot trends

## Failure Criteria

- profile-specific budgets or hyperparameters change after seeing results
- private holdout is used
- metrics are framed as paper-level evidence
- hidden or oracle actor inputs are introduced
- failed profiles are omitted from summary

## Evidence Gates

- M1199 may run the public fair comparison pilot only
- M1199 may run PPO under the fixed M1198 profile budgets and seeds
- M1199 must not promote
- M1199 must not use private holdout
- M1199 must not tune profiles based on results
- M1199 must not run candidate replay
- M1199 must not add hidden or oracle actor inputs
- M1199 must not claim paper-level evidence or self-identification

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not change profile-specific budgets
- do not use private holdout
- do not promote any checkpoint
- do not run public proof replay as if this were a driver candidate
- do not tune hyperparameters after seeing profile results
- do not add hidden or oracle actor inputs
- do not claim recurrent-belief advantage or self-identification

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1199-paper-route-fair-comparison-pilot-run
- type: gate
- checkpoint: runs/m1199_fair_comparison_pilot/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: fair_comparison_pilot_completed_route_to_result_audit
- reason: M1199 completes all 24 fixed public pilot seed runs with finite metrics; L2 finite-window profiles show the strongest public pilot trend while L2 window-equivalence and L3 reset-parity require audit before longer training or stronger claims

## Next Blocker

m1200-paper-route-fair-comparison-pilot-result-audit
