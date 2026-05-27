# m1115-v4-public-base-materialized-failed-wrong-history-retention-export Research Review

## Summary

- Generated at UTC: 20260527T205556Z
- Type: infrastructure
- Gate tier: proof
- Promotion decision: materialized_failed_wrong_history_retention_export_pass_route_to_actor_update_design
- Decision reason: M1115 reproduces 47 lost success-drop events with 0 normal-lost and 47 wrong-history-safe events plus 19 target-base rows in a 707-row rejected-history anchor while keeping 28 short-family rows diagnostic-only and writing a 4664-row combined anchor without promotion

## Hypothesis

The M1112 failed wrong-history rows can be exported into a deterministic registry and target-base trajectory anchor without using short-family hidden states.

## Lineage

- parent_checkpoint: runs/m1073_medium_ppo_failed_row_repair_projection_probe/temporal_projection/checkpoints/m1031_base_row16x4_s40_a1.pt
- parent_dataset: docs/m1114-v4-public-base-materialized-failed-wrong-history-retention-design.md, runs/m1112_materialized_actor_update_full_public_gate/summary.json, runs/m1112_materialized_actor_update_full_public_gate/proof_replay_summary.csv, runs/m1112_materialized_actor_update_full_public_gate/family_intersection_public_gate/replay_gate_summary.csv, runs/m1112_materialized_actor_update_full_public_gate/source_diverse_protected_diagnostic/replay_gate_summary.csv
- parent_config: experiments/manifests/m1114-v4-public-base-materialized-failed-wrong-history-retention-design.json
- parent_objective: export failed wrong-history registry and target-base rejected trajectory anchor
- derived_from: m1114-v4-public-base-materialized-failed-wrong-history-retention-design
- blocked_by: M1114 requires target-base materialization before training from failed wrong-history rows
- supersedes: None
- invalidates: using short-family hidden states directly as training anchors, actor update before failed-row retention export, PPO before failed-row retention export

## Success Criteria

- failed_wrong_history_events.csv exists
- failed event count is 47
- normal_lost count is 0
- wrong_history_safe count is 47
- target_base_failed_rows.csv exists
- family_source_failed_rows.csv exists
- target_base_rejected_trajectory_anchor.npz loads
- combined_target_base_rejected_anchor.npz loads
- short-family rows are not included in training anchor
- no actor training, PPO, replay, mining, promotion, or private holdout occurs

## Failure Criteria

- failed event count mismatch
- normal_lost count is nonzero
- anchor includes short-family hidden states
- anchor load sanity fails
- actor training, PPO, replay, mining, promotion, or private holdout starts

## Evidence Gates

- M1115 may implement/export failed-row registry and target-base trajectory anchors
- M1115 must not train actor weights
- M1115 must not run PPO
- M1115 must not run replay
- M1115 must not mine new rows
- M1115 must not promote
- M1115 must not use private holdout
- M1115 must preserve actor inputs
- M1115 must not use short-family hidden states as training anchors

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train actor weights
- do not run PPO
- do not run replay
- do not mine new rows
- do not promote
- do not use private holdout
- do not change actor inputs
- do not weaken replay gates
- do not try backup M1110 candidates
- do not use short-family hidden states as training anchors

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1115-v4-public-base-materialized-failed-wrong-history-retention-export
- type: infrastructure
- checkpoint: runs/m1115_materialized_failed_wrong_history_retention_export/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: materialized_failed_wrong_history_retention_export_pass_route_to_actor_update_design
- reason: M1115 reproduces 47 lost success-drop events with 0 normal-lost and 47 wrong-history-safe events plus 19 target-base rows in a 707-row rejected-history anchor while keeping 28 short-family rows diagnostic-only and writing a 4664-row combined anchor without promotion

## Next Blocker

m1115-v4-public-base-materialized-failed-wrong-history-retention-export
