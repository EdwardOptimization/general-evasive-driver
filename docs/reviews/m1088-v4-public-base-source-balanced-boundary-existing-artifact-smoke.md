# m1088-v4-public-base-source-balanced-boundary-existing-artifact-smoke Research Review

## Summary

- Generated at UTC: 20260527T165957Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: source_balanced_existing_artifact_smoke_export_limited_route_to_relocation_run_design
- Decision reason: M1088 finds pre-boundary source budget ready with 371 eligible physical pairs and 370 selected pairs but the existing boundary export remains six-pair limited

## Hypothesis

The new source-balanced boundary tooling can cheaply classify whether the existing M1083 artifacts contain enough pre-boundary source diversity and whether post-export balance remains impossible without a new relocation run.

## Lineage

- parent_checkpoint: runs/m1073_medium_ppo_failed_row_repair_projection_probe/temporal_projection/checkpoints/m1031_base_row16x4_s40_a1.pt
- parent_dataset: runs/m1083_proof_hardened_retarget_outcome_seed108200/outcome_interventions.csv, runs/m1083_proof_hardened_retarget_boundary_surface_seed108200/boundary_relocation_rows.csv, docs/m1086-v4-public-base-source-balanced-boundary-tooling-implementation.md, docs/training-stage-discipline.md
- parent_config: experiments/manifests/m1087-staged-training-discipline-harness-rule.json
- parent_objective: run source-balanced boundary accounting over existing M1083 artifacts without new mining
- derived_from: m1086-v4-public-base-source-balanced-boundary-tooling-implementation, m1087-staged-training-discipline-harness-rule
- blocked_by: M1086 implemented tooling but has not yet measured existing M1083 artifacts through the new source-budget path
- supersedes: m1087-v4-public-base-source-balanced-boundary-existing-artifact-smoke
- invalidates: claiming the new tooling fixes M1083 without running it on existing artifacts, rerunning full matched-current or boundary relocation mining before a cheap artifact smoke

## Success Criteria

- source-balanced artifact smoke runs on existing M1083 CSVs
- source_budget_summary.json exists
- balanced_accepted_wrong_history_rows.csv exists
- summary distinguishes budget-limited from export-limited failure
- no training, PPO, promotion, private holdout, or full new mining run occurs

## Failure Criteria

- artifact smoke cannot read existing M1083 CSVs
- tooling requires full mining to run
- training, PPO, promotion, or private holdout starts
- robustness thresholds are weakened

## Evidence Gates

- M1088 must not train
- M1088 must not run PPO
- M1088 must not promote
- M1088 must not use private holdout
- M1088 must not run a full new mining pipeline
- M1088 must use existing M1083 CSV artifacts only
- M1088 must preserve existing robustness thresholds

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not promote
- do not use private holdout
- do not rerun matched-current mining
- do not rerun boundary relocation
- do not lower robustness thresholds

## Failure Taxonomy

- scenario_sampling_failure

## Scoreboard

- milestone: m1088-v4-public-base-source-balanced-boundary-existing-artifact-smoke
- type: infrastructure
- checkpoint: runs/m1088_source_balanced_boundary_existing_artifact_smoke/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: source_balanced_existing_artifact_smoke_export_limited_route_to_relocation_run_design
- reason: M1088 finds pre-boundary source budget ready with 371 eligible physical pairs and 370 selected pairs but the existing boundary export remains six-pair limited

## Next Blocker

m1089-v4-public-base-source-balanced-relocation-run-design
