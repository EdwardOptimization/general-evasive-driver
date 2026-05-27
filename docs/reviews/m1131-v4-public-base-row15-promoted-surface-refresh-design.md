# m1131-v4-public-base-row15-promoted-surface-refresh-design Research Review

## Summary

- Generated at UTC: 20260527T220904Z
- Type: gate
- Gate tier: process
- Promotion decision: row15_promoted_surface_refresh_design_admit_m1132_refresh
- Decision reason: M1131 designs source-balanced promoted-base surface refresh for alpha_0_15 using row15_current previous_m1078_base and short61049/61050/61051 family policies with strict diversity thresholds

## Hypothesis

The promoted M1129 alpha_0_15 public-gate base needs a fresh source-diverse protected/preference surface before any new PPO proposal.

## Lineage

- parent_checkpoint: runs/m1123_row15_unsafe_margin_projection_probe/checkpoints/alpha_0_15.pt
- parent_dataset: docs/m1130-v4-public-base-row15-projection-post-promotion-synthesis.md, docs/m1129-v4-public-base-row15-projection-promotion-audit.md
- parent_config: experiments/manifests/m1130-v4-public-base-row15-projection-post-promotion-synthesis.json
- parent_objective: design a current-base source-diverse protected/preference surface refresh before any new PPO proposal
- derived_from: m1130-v4-public-base-row15-projection-post-promotion-synthesis
- blocked_by: M1130 opened row15_promoted_base_surface_refresh and blocked direct PPO until refresh design
- supersedes: None
- invalidates: running PPO directly from the M1129 public-gate base, reusing only M1120/M1123/M1127 active rows as if they were fresh current-base evidence

## Success Criteria

- design artifact exists
- current base checkpoint is explicit
- mining axes are explicit
- source-diversity thresholds are explicit
- objective/replay conversion plan is explicit
- no training, PPO, replay, mining, promotion, or private holdout occurs

## Failure Criteria

- design artifact is missing
- current base checkpoint is ambiguous
- source-diversity thresholds are missing
- training, PPO, replay, or mining starts
- private holdout is used

## Evidence Gates

- M1131 must not train actor weights
- M1131 must not run PPO
- M1131 must not use private holdout
- M1131 must not mine rows; design only
- M1131 must define acceptance criteria for a current-base source-diverse refresh

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train actor weights
- do not run PPO
- do not mine rows
- do not run replay
- do not promote
- do not use private holdout
- do not weaken actor-input or changed-parameter contracts

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1131-v4-public-base-row15-promoted-surface-refresh-design
- type: gate
- checkpoint: docs/m1131-v4-public-base-row15-promoted-surface-refresh-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: row15_promoted_surface_refresh_design_admit_m1132_refresh
- reason: M1131 designs source-balanced promoted-base surface refresh for alpha_0_15 using row15_current previous_m1078_base and short61049/61050/61051 family policies with strict diversity thresholds

## Next Blocker

m1132-v4-public-base-row15-promoted-surface-refresh
