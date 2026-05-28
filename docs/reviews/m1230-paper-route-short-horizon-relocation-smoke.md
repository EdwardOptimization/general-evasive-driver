# m1230-paper-route-short-horizon-relocation-smoke Research Review

## Summary

- Generated at UTC: 20260528T081254Z
- Type: gate
- Gate tier: proof
- Promotion decision: short_horizon_relocation_partial_source_collapsed_audit_required
- Decision reason: M1230 produced 80 short-horizon accepted wrong-history success-drop rows but failed source-diversity gates with one target two left steps one checkpoint and one margin bucket

## Hypothesis

The M1227 relocation grid may materialize wrong-history margin degradation under the M1222-compatible short horizon where exact source geometry remains normal-success.

## Lineage

- parent_checkpoint: runs/m1212_corrected_profile_repeat/profile_runs/L3_online_gru/seed_111602/checkpoint.pt
- parent_dataset: runs/m1226_terminal_boundary_candidate_export/candidate_outcomes.csv, runs/m1229_source_geometry_consistency_short/summary.json, runs/m1229_source_geometry_consistency_long/summary.json, docs/m1229-paper-route-source-geometry-consistency-audit.md
- parent_config: experiments/manifests/m1229-paper-route-source-geometry-consistency-audit.json, configs/paper_route_corrected_profiles/m1207_l3_online_gru.json
- parent_objective: test whether M1226 action-divergent candidates can be materialized under the short horizon where source geometry is replay-consistent
- derived_from: m1229-paper-route-source-geometry-consistency-audit
- blocked_by: long-horizon exact source geometry collides for all selected M1226 candidates
- supersedes: long-horizon relocation over short-horizon-safe candidates
- invalidates: claiming M1227 all-collision result as a source-schema failure

## Success Criteria

- runs/m1230_short_horizon_relocation_smoke/summary.json exists
- runs/m1230_short_horizon_relocation_smoke/boundary_relocation_rows.csv exists
- source budget and candidate selection pass before replay
- accepted wrong-history rows, if any, are reported with source-diversity accounting
- private holdout remains unused
- no training, PPO, promotion, private holdout, profile tuning, or actor-input contract expansion occurs
- next audit or fallback route is selected

## Failure Criteria

- M1230 trains or tunes profiles
- private holdout is used
- accepted rows are claimed without source-diversity accounting
- short-horizon rows are claimed as long-horizon performance
- next route is left vague

## Evidence Gates

- M1230 may run bounded short-horizon relocation replay only
- M1230 must preserve actor input contract
- M1230 must not train controllers
- M1230 must not run PPO
- M1230 must not use private holdout
- M1230 must not promote
- M1230 must scope any positive result to short-horizon materialization
- M1230 must not claim long-horizon evasive-driver performance or self-identification

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not use private holdout
- do not promote
- do not add hidden or oracle actor inputs
- do not claim long-horizon performance from short-horizon accepted rows
- do not weaken accepted-row criteria
- do not accept single-source active-set collapse

## Failure Taxonomy

- scenario_sampling_failure

## Scoreboard

- milestone: m1230-paper-route-short-horizon-relocation-smoke
- type: gate
- checkpoint: runs/m1230_short_horizon_relocation_smoke/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: short_horizon_relocation_partial_source_collapsed_audit_required
- reason: M1230 produced 80 short-horizon accepted wrong-history success-drop rows but failed source-diversity gates with one target two left steps one checkpoint and one margin bucket

## Next Blocker

m1231-paper-route-short-horizon-partial-positive-audit
