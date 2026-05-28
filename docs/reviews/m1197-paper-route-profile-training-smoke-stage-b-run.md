# m1197-paper-route-profile-training-smoke-stage-b-run Research Review

## Summary

- Generated at UTC: 20260528T052250Z
- Type: gate
- Gate tier: infrastructure
- Promotion decision: profile_training_smoke_stage_b_pass_route_to_fair_comparison_pilot_design
- Decision reason: M1197 completes Stage B smoke-scale PPO plumbing for all eight generated profiles with finite metrics and L0 runtime mask metadata present; no profile superiority driver-performance promotion private holdout candidate replay or actor-input change claim

## Hypothesis

All eight generated L0/L1/L2/L3 profiles can complete identical smoke-scale PPO training loops after Stage A passes.

## Lineage

- parent_checkpoint: runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt
- parent_dataset: docs/m1196-paper-route-profile-training-smoke-stage-a-run.md, configs/paper_route_profiles
- parent_config: experiments/manifests/m1196-paper-route-profile-training-smoke-stage-a-run.json
- parent_objective: run full generated-profile Stage B smoke after representative Stage A training plumbing passes
- derived_from: m1196-paper-route-profile-training-smoke-stage-a-run
- blocked_by: Stage A passed but the remaining L2 windows and L3_reset_control have not run train-loop smoke
- supersedes: assuming all generated profiles train because representative profiles passed
- invalidates: starting fair comparison pilot before all generated profiles complete smoke training

## Success Criteria

- docs/m1197-paper-route-profile-training-smoke-stage-b-run.md exists
- runs/m1197_profile_training_smoke_stage_b/summary.json exists
- all eight generated profile runs complete
- metrics are finite
- summary reports no private holdout no promotion no candidate replay no actor-input expansion
- no profile superiority or driver-performance claim occurs

## Failure Criteria

- any generated profile cannot complete the smoke run
- metrics are non-finite
- private holdout or promotion occurs
- hidden or oracle actor inputs are introduced
- results are framed as profile superiority

## Evidence Gates

- M1197 may run bounded Stage B PPO training smoke only
- M1197 may train all eight generated profiles for smoke-scale plumbing only
- M1197 must not promote
- M1197 must not use private holdout
- M1197 must not tune profiles based on early results
- M1197 must not run candidate replay
- M1197 must not add hidden or oracle actor inputs
- M1197 must not claim profile superiority or driver performance

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not change generated configs per profile after seeing results
- do not use private holdout
- do not promote a checkpoint
- do not run public proof replay as if this were a driver candidate
- do not compare performance except as smoke diagnostics
- do not add hidden or oracle actor inputs
- do not skip recording failed profiles

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1197-paper-route-profile-training-smoke-stage-b-run
- type: gate
- checkpoint: runs/m1197_profile_training_smoke_stage_b/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: profile_training_smoke_stage_b_pass_route_to_fair_comparison_pilot_design
- reason: M1197 completes Stage B smoke-scale PPO plumbing for all eight generated profiles with finite metrics and L0 runtime mask metadata present; no profile superiority driver-performance promotion private holdout candidate replay or actor-input change claim

## Next Blocker

m1198-paper-route-fair-comparison-pilot-design
