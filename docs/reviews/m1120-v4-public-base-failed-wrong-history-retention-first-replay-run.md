# m1120-v4-public-base-failed-wrong-history-retention-first-replay-run Research Review

## Summary

- Generated at UTC: 20260527T212111Z
- Type: gate
- Gate tier: proof
- Promotion decision: failed_wrong_history_retention_first_replay_reject_wrong_history_safe_route_to_audit
- Decision reason: M1120 first replay passes 2 of 6 surfaces and fails 4 of 6 because row15 pair 9530:21:9550:21 becomes wrong-history safe with zero normal-lost events so it routes to failure audit

## Hypothesis

The M1118 best candidate preserves the target-base old-public and source-diverse replay surfaces that M1112 washed out.

## Lineage

- parent_checkpoint: runs/m1118_failed_wrong_history_retention_actor_update_seed111800/optimized_checkpoint.pt
- parent_dataset: docs/m1119-v4-public-base-failed-wrong-history-retention-first-replay-design.md, runs/m183_m168_boundary_outcome_corpus_dedup_seed9510/boundary_outcome_corpus.csv, runs/m223_m219_boundary_outcome_corpus_seed10060/boundary_outcome_corpus.csv, runs/m267_m264_boundary_outcome_corpus_seed10070/boundary_outcome_corpus.csv, runs/m320_m316_repaired_boundary_outcome_corpus_seed10080/boundary_outcome_corpus.csv, runs/m320_m314_boundary_outcome_corpus_seed10080/boundary_outcome_corpus.csv, runs/m320_m316_boundary_outcome_corpus_seed10080/boundary_outcome_corpus.csv
- parent_config: experiments/manifests/m1119-v4-public-base-failed-wrong-history-retention-first-replay-design.json
- parent_objective: run target-base old-public and source-diverse first replay gates for M1118 best candidate
- derived_from: m1119-v4-public-base-failed-wrong-history-retention-first-replay-design
- blocked_by: M1118 passed only pre-replay gates
- supersedes: None
- invalidates: promotion before replay, PPO before replay, family-source training anchor before materialization

## Success Criteria

- all three old-public first replay surfaces pass
- all three source-diverse first replay surfaces pass
- aggregate summary is written
- failure class is none for every surface
- no actor training, PPO, promotion, private holdout, actor-input change, family-intersection replay, fresh/OOD, or behavior gate occurs

## Failure Criteria

- any old-public first replay surface fails
- any source-diverse first replay surface fails
- aggregate summary is missing
- actor training, PPO, promotion, private holdout, actor-input change, family-intersection replay, fresh/OOD, or behavior gate starts

## Evidence Gates

- M1120 may run old-public and source-diverse target-base first replay
- M1120 must not train actor weights
- M1120 must not run PPO
- M1120 must not promote
- M1120 must not use private holdout
- M1120 must not run family-intersection replay
- M1120 must preserve actor inputs

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train actor weights
- do not run PPO
- do not promote
- do not use private holdout
- do not change actor inputs
- do not run family-intersection replay
- do not run fresh/OOD or behavior gates
- do not weaken replay thresholds

## Failure Taxonomy

- proof_washout

## Scoreboard

- milestone: m1120-v4-public-base-failed-wrong-history-retention-first-replay-run
- type: gate
- checkpoint: runs/m1120_failed_wrong_history_retention_first_replay/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: failed_wrong_history_retention_first_replay_reject_wrong_history_safe_route_to_audit
- reason: M1120 first replay passes 2 of 6 surfaces and fails 4 of 6 because row15 pair 9530:21:9550:21 becomes wrong-history safe with zero normal-lost events so it routes to failure audit

## Next Blocker

m1121-v4-public-base-failed-wrong-history-retention-first-replay-failure-audit
