# m1061-v4-public-base-post-short-promotion-family-intersection-corpus Research Review

## Summary

- Generated at UTC: 20260527T054700Z
- Type: objective_sanity
- Gate tier: proof
- Promotion decision: post_short_promotion_family_intersection_corpus_pass_route_to_synthesis
- Decision reason: M1061 selects 79 strict family-intersection rows and passes objective sanity plus six cross-family replay gates for the short-PPO family without PPO or promotion

## Hypothesis

Family-intersection replay filtering can remove near-zero wrong-history positive rows while preserving enough compact source diversity for objective and replay sanity.

## Lineage

- parent_checkpoint: runs/ppo_m1049_guarded_short_escalation_seed61049/checkpoint.pt, runs/ppo_m1050_guarded_short_repeat_seed61050/checkpoint.pt, runs/ppo_m1050_guarded_short_repeat_seed61051/checkpoint.pt
- parent_dataset: docs/m1060-v4-public-base-post-short-promotion-family-intersection-corpus-design.md, runs/m1056_margin_bucket_width_0005/accepted_wrong_history_rows.csv
- parent_config: experiments/manifests/m1060-v4-public-base-post-short-promotion-family-intersection-corpus-design.json
- parent_objective: implement and run family-intersection replay-calibrated compact corpus selector
- derived_from: m1060-v4-public-base-post-short-promotion-family-intersection-corpus-design
- blocked_by: M1058 compact corpus failed cross-family replay because current-base rows were not family-intersection filtered
- supersedes: None
- invalidates: using current-base-only compact corpus as family-wide proof gate

## Success Criteria

- selector tool and tests exist
- family-intersection compact corpus exists
- selected rows >= 20
- physical pairs >= 10
- targets >= 2
- all selected rows pass success-drop under all family policies
- objective sanity passes
- replay sanity passes
- no PPO actor training promotion or private holdout occurs

## Failure Criteria

- selector is missing
- family-intersection rows are sparse
- objective sanity fails
- replay sanity fails
- PPO or actor training starts
- private holdout is used

## Evidence Gates

- M1061 must not run PPO
- M1061 must not train actor
- M1061 must preserve actor inputs
- M1061 must implement deterministic family-intersection row selection
- M1061 must require selected rows to pass success-drop under all short-PPO family policies
- M1061 must run objective and replay sanity if compact selection is sufficient

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run PPO
- do not train actor
- do not promote
- do not use private holdout
- do not accept rows that fail under any family policy

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1061-v4-public-base-post-short-promotion-family-intersection-corpus
- type: objective_sanity
- checkpoint: runs/m1061_family_intersection_summary/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: post_short_promotion_family_intersection_corpus_pass_route_to_synthesis
- reason: M1061 selects 79 strict family-intersection rows and passes objective sanity plus six cross-family replay gates for the short-PPO family without PPO or promotion

## Next Blocker

m1061-v4-public-base-post-short-promotion-family-intersection-corpus
