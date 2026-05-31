# m1951-executable-v2-task-quality-offtrack-support-repair-calibrated-source-mining-application-design Research Review

## Summary

- Generated at UTC: 20260531T094751Z
- Type: gate
- Gate tier: process
- Promotion decision: task_quality_calibrated_source_mining_application_design_admit_implementation
- Decision reason: M1951 designs an artifact-provenanced --anchor-fallback-geometry path for the full no-rollout source-mining rerun while preserving M1947 source-kind gates

## Hypothesis

The M1950 calibrated fallback artifact can be wired into the source-mining adapter through an explicit no-rollout rerun design that preserves M1947 gates.

## Lineage

- parent_checkpoint: not_applicable_task_quality_offtrack_support_calibrated_source_mining_application_design
- parent_dataset: docs/m1950-executable-v2-task-quality-offtrack-support-repair-anchor-fallback-geometry-calibration-implementation.md, runs/m1950_executable_v2_task_quality_offtrack_support_repair_anchor_fallback_geometry_calibration/summary.json, runs/m1950_executable_v2_task_quality_offtrack_support_repair_anchor_fallback_geometry_calibration/selected_anchor_fallback_geometry.json, configs/executable_v2_task_quality_offtrack_support_repair_candidates_v0.json
- parent_config: experiments/manifests/m1950-executable-v2-task-quality-offtrack-support-repair-anchor-fallback-geometry-calibration-implementation.json
- parent_objective: design calibrated fallback application to the full offtrack-support repair source-mining adapter
- derived_from: m1950-executable-v2-task-quality-offtrack-support-repair-anchor-fallback-geometry-calibration-implementation
- blocked_by: M1950 produced calibrated stable-AEB fallback geometry, but the full M1947 source-mining adapter does not yet consume it
- supersedes: manual patching of source-mining fallback constants without a design, rerunning M1947 with stale fallback geometry
- invalidates: None

## Success Criteria

- docs/m1951-executable-v2-task-quality-offtrack-support-repair-calibrated-source-mining-application-design.md exists
- design specifies calibrated fallback artifact input and output directory
- design preserves original M1947 source-kind support gates
- next implementation route is explicit
- no reset rollout ranking or paper-level claim is made

## Failure Criteria

- design document is missing
- design hard-codes calibrated geometry without artifact provenance
- design weakens source-kind or label gates
- next route is ambiguous
- ranking or paper-level claims are made

## Evidence Gates

- M1951 must design how the source-mining adapter consumes selected_anchor_fallback_geometry.json
- M1951 must preserve M1947 source-kind support gates
- M1951 must specify exact command outputs and pass/fail routing for the calibrated no-rollout rerun
- M1951 must keep reset rollout measured execution profile tuning ranking paper and level3 claims blocked

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run environment reset
- do not run environment rollout
- do not execute policy actions
- do not run measured execution
- do not train
- do not run replay
- do not run PPO
- do not promote a checkpoint
- do not use private holdout
- do not change actor inputs
- do not tune controller profiles
- do not rank controller families
- do not relax stable-AEB anchors to accept aes_feasible labels
- do not claim paper-level evidence
- do not claim level3 self-identification

## Failure Taxonomy

- scenario_sampling_failure

## Scoreboard

- milestone: m1951-executable-v2-task-quality-offtrack-support-repair-calibrated-source-mining-application-design
- type: gate
- checkpoint: docs/m1951-executable-v2-task-quality-offtrack-support-repair-calibrated-source-mining-application-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: task_quality_calibrated_source_mining_application_design_admit_implementation
- reason: M1951 designs an artifact-provenanced --anchor-fallback-geometry path for the full no-rollout source-mining rerun while preserving M1947 source-kind gates

## Next Blocker

m1951-executable-v2-task-quality-offtrack-support-repair-calibrated-source-mining-application-design
