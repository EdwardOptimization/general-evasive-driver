# m1130-v4-public-base-row15-projection-post-promotion-synthesis Research Review

## Summary

- Generated at UTC: 20260527T220553Z
- Type: gate
- Gate tier: process
- Promotion decision: row15_projection_post_promotion_synthesis_open_surface_refresh
- Decision reason: M1130 closes row15_projection_promotion_audit and opens row15_promoted_base_surface_refresh; next branch should refresh current-base protected/preference surfaces before any PPO

## Hypothesis

After M1129 promotion, the next branch should refresh current-base source-diverse protected/preference surfaces before another PPO proposal.

## Lineage

- parent_checkpoint: runs/m1123_row15_unsafe_margin_projection_probe/checkpoints/alpha_0_15.pt
- parent_dataset: docs/m1129-v4-public-base-row15-projection-promotion-audit.md, docs/m1128-v4-public-base-row15-projection-branch-synthesis.md, docs/m1127-v4-public-base-row15-projection-full-public-gate.md
- parent_config: experiments/manifests/m1129-v4-public-base-row15-projection-promotion-audit.json
- parent_objective: synthesize post-promotion route after alpha_0_15 becomes the public-gate base
- derived_from: m1129-v4-public-base-row15-projection-promotion-audit
- blocked_by: M1129 promoted a new public-gate base and the next branch has not been selected
- supersedes: None
- invalidates: starting PPO immediately after promotion without post-promotion synthesis, claiming performance improvement from proof-hardening promotion

## Success Criteria

- synthesis artifact exists
- promotion evidence is summarized
- supported and unsupported claims are explicit
- public-gate overfit risk is explicit
- next branch decision is explicit
- no actor training, PPO, replay, objective optimization, mining, promotion, private holdout, or actor-input change occurs

## Failure Criteria

- synthesis artifact is missing
- next branch decision is ambiguous
- promotion scope is overclaimed
- actor training, PPO, replay, objective optimization, mining, promotion, private holdout, or actor-input change starts

## Evidence Gates

- M1130 must synthesize the promotion and choose the next branch
- M1130 must not train actor weights
- M1130 must not run PPO
- M1130 must not run replay
- M1130 must not run objective optimization
- M1130 must not mine rows
- M1130 must not promote another checkpoint
- M1130 must not use private holdout
- M1130 must preserve actor inputs

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train actor weights
- do not run PPO
- do not run replay
- do not run objective optimization
- do not mine rows
- do not promote another checkpoint
- do not use private holdout
- do not change actor inputs
- do not start medium PPO before selecting the post-promotion branch

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1130-v4-public-base-row15-projection-post-promotion-synthesis
- type: gate
- checkpoint: docs/m1130-v4-public-base-row15-projection-post-promotion-synthesis.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: row15_projection_post_promotion_synthesis_open_surface_refresh
- reason: M1130 closes row15_projection_promotion_audit and opens row15_promoted_base_surface_refresh; next branch should refresh current-base protected/preference surfaces before any PPO

## Next Blocker

m1131-v4-public-base-row15-promoted-surface-refresh-design
