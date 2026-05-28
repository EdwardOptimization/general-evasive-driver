# m1290-paper-route-source-history-directional-conflict-audit Research Review

## Summary

- Generated at UTC: 20260528T141857Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: source_history_directional_conflict_magnitude_compression_route_to_directional_repair_design
- Decision reason: M1290 confirms M1288 is magnitude compression: 152/152 losses improve but 152/152 rows remain mutually exclusive and both_directional_fraction stays zero

## Hypothesis

A no-training directional conflict audit can explain why M1288 reduces exact loss while leaving both_directional_fraction at zero.

## Lineage

- parent_checkpoint: runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt, runs/m1288_source_history_objective_only_update/checkpoints/raw_objective_update.pt
- parent_dataset: docs/m1289-paper-route-source-history-objective-only-update-result-audit.md, runs/m1288_source_history_objective_only_update/summary.json, runs/m1288_source_history_objective_only_update/source_history_objective_rows_before.csv, runs/m1288_source_history_objective_only_update/source_history_objective_rows_after.csv
- parent_config: experiments/manifests/m1289-paper-route-source-history-objective-only-update-result-audit.json
- parent_objective: quantify row-wise directional conflict after exact-loss-positive actor_mean_only update
- derived_from: m1289-paper-route-source-history-objective-only-update-result-audit
- blocked_by: M1288 improves exact loss but both_directional_fraction remains 0.0
- supersedes: blindly increasing actor_mean_only update steps after M1288
- invalidates: None

## Success Criteria

- runs/m1290_source_history_directional_conflict_audit/summary.json exists
- directional_conflict_rows.csv exists
- before and after sign-quadrant counts are reproduced
- audit classifies the M1288 update mechanism
- next branch step is explicit
- no training, PPO, promotion, private holdout, threshold relaxation, or actor-input expansion occurs

## Failure Criteria

- run artifacts are missing
- sign-quadrant counts cannot be reproduced
- audit ignores both_directional_fraction=0.0
- audit starts training or PPO
- audit overclaims self-identification
- private holdout, promotion, threshold relaxation, or actor-input expansion occurs

## Evidence Gates

- M1290 must not train
- M1290 must not run PPO
- M1290 must not use private holdout
- M1290 must not promote
- M1290 must quantify before-after sign quadrants
- M1290 must quantify paired-row symmetry or conflict
- M1290 must decide whether next step is longer actor_mean continuation, directional objective repair, trainable-scope escalation, or source-history refresh

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not promote
- do not use private holdout
- do not add actor inputs
- do not infer closed-loop performance from row-wise objective CSVs
- do not overclaim self-identification

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1290-paper-route-source-history-directional-conflict-audit
- type: infrastructure
- checkpoint: runs/m1290_source_history_directional_conflict_audit/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: source_history_directional_conflict_magnitude_compression_route_to_directional_repair_design
- reason: M1290 confirms M1288 is magnitude compression: 152/152 losses improve but 152/152 rows remain mutually exclusive and both_directional_fraction stays zero

## Next Blocker

m1291-paper-route-source-history-directional-repair-design
