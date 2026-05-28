# m1160-v4-public-base-row15-promoted-margin-slack-surface-refresh-design Research Review

## Summary

- Generated at UTC: 20260528T000813Z
- Type: gate
- Gate tier: process
- Promotion decision: not_applicable
- Decision reason: M1160 may only design the next alpha_0_05 current-base margin-slack surface refresh. It cannot run mining, replay, actor training, PPO, promotion, private holdout, or actor-input changes.

## Hypothesis

A source-diverse margin-slack refresh can produce a stronger alpha_0_05 current-base proof surface before any PPO continuation.

## Lineage

- parent_checkpoint: runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt
- parent_dataset: docs/m1159-v4-public-base-row15-promoted-projection-post-promotion-synthesis.md, docs/m1158-v4-public-base-row15-promoted-projection-promotion-audit.md
- parent_config: experiments/manifests/m1159-v4-public-base-row15-promoted-projection-post-promotion-synthesis.json
- parent_objective: design current-base protected/preference surface refresh with explicit margin-slack attention after alpha_0_05 promotion
- derived_from: m1159-v4-public-base-row15-promoted-projection-post-promotion-synthesis
- blocked_by: M1159 opens row15_promoted_margin_slack_surface_refresh before any PPO proposal
- supersedes: None
- invalidates: PPO before current-base surface refresh design, private holdout before public surface refresh, surface mining without pre-registered margin-slack and diversity thresholds

## Success Criteria

- design artifact exists
- source policy family is explicit
- margin-slack buckets and thresholds are explicit
- diversity thresholds are explicit
- next run command is explicit
- no actor training, PPO, replay, mining, promotion, private holdout, or actor-input change occurs

## Failure Criteria

- design artifact is missing
- source family remains ambiguous
- margin-slack thresholds remain ambiguous
- next route is ambiguous
- actor training, PPO, replay, mining, promotion, private holdout, or actor-input change starts

## Evidence Gates

- M1160 must design the alpha_0_05 current-base surface refresh only
- M1160 must pre-register source diversity and margin-slack thresholds
- M1160 must not run mining
- M1160 must not run replay
- M1160 must not train actor weights
- M1160 must not run PPO
- M1160 must not promote
- M1160 must not use private holdout
- M1160 must preserve actor inputs

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run mining
- do not run replay
- do not train actor weights
- do not run PPO
- do not promote
- do not use private holdout
- do not change actor inputs
- do not weaken diversity thresholds after seeing results
- do not treat row15 near-boundary margin as sufficient coverage by itself

## Failure Taxonomy

- none

## Scoreboard

- No scoreboard row recorded.

## Next Blocker

m1160-v4-public-base-row15-promoted-margin-slack-surface-refresh-design
