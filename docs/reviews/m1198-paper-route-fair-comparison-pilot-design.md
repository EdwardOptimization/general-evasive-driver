# m1198-paper-route-fair-comparison-pilot-design Research Review

## Summary

- Generated at UTC: 20260528T052859Z
- Type: gate
- Gate tier: infrastructure
- Promotion decision: fair_comparison_pilot_design_admit_public_pilot_run
- Decision reason: M1198 fixes the first fair public profile comparison pilot protocol with seven main profiles plus L3_reset diagnostic fixed 3-seed 8192-step budget fixed public eval seeds and explicit ban on smoke-metric performance claims promotion private holdout per-profile tuning and self-ID claims

## Hypothesis

A fair public comparison pilot can be designed for L0/L1/L2/L3 profiles without using smoke metrics as performance evidence or tuning profiles unequally.

## Lineage

- parent_checkpoint: runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt
- parent_dataset: docs/m1197-paper-route-profile-training-smoke-stage-b-run.md, runs/m1197_profile_training_smoke_stage_b/summary.json, configs/paper_route_profiles
- parent_config: experiments/manifests/m1197-paper-route-profile-training-smoke-stage-b-run.json
- parent_objective: design the first fair multi-profile comparison pilot after all generated profiles pass train-loop smoke
- derived_from: m1197-paper-route-profile-training-smoke-stage-b-run
- blocked_by: Stage B proves train-loop plumbing but not fair comparison readiness or profile superiority
- supersedes: using one-seed smoke diagnostics as a profile comparison
- invalidates: claiming finite-window or GRU advantage from M1197 smoke metrics

## Success Criteria

- docs/m1198-paper-route-fair-comparison-pilot-design.md exists
- profile set, seeds, training budget, eval budget, metrics, artifacts, failure rules, and claim scope are fixed
- private holdout remains unused
- smoke metrics are explicitly excluded as performance evidence
- no controller training, candidate replay, PPO, promotion, private holdout, or actor-input contract change occurs
- next run or implementation milestone is selected

## Failure Criteria

- training starts in M1198
- pilot uses unequal budgets or per-profile tuning
- private holdout is used
- M1197 smoke metrics are used as comparison evidence
- hidden or oracle actor inputs are introduced

## Evidence Gates

- M1198 may design a fair comparison pilot only
- M1198 must not train controller weights
- M1198 must not run PPO
- M1198 must not run candidate replay
- M1198 must not promote
- M1198 must not use private holdout
- M1198 must not add hidden or oracle actor inputs
- M1198 must not claim profile superiority

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run training
- do not reuse smoke metrics as comparison evidence
- do not use private holdout
- do not tune per profile from M1196 or M1197 results
- do not add hidden or oracle actor inputs
- do not promote any checkpoint
- do not claim paper-level evidence from a design document

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1198-paper-route-fair-comparison-pilot-design
- type: gate
- checkpoint: docs/m1198-paper-route-fair-comparison-pilot-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: fair_comparison_pilot_design_admit_public_pilot_run
- reason: M1198 fixes the first fair public profile comparison pilot protocol with seven main profiles plus L3_reset diagnostic fixed 3-seed 8192-step budget fixed public eval seeds and explicit ban on smoke-metric performance claims promotion private holdout per-profile tuning and self-ID claims

## Next Blocker

m1199-paper-route-fair-comparison-pilot-run
