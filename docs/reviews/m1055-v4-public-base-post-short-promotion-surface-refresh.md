# m1055-v4-public-base-post-short-promotion-surface-refresh Research Review

## Summary

- Generated at UTC: 20260527T043159Z
- Type: gate
- Gate tier: proof
- Promotion decision: post_short_promotion_surface_refresh_margin_bucket_sparse_route_to_bucket_audit
- Decision reason: M1055 mines 315 accepted wrong-history rows but rejects direct conversion because normal-margin bucket diversity is 1 under the 0.01m rule

## Hypothesis

The newly promoted 4096-step public-gate base family still exposes a source-diverse wrong-history outcome boundary surface suitable for conversion into replay/objective corpora.

## Lineage

- parent_checkpoint: runs/ppo_m1049_guarded_short_escalation_seed61049/checkpoint.pt, runs/ppo_m1050_guarded_short_repeat_seed61050/checkpoint.pt, runs/ppo_m1050_guarded_short_repeat_seed61051/checkpoint.pt
- parent_dataset: docs/m1054-v4-public-base-post-short-promotion-surface-refresh-design.md
- parent_config: experiments/manifests/m1054-v4-public-base-post-short-promotion-surface-refresh-design.json
- parent_objective: mine and robustness-gate a source-diverse current-base wrong-history boundary surface after short-PPO promotion
- derived_from: m1054-v4-public-base-post-short-promotion-surface-refresh-design
- blocked_by: current public-gate base was promoted from known public surfaces; refreshed source-diverse current-base surface is needed before medium PPO
- supersedes: None
- invalidates: running medium PPO before current-base surface refresh

## Success Criteria

- matched-current summary exists
- outcome summary exists
- boundary relocation summary exists
- robustness summary exists
- accepted wrong-history rows >= 80
- physical pairs >= 10
- left steps >= 5
- checkpoints >= 3
- targets >= 2
- success_drop_fraction == 1.0
- no training or PPO occurs

## Failure Criteria

- surface is sparse
- surface is duplicate-dominated
- wrong-history outcome sensitivity is absent
- actor inputs change
- training or PPO starts
- private holdout is used

## Evidence Gates

- M1055 must not train or run PPO
- M1055 must preserve actor inputs
- M1055 must mine matched-current ambiguity for the three 4096-step family checkpoints
- M1055 must run outcome, boundary relocation, and source-diverse robustness stages
- M1055 must classify sparse or duplicate-dominated surfaces instead of loosening thresholds
- M1055 must not promote a checkpoint

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run PPO
- do not train
- do not promote
- do not use private holdout
- do not change actor inputs
- do not loosen source-diversity thresholds after seeing failure
- do not route to medium PPO directly from M1055

## Failure Taxonomy

- scenario_sampling_failure

## Scoreboard

- milestone: m1055-v4-public-base-post-short-promotion-surface-refresh
- type: gate
- checkpoint: docs/m1055-v4-public-base-post-short-promotion-surface-refresh.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: post_short_promotion_surface_refresh_margin_bucket_sparse_route_to_bucket_audit
- reason: M1055 mines 315 accepted wrong-history rows but rejects direct conversion because normal-margin bucket diversity is 1 under the 0.01m rule

## Next Blocker

m1056-v4-public-base-post-short-promotion-margin-bucket-audit
