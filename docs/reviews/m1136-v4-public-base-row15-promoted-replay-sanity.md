# m1136-v4-public-base-row15-promoted-replay-sanity Research Review

## Summary

- Generated at UTC: 20260527T223117Z
- Type: gate
- Gate tier: proof
- Promotion decision: row15_promoted_replay_sanity_source_gate_pass_route_to_cross_family_audit
- Decision reason: M1136 passes source-policy replay gate for 172 rows but cross-family report has 34 failed duplicate geometry groups so direct mixed-family objective remains blocked

## Hypothesis

M1134 aggregate rows reproduce source-policy normal-history success and wrong-history failure under replay.

## Lineage

- parent_checkpoint: runs/m1123_row15_unsafe_margin_projection_probe/checkpoints/alpha_0_15.pt
- parent_dataset: runs/m1134_row15_promoted_family_aggregate_conversion/family_aggregate_boundary_rows.csv, docs/m1135-v4-public-base-row15-promoted-replay-sanity-design.md
- parent_config: experiments/manifests/m1135-v4-public-base-row15-promoted-replay-sanity-design.json
- parent_objective: run source-aware replay sanity for M1134 aggregate rows
- derived_from: m1135-v4-public-base-row15-promoted-replay-sanity-design
- blocked_by: source-aware replay sanity has not been run
- supersedes: None
- invalidates: objective conversion before replay sanity, training on aggregate rows before replay sanity

## Success Criteria

- source_policy_source_rows_replay.csv exists
- source_policy_gate_summary.csv exists
- cross_family_replay_rows.csv exists
- cross_family_policy_summary.csv exists
- duplicate_geometry_replay_summary.csv exists
- failed_duplicate_geometry_groups.csv exists
- summary.json exists
- source_row_count == 172
- normal_success_count == 172
- wrong_history_success_count == 0
- success_drop_count == 172
- physical_pairs >= 12
- checkpoints >= 4
- targets >= 2
- no actor training, PPO, objective optimization, promotion, private holdout, or actor-input change occurs

## Failure Criteria

- source-policy source-row gate fails
- cross-family report is missing
- duplicate geometry report is missing
- actor training, PPO, objective optimization, promotion, private holdout, or actor-input change starts

## Evidence Gates

- M1136 may run only the M1135 pre-registered replay sanity command
- M1136 must not train actor weights
- M1136 must not run PPO
- M1136 must not run objective optimization
- M1136 must not promote
- M1136 must not use private holdout
- M1136 must preserve actor inputs

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train actor weights
- do not run PPO
- do not run objective optimization
- do not promote
- do not use private holdout
- do not change actor inputs
- do not skip cross-family report
- do not skip duplicate-geometry failure report

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1136-v4-public-base-row15-promoted-replay-sanity
- type: gate
- checkpoint: runs/m1136_row15_promoted_family_aggregate_replay_sanity/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: row15_promoted_replay_sanity_source_gate_pass_route_to_cross_family_audit
- reason: M1136 passes source-policy replay gate for 172 rows but cross-family report has 34 failed duplicate geometry groups so direct mixed-family objective remains blocked

## Next Blocker

m1137-v4-public-base-row15-promoted-cross-family-replay-audit
