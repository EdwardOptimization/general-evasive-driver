# m1149-v4-public-base-row15-promoted-actor-update-first-replay-run Research Review

## Summary

- Generated at UTC: 20260527T231724Z
- Type: gate
- Gate tier: proof
- Promotion decision: row15_promoted_first_replay_reject_wrong_history_safe_route_to_failure_audit
- Decision reason: M1149 first replay passes 8 of 10 surfaces but rejects m1147_114602 because M267 and row15-promoted materialized surfaces lose 76 success-drop events through wrong-history-safe rollouts with zero normal-lost events

## Hypothesis

The M1147 best candidate preserves old-public, source-diverse, and row15-promoted materialized replay surfaces.

## Lineage

- parent_checkpoint: runs/m1147_row15_promoted_actor_coupling_anchor100_s10_lr5e5_seed114602/optimized_checkpoint.pt
- parent_dataset: docs/m1148-v4-public-base-row15-promoted-actor-update-first-replay-design.md, runs/m183_m168_boundary_outcome_corpus_dedup_seed9510/boundary_outcome_corpus.csv, runs/m183_m170_boundary_outcome_corpus_dedup_seed9510/boundary_outcome_corpus.csv, runs/m193_m189_boundary_outcome_corpus_seed9630/boundary_outcome_corpus.csv, runs/m212_m204_boundary_outcome_corpus_seed10040/boundary_outcome_corpus.csv, runs/m223_m219_boundary_outcome_corpus_seed10060/boundary_outcome_corpus.csv, runs/m267_m264_boundary_outcome_corpus_seed10070/boundary_outcome_corpus.csv, runs/m320_m316_repaired_boundary_outcome_corpus_seed10080/boundary_outcome_corpus.csv, runs/m320_m314_boundary_outcome_corpus_seed10080/boundary_outcome_corpus.csv, runs/m320_m316_boundary_outcome_corpus_seed10080/boundary_outcome_corpus.csv, runs/m1142_row15_promoted_target_materialization/row15_current_boundary_rows.csv
- parent_config: experiments/manifests/m1148-v4-public-base-row15-promoted-actor-update-first-replay-design.json
- parent_objective: run old-public, source-diverse, and row15-promoted materialized first replay gates for M1147 best candidate
- derived_from: m1148-v4-public-base-row15-promoted-actor-update-first-replay-design
- blocked_by: M1147 passed only pre-replay exact, anchor, and parameter-scope gates
- supersedes: None
- invalidates: promotion before replay, PPO before replay, full public gate before first replay result

## Success Criteria

- all six old-public first replay surfaces pass
- all three source-diverse first replay surfaces pass
- row15-promoted materialized replay passes
- aggregate summary is written
- failure class is none for every surface
- no actor training, PPO, promotion, private holdout, actor-input change, M1061 family replay, fresh/OOD, or behavior gate occurs

## Failure Criteria

- any old-public first replay surface fails
- any source-diverse first replay surface fails
- row15-promoted materialized replay fails
- aggregate summary is missing
- actor training, PPO, promotion, private holdout, actor-input change, M1061 family replay, fresh/OOD, or behavior gate starts

## Evidence Gates

- M1149 may run only old-public, source-diverse, and row15-promoted first replay
- M1149 must not train actor weights
- M1149 must not run PPO
- M1149 must not promote
- M1149 must not use private holdout
- M1149 must not run M1061 family-intersection replay
- M1149 must not run fresh/OOD or behavior gates
- M1149 must preserve actor inputs

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train actor weights
- do not run PPO
- do not promote
- do not use private holdout
- do not change actor inputs
- do not run M1061 family-intersection replay
- do not run fresh/OOD or behavior gates
- do not weaken replay thresholds

## Failure Taxonomy

- proof_washout

## Scoreboard

- milestone: m1149-v4-public-base-row15-promoted-actor-update-first-replay-run
- type: gate
- checkpoint: runs/m1149_row15_promoted_actor_update_first_replay/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: row15_promoted_first_replay_reject_wrong_history_safe_route_to_failure_audit
- reason: M1149 first replay passes 8 of 10 surfaces but rejects m1147_114602 because M267 and row15-promoted materialized surfaces lose 76 success-drop events through wrong-history-safe rollouts with zero normal-lost events

## Next Blocker

m1150-v4-public-base-row15-promoted-first-replay-failure-audit
