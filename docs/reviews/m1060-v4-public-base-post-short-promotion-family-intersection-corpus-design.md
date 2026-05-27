# m1060-v4-public-base-post-short-promotion-family-intersection-corpus-design Research Review

## Summary

- Generated at UTC: 20260527T045810Z
- Type: gate
- Gate tier: process
- Promotion decision: post_short_promotion_family_intersection_design_admit_m1061_selector
- Decision reason: M1060 designs deterministic family-intersection replay-calibrated compact corpus filtering after M1058 replay failure

## Hypothesis

A replay-calibrated family-intersection selector can remove near-zero wrong-history positive rows while preserving enough source diversity for compact corpus conversion.

## Lineage

- parent_checkpoint: runs/ppo_m1049_guarded_short_escalation_seed61049/checkpoint.pt, runs/ppo_m1050_guarded_short_repeat_seed61050/checkpoint.pt, runs/ppo_m1050_guarded_short_repeat_seed61051/checkpoint.pt
- parent_dataset: docs/m1059-v4-public-base-post-short-promotion-conversion-replay-failure-audit.md, runs/m1058_short61049_replay_sanity_seed10570/boundary_replay_rows.csv
- parent_config: experiments/manifests/m1059-v4-public-base-post-short-promotion-conversion-replay-failure-audit.json
- parent_objective: design family-intersection replay-calibrated compact corpus conversion after M1058 replay failure
- derived_from: m1059-v4-public-base-post-short-promotion-conversion-replay-failure-audit
- blocked_by: M1058 compact corpus conversion loses three success-drop rows under short61050 candidate replay
- supersedes: None
- invalidates: using current-checkpoint-only compact rows as a family-wide gate

## Success Criteria

- design artifact exists
- family-intersection policy set is explicit
- row filter criteria are explicit
- minimum corpus diversity thresholds are explicit
- objective and replay sanity requirements are explicit
- no training or PPO occurs

## Failure Criteria

- design artifact is missing
- family-intersection criteria are ambiguous
- PPO starts
- private holdout is used
- actor inputs change

## Evidence Gates

- M1060 must design only
- M1060 must not train or run PPO
- M1060 must preserve actor inputs
- M1060 must require family-intersection replay filtering before compact conversion
- M1060 must specify minimum rows physical pairs and targets after filtering

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run PPO
- do not train
- do not promote
- do not use private holdout
- do not accept current-base-only rows as family-wide proof rows

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1060-v4-public-base-post-short-promotion-family-intersection-corpus-design
- type: gate
- checkpoint: docs/m1060-v4-public-base-post-short-promotion-family-intersection-corpus-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: post_short_promotion_family_intersection_design_admit_m1061_selector
- reason: M1060 designs deterministic family-intersection replay-calibrated compact corpus filtering after M1058 replay failure

## Next Blocker

m1061-v4-public-base-post-short-promotion-family-intersection-corpus
