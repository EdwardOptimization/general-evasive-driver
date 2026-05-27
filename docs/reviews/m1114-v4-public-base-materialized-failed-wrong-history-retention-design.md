# m1114-v4-public-base-materialized-failed-wrong-history-retention-design Research Review

## Summary

- Generated at UTC: 20260527T204322Z
- Type: gate
- Gate tier: process
- Promotion decision: materialized_failed_wrong_history_retention_design_admit_export
- Decision reason: M1114 designs failed wrong-history registry and target-base trajectory retention export while forbidding direct short-family hidden-state anchors

## Hypothesis

A failed wrong-history trajectory-retention design can address the M1112 proof washout more directly than increasing the M1107 exact objective weight.

## Lineage

- parent_checkpoint: runs/m1073_medium_ppo_failed_row_repair_projection_probe/temporal_projection/checkpoints/m1031_base_row16x4_s40_a1.pt, runs/m1110_materialized_actor_coupling_anchor100_s10_lr5e5_seed110901/optimized_checkpoint.pt
- parent_dataset: docs/m1113-v4-public-base-materialized-actor-update-proof-washout-audit.md, runs/m1112_materialized_actor_update_full_public_gate/summary.json, runs/m1112_materialized_actor_update_full_public_gate/full_gates/m267_m264_replay/boundary_replay_rows.csv, runs/m1112_materialized_actor_update_full_public_gate/family_intersection_public_gate/replay_gate_summary.csv, runs/m1112_materialized_actor_update_full_public_gate/source_diverse_protected_diagnostic/replay_gate_summary.csv
- parent_config: experiments/manifests/m1113-v4-public-base-materialized-actor-update-proof-washout-audit.json
- parent_objective: design failed wrong-history retention before another actor update
- derived_from: m1113-v4-public-base-materialized-actor-update-proof-washout-audit
- blocked_by: M1113 finds wrong-history branches became safe while normal branches stayed successful
- supersedes: None
- invalidates: retrying M1110 backup candidates without retention design, longer materialized actor update without rejected-history trajectory retention, PPO from the failed exact-improving candidate

## Success Criteria

- design artifact exists
- failed-row selection rule is explicit
- trajectory or replay-retention target is explicit
- post-update exact/replay/behavior gates are explicit
- next route is explicit
- no actor training, PPO, replay, corpus export, mining, promotion, or private holdout occurs

## Failure Criteria

- design artifact is missing
- failed-row selection is ambiguous
- retention target is ambiguous
- post-update gates are ambiguous
- actor training, PPO, replay, corpus export, mining, promotion, or private holdout starts

## Evidence Gates

- M1114 must design only
- M1114 must not train actor weights
- M1114 must not run PPO
- M1114 must not run replay
- M1114 must not build or export corpus
- M1114 must not mine rows
- M1114 must not promote
- M1114 must not use private holdout
- M1114 must preserve actor inputs

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train actor weights
- do not run PPO
- do not run replay
- do not build or export corpus
- do not mine rows
- do not promote
- do not use private holdout
- do not change actor inputs
- do not weaken replay gates
- do not try backup M1110 candidates

## Failure Taxonomy

- proof_washout

## Scoreboard

- milestone: m1114-v4-public-base-materialized-failed-wrong-history-retention-design
- type: gate
- checkpoint: docs/m1114-v4-public-base-materialized-failed-wrong-history-retention-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: materialized_failed_wrong_history_retention_design_admit_export
- reason: M1114 designs failed wrong-history registry and target-base trajectory retention export while forbidding direct short-family hidden-state anchors

## Next Blocker

m1115-v4-public-base-materialized-failed-wrong-history-retention-export
