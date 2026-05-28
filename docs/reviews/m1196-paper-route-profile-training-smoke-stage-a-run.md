# m1196-paper-route-profile-training-smoke-stage-a-run Research Review

## Summary

- Generated at UTC: 20260528T051639Z
- Type: gate
- Gate tier: infrastructure
- Promotion decision: profile_training_smoke_stage_a_pass_route_to_stage_b_full_profile_smoke
- Decision reason: M1196 completes Stage A smoke-scale PPO plumbing for L0 L1 L2_window_25 and L3 with finite metrics and L0 runtime mask metadata present; no profile superiority driver-performance promotion private holdout candidate replay or actor-input change claim

## Hypothesis

The representative Stage A L0/L1/L2/L3 generated profiles can complete identical smoke-scale PPO training loops after vector-path profile-mask integration.

## Lineage

- parent_checkpoint: runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt
- parent_dataset: docs/m1195-paper-route-train-entrypoint-profile-mask-integration.md, configs/paper_route_profiles
- parent_config: experiments/manifests/m1195-paper-route-train-entrypoint-profile-mask-integration.json
- parent_objective: run the bounded M1193 Stage A profile training smoke after vector-path masks are integrated
- derived_from: m1195-paper-route-train-entrypoint-profile-mask-integration
- blocked_by: profile train/eval path is now mask-ready but no generated profile has run the training loop yet
- supersedes: training-loop readiness inferred from runtime smoke alone
- invalidates: claiming profile training readiness before Stage A smoke completes

## Success Criteria

- docs/m1196-paper-route-profile-training-smoke-stage-a-run.md exists
- runs/m1196_profile_training_smoke_stage_a/summary.json exists
- L0_current_masked L1_one_step L2_window_25 and L3_online_gru runs complete
- metrics are finite
- summary reports no private holdout no promotion no candidate replay no actor-input expansion
- L0 artifacts include controller_profile_runtime metadata
- no profile superiority or driver-performance claim occurs

## Failure Criteria

- any Stage A profile cannot complete the smoke run
- metrics are non-finite
- L0 artifacts lack runtime mask metadata
- private holdout or promotion occurs
- hidden or oracle actor inputs are introduced
- results are framed as profile superiority

## Evidence Gates

- M1196 may run bounded Stage A PPO training smoke only
- M1196 may train L0_current_masked L1_one_step L2_window_25 and L3_online_gru for smoke-scale plumbing only
- M1196 must not promote
- M1196 must not use private holdout
- M1196 must not tune profiles based on early results
- M1196 must not run candidate replay
- M1196 must not add hidden or oracle actor inputs
- M1196 must not claim profile superiority or driver performance

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

- milestone: m1196-paper-route-profile-training-smoke-stage-a-run
- type: gate
- checkpoint: runs/m1196_profile_training_smoke_stage_a/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: profile_training_smoke_stage_a_pass_route_to_stage_b_full_profile_smoke
- reason: M1196 completes Stage A smoke-scale PPO plumbing for L0 L1 L2_window_25 and L3 with finite metrics and L0 runtime mask metadata present; no profile superiority driver-performance promotion private holdout candidate replay or actor-input change claim

## Next Blocker

m1197-paper-route-profile-training-smoke-stage-b-run
