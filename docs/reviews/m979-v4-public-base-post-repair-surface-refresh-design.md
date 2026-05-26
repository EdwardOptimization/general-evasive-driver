# m979-v4-public-base-post-repair-surface-refresh-design Research Review

## Summary

- Generated at UTC: 20260526T112842Z
- Type: gate
- Gate tier: process
- Promotion decision: post_repair_surface_refresh_design_admit_m980
- Decision reason: M979 designs no-PPO current-base normal-success wrong-history surface refresh with fresh public seed ranges before PPO

## Hypothesis

Before another guarded PPO continuation from the M974 public base, the project should refresh current-base wrong-history, preference, and source-diverse proof surfaces to reduce public-gate overfit risk.

## Lineage

- parent_checkpoint: runs/m974_exact_repair_from_base_s40_seed5974/candidate_checkpoint.pt
- parent_dataset: docs/m978-v4-public-base-post-exact-repair-promotion-synthesis.md, docs/m977-v4-public-base-post-promotion-exact-repair-promotion-audit.md, runs/m976_v4_public_base_post_promotion_exact_repair_full_public_gate/summary.json
- parent_config: experiments/manifests/m978-v4-public-base-post-exact-repair-promotion-synthesis.json
- parent_objective: design a fresh current-base surface refresh before another PPO continuation
- derived_from: m978-v4-public-base-post-exact-repair-promotion-synthesis, m977-v4-public-base-post-promotion-exact-repair-promotion-audit
- blocked_by: M978 synthesis identifies moderate public-gate overfit risk after repeated optimization on established surfaces
- supersedes: None
- invalidates: starting a new guarded PPO branch from M974 base before refreshing current-base proof surfaces

## Success Criteria

- design document exists
- design names the new public-gate base
- design specifies fresh wrong-history boundary mining
- design specifies preference/source-diverse acceptance thresholds
- design keeps PPO, promotion, and private holdout blocked

## Failure Criteria

- design starts PPO
- design uses only old M267/M264 rows
- design omits source diversity
- design changes actor inputs
- design uses private holdout

## Evidence Gates

- M979 must not run PPO
- M979 must not promote
- M979 must not use private holdout
- M979 must preserve P0 actor-input contract
- M979 must design fresh current-base wrong-history and source-diverse surface mining
- M979 must keep old public surfaces as retention gates, not the only discovery source

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not start PPO from the new base before surface refresh
- do not mine only the existing M267/M264 rows
- do not change actor inputs
- do not use private holdout
- do not treat surface refresh as driver promotion

## Failure Taxonomy

- none

## Scoreboard

- milestone: m979-v4-public-base-post-repair-surface-refresh-design
- type: gate
- checkpoint: docs/m979-v4-public-base-post-repair-surface-refresh-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: post_repair_surface_refresh_design_admit_m980
- reason: M979 designs no-PPO current-base normal-success wrong-history surface refresh with fresh public seed ranges before PPO

## Next Blocker

m980-v4-public-base-post-repair-surface-refresh-implementation
