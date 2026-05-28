# m1159-v4-public-base-row15-promoted-projection-post-promotion-synthesis Research Review

## Summary

- Generated at UTC: 20260528T000524Z
- Type: gate
- Gate tier: process
- Promotion decision: not_applicable
- Decision reason: M1159 may only synthesize the post-promotion state and choose the next branch. It cannot train actor weights, run PPO, run replay, run objective optimization, mine rows, promote, use private holdout, or change actor inputs.

## Hypothesis

After M1158 promotion, the next branch should refresh current-base source-diverse protected/preference surfaces with explicit margin-slack attention before another PPO proposal.

## Lineage

- parent_checkpoint: runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt
- parent_dataset: docs/m1158-v4-public-base-row15-promoted-projection-promotion-audit.md, docs/m1157-v4-public-base-row15-promoted-projection-diagnostic-result-audit.md, docs/m1156-v4-public-base-row15-promoted-projection-family-behavior-run.md, docs/m1154-v4-public-base-row15-promoted-unsafe-margin-projection-run.md
- parent_config: experiments/manifests/m1158-v4-public-base-row15-promoted-projection-promotion-audit.json
- parent_objective: synthesize post-promotion route after alpha_0_05 becomes the public-gate base
- derived_from: m1158-v4-public-base-row15-promoted-projection-promotion-audit
- blocked_by: M1158 promotes a new public-gate base and the next branch has not been selected
- supersedes: None
- invalidates: starting PPO immediately after promotion without post-promotion synthesis, claiming performance improvement from proof-hardening promotion, ignoring the near-boundary wrong-history margin caveat in the next branch

## Success Criteria

- synthesis artifact exists
- promotion evidence is summarized
- supported and unsupported claims are explicit
- public-gate overfit risk is explicit
- near-boundary margin caveat is explicit
- next branch decision is explicit
- no actor training, PPO, replay, objective optimization, mining, promotion, private holdout, or actor-input change occurs

## Failure Criteria

- synthesis artifact is missing
- next branch decision is ambiguous
- promotion scope is overclaimed
- near-boundary caveat is ignored
- actor training, PPO, replay, objective optimization, mining, promotion, private holdout, or actor-input change starts

## Evidence Gates

- M1159 must synthesize the promotion and choose the next branch
- M1159 must not train actor weights
- M1159 must not run PPO
- M1159 must not run replay
- M1159 must not run objective optimization
- M1159 must not mine rows
- M1159 must not promote another checkpoint
- M1159 must not use private holdout
- M1159 must preserve actor inputs

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

- No scoreboard row recorded.

## Next Blocker

m1159-v4-public-base-row15-promoted-projection-post-promotion-synthesis
