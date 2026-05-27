# m1116-v4-public-base-failed-wrong-history-retention-actor-update-design Research Review

## Summary

- Generated at UTC: 20260527T210137Z
- Type: gate
- Gate tier: proof
- Promotion decision: failed_wrong_history_retention_actor_update_design_route_to_branch_synthesis
- Decision reason: M1116 designs a lower-lr actor_coupling probe using M1107 exact objective plus M1115 combined trajectory retention and target-base-only anchor gates then routes to cadence synthesis before implementation

## Hypothesis

A bounded actor-update probe can be designed that uses M1115 target-base rejected-history trajectory retention together with M1107 exact objective before any replay or PPO.

## Lineage

- parent_checkpoint: runs/m1073_medium_ppo_failed_row_repair_projection_probe/temporal_projection/checkpoints/m1031_base_row16x4_s40_a1.pt
- parent_dataset: runs/m1115_materialized_failed_wrong_history_retention_export/summary.json, runs/m1115_materialized_failed_wrong_history_retention_export/failed_wrong_history_events.csv, runs/m1115_materialized_failed_wrong_history_retention_export/target_base_failed_rows.csv, runs/m1115_materialized_failed_wrong_history_retention_export/family_source_failed_rows.csv, runs/m1115_materialized_failed_wrong_history_retention_export/combined_target_base_rejected_anchor.npz
- parent_config: experiments/manifests/m1115-v4-public-base-materialized-failed-wrong-history-retention-export.json
- parent_objective: design a bounded actor update that combines M1107 exact objective with M1115 target-base rejected-history trajectory retention
- derived_from: m1115-v4-public-base-materialized-failed-wrong-history-retention-export
- blocked_by: M1112 proof washout made wrong-history branches safe, M1115 exported target-base retention anchors but did not train
- supersedes: None
- invalidates: actor update without target-base failed wrong-history retention, direct training from short-family hidden states, PPO before rejected-history retention gate design

## Success Criteria

- M1115 artifacts are cited and load requirements are included
- actor update train scope is restricted
- exact M1107 objective no-regression is a pre-replay gate
- target-base failed-row trajectory-anchor loss no-regression is a pre-replay gate
- short-family rows remain replay diagnostics unless materialized
- old public, source-diverse, family-intersection, and behavior gate order is specified
- no actor training, PPO, replay, promotion, or private holdout occurs

## Failure Criteria

- design uses short-family hidden states directly as training anchors
- design admits training before M1115 anchor sanity
- design lacks exact objective or trajectory-anchor no-regression gates
- design weakens replay gates or allows promotion
- actor training, PPO, replay, promotion, or private holdout starts

## Evidence Gates

- M1116 may design an actor-update probe using M1115 target-base retention artifacts
- M1116 must not train actor weights
- M1116 must not run PPO
- M1116 must not run replay
- M1116 must not promote
- M1116 must not use private holdout
- M1116 must keep short-family rows replay-only unless target-policy materialization is explicitly designed
- M1116 must preserve actor inputs

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train actor weights
- do not run PPO
- do not run replay
- do not promote
- do not use private holdout
- do not change actor inputs
- do not weaken replay gates
- do not use short-family hidden states as training anchors
- do not rerun M1110 backup candidates

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1116-v4-public-base-failed-wrong-history-retention-actor-update-design
- type: gate
- checkpoint: docs/m1116-v4-public-base-failed-wrong-history-retention-actor-update-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: failed_wrong_history_retention_actor_update_design_route_to_branch_synthesis
- reason: M1116 designs a lower-lr actor_coupling probe using M1107 exact objective plus M1115 combined trajectory retention and target-base-only anchor gates then routes to cadence synthesis before implementation

## Next Blocker

m1117-v4-public-base-materialized-objective-branch-synthesis
