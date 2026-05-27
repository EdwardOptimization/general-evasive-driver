# m1093-v4-public-base-source-balanced-compact-corpus-conversion-design Research Review

## Summary

- Generated at UTC: 20260527T185044Z
- Type: gate
- Gate tier: process
- Promotion decision: source_balanced_compact_conversion_design_route_to_compactability_audit
- Decision reason: M1093 finds M1092 aggregate surface passes but direct per-checkpoint compact conversion is sparse especially proof_current 8 rows 4 pairs at cap2; route to compactability audit before conversion

## Hypothesis

The M1092 source-balanced accepted rows can be converted into compact source-capped objective/replay corpora before any future PPO.

## Lineage

- parent_checkpoint: runs/m1073_medium_ppo_failed_row_repair_projection_probe/temporal_projection/checkpoints/m1031_base_row16x4_s40_a1.pt, runs/ppo_m1049_guarded_short_escalation_seed61049/checkpoint.pt, runs/ppo_m1050_guarded_short_repeat_seed61050/checkpoint.pt, runs/ppo_m1050_guarded_short_repeat_seed61051/checkpoint.pt
- parent_dataset: runs/m1092_source_balanced_coverage_expansion_seed109200/balanced_accepted_wrong_history_rows.csv, runs/m1092_source_balanced_coverage_expansion_seed109200/summary.json, docs/m1092-v4-public-base-source-balanced-coverage-expansion-run.md
- parent_config: experiments/manifests/m1092-v4-public-base-source-balanced-coverage-expansion-run.json
- parent_objective: design compact objective/replay corpus conversion for the passed M1092 source-balanced boundary surface
- derived_from: m1092-v4-public-base-source-balanced-coverage-expansion-run
- blocked_by: M1092 produced a passing source-balanced wrong-history boundary export and must be converted before any future PPO
- supersedes: None
- invalidates: routing directly from M1092 proof surface to PPO, using the full 146-row surface without source-capped compact conversion, claiming promotion or private-holdout evidence from M1092

## Success Criteria

- conversion design artifact exists
- source row path is explicit
- compact corpus caps are explicit
- objective sanity commands are explicit
- replay sanity commands are explicit
- no training, PPO, promotion, or private holdout occurs

## Failure Criteria

- design artifact is missing
- compact corpus caps are ambiguous
- objective or replay sanity is missing
- PPO starts
- private holdout is used

## Evidence Gates

- M1093 must design only
- M1093 must not train
- M1093 must not run PPO
- M1093 must not promote
- M1093 must not use private holdout
- M1093 must preserve actor inputs
- M1093 must specify compact corpus caps and replay sanity before conversion

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not promote
- do not use private holdout
- do not change actor inputs
- do not skip replay sanity
- do not treat M1092 as a driver capability promotion

## Failure Taxonomy

- scenario_sampling_failure

## Scoreboard

- milestone: m1093-v4-public-base-source-balanced-compact-corpus-conversion-design
- type: gate
- checkpoint: docs/m1093-v4-public-base-source-balanced-compact-corpus-conversion-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: source_balanced_compact_conversion_design_route_to_compactability_audit
- reason: M1093 finds M1092 aggregate surface passes but direct per-checkpoint compact conversion is sparse especially proof_current 8 rows 4 pairs at cap2; route to compactability audit before conversion

## Next Blocker

m1094-v4-public-base-source-balanced-compactability-audit
