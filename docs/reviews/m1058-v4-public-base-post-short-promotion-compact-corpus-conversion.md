# m1058-v4-public-base-post-short-promotion-compact-corpus-conversion Research Review

## Summary

- Generated at UTC: 20260527T044953Z
- Type: objective_sanity
- Gate tier: proof
- Promotion decision: post_short_promotion_compact_corpus_conversion_replay_failure_route_to_audit
- Decision reason: M1058 objective conversion passes for three compact corpora but one cross-family replay sanity gate loses three success-drop rows

## Hypothesis

The refreshed post-short-promotion surface can be converted into compact source-capped corpora whose objective and replay sanity pass for the short-PPO family.

## Lineage

- parent_checkpoint: runs/ppo_m1049_guarded_short_escalation_seed61049/checkpoint.pt, runs/ppo_m1050_guarded_short_repeat_seed61050/checkpoint.pt, runs/ppo_m1050_guarded_short_repeat_seed61051/checkpoint.pt
- parent_dataset: runs/m1056_margin_bucket_width_0005/accepted_wrong_history_rows.csv, docs/m1057-v4-public-base-post-short-promotion-compact-corpus-conversion-design.md
- parent_config: experiments/manifests/m1057-v4-public-base-post-short-promotion-compact-corpus-conversion-design.json
- parent_objective: convert refreshed current-base surface into compact objective/replay corpora
- derived_from: m1057-v4-public-base-post-short-promotion-compact-corpus-conversion-design
- blocked_by: M1056 admits conversion after diagnosing M1055 margin-bucket failure as coarse bucket artifact
- supersedes: None
- invalidates: using refreshed surface for PPO before compact corpus objective and replay sanity

## Success Criteria

- three objective summaries exist
- three replay sanity summaries exist
- all compact corpora have >= 20 rows
- all compact corpora have >= 10 physical pairs
- all compact corpora have >= 2 targets
- all objective sanity gates pass
- all replay sanity gates pass
- no actor training PPO promotion or private holdout occurs

## Failure Criteria

- compact corpus is too small
- objective sanity fails
- replay sanity fails
- actor training or PPO starts
- private holdout is used

## Evidence Gates

- M1058 must not train actor or run PPO
- M1058 must build compact source-capped corpora for all three short-PPO family checkpoints
- M1058 must run objective sanity for all three corpora
- M1058 must run cross-family replay sanity
- M1058 must not promote a checkpoint
- M1058 must preserve actor inputs

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run PPO
- do not train actor
- do not promote
- do not use private holdout
- do not change actor inputs
- do not skip replay sanity

## Failure Taxonomy

- proof_washout

## Scoreboard

- milestone: m1058-v4-public-base-post-short-promotion-compact-corpus-conversion
- type: objective_sanity
- checkpoint: runs/m1058_post_short_promotion_compact_conversion_summary/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: post_short_promotion_compact_corpus_conversion_replay_failure_route_to_audit
- reason: M1058 objective conversion passes for three compact corpora but one cross-family replay sanity gate loses three success-drop rows

## Next Blocker

m1059-v4-public-base-post-short-promotion-conversion-replay-failure-audit
