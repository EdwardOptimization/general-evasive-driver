# m1212-paper-route-corrected-profile-repeat-run Research Review

## Summary

- Generated at UTC: 20260528T064135Z
- Type: gate
- Gate tier: infrastructure
- Promotion decision: corrected_profile_repeat_completed_route_to_repeat_result_audit
- Decision reason: M1212 completes 24/24 fresh repeat seed runs; L2 current-tiled controls outperform normal L2 and L3 online beats corrected reset in aggregate but L3 family ranking conflicts with M1209 so route to cross-block audit

## Hypothesis

A fresh public seed block can test whether M1209 corrected profile trends are repeatable without private holdout or tuning.

## Lineage

- parent_checkpoint: none
- parent_dataset: docs/m1211-paper-route-corrected-profile-repeat-design.md, configs/paper_route_corrected_profiles
- parent_config: experiments/manifests/m1211-paper-route-corrected-profile-repeat-design.json
- parent_objective: run a fresh public repeat of the corrected profile pilot using fixed new seed and eval blocks
- derived_from: m1211-paper-route-corrected-profile-repeat-design
- blocked_by: M1211 pre-registers the repeat protocol but no fresh repeat has run
- supersedes: deciding from the single M1209 seed block
- invalidates: claiming stable L3 or L2 trends without fresh public repeat

## Success Criteria

- docs/m1212-paper-route-corrected-profile-repeat-run.md exists
- runs/m1212_corrected_profile_repeat/summary.json exists
- profile_seed_rows.csv exists
- eval_rows.csv exists
- profile_aggregate.csv exists
- all selected profile seed runs complete or failures are recorded
- private holdout remains unused
- no promotion or actor-input contract change occurs
- claims are limited to fresh public repeat trends

## Failure Criteria

- profile-specific budgets or hyperparameters change after seeing results
- private holdout is used
- metrics are framed as paper-level evidence
- hidden or oracle actor inputs are introduced
- failed profiles are omitted from summary
- corrected controls are not applied in training or evaluation

## Evidence Gates

- M1212 may run the fresh corrected public repeat only
- M1212 may run PPO under the fixed M1211 repeat budget and seeds
- M1212 must evaluate every checkpoint on the same fresh public eval seeds
- M1212 must not promote
- M1212 must not use private holdout
- M1212 must not tune profiles based on M1209 or partial M1212 results
- M1212 must not run candidate replay
- M1212 must not add hidden or oracle actor inputs
- M1212 must not claim paper-level evidence or self-identification

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not change profile-specific budgets
- do not use private holdout
- do not promote any checkpoint
- do not tune hyperparameters after seeing profile results
- do not add hidden or oracle actor inputs
- do not claim recurrent-belief advantage or self-identification

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1212-paper-route-corrected-profile-repeat-run
- type: gate
- checkpoint: runs/m1212_corrected_profile_repeat/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: corrected_profile_repeat_completed_route_to_repeat_result_audit
- reason: M1212 completes 24/24 fresh repeat seed runs; L2 current-tiled controls outperform normal L2 and L3 online beats corrected reset in aggregate but L3 family ranking conflicts with M1209 so route to cross-block audit

## Next Blocker

m1213-paper-route-corrected-profile-repeat-result-audit
