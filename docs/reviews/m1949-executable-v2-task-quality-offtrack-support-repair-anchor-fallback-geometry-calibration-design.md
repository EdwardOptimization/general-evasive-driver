# m1949-executable-v2-task-quality-offtrack-support-repair-anchor-fallback-geometry-calibration-design Research Review

## Summary

- Generated at UTC: 20260531T093805Z
- Type: gate
- Gate tier: process
- Promotion decision: task_quality_anchor_fallback_geometry_calibration_design_admit_implementation
- Decision reason: M1949 designs a no-rollout label-preserving calibration artifact for stable-AEB anchor fallback geometry with explicit selected-surface support floors and guardrails

## Hypothesis

A bounded no-rollout calibration design can repair the stale stable-AEB anchor fallback geometry while preserving source label semantics.

## Lineage

- parent_checkpoint: not_applicable_task_quality_offtrack_support_anchor_fallback_geometry_calibration_design
- parent_dataset: docs/m1948-executable-v2-task-quality-offtrack-support-repair-source-mining-result-audit.md, runs/m1947_executable_v2_task_quality_offtrack_support_repair_source_mining/summary.json, runs/m1947_executable_v2_task_quality_offtrack_support_repair_source_mining/repair_blocked_rows.csv, configs/executable_v2_task_quality_offtrack_support_repair_candidates_v0.json
- parent_config: experiments/manifests/m1948-executable-v2-task-quality-offtrack-support-repair-source-mining-result-audit.json
- parent_objective: design no-rollout stable-AEB anchor fallback geometry calibration before rerunning source mining
- derived_from: m1948-executable-v2-task-quality-offtrack-support-repair-source-mining-result-audit
- blocked_by: M1947 anchor-neighborhood support was 0/64 because stable-AEB fallback geometry classified as aes_feasible
- supersedes: rerunning source mining with the same stable-AEB anchor fallback defaults, relaxing stable-AEB source labels to accept aes_feasible rows
- invalidates: None

## Success Criteria

- docs/m1949-executable-v2-task-quality-offtrack-support-repair-anchor-fallback-geometry-calibration-design.md exists
- calibration inputs outputs and pass gates are explicit
- design preserves stable-AEB label semantics
- source-mining rerun remains deferred
- no reset rollout ranking or paper-level claim is made

## Failure Criteria

- design document is missing
- calibration route relaxes stable-AEB labels
- calibration route requires reset or rollout
- next route is ambiguous
- ranking or paper-level claims are made

## Evidence Gates

- M1949 must design a no-rollout calibration step for stable-AEB anchor fallback geometry
- M1949 must preserve source-kind label semantics rather than relaxing labels
- M1949 must specify calibration inputs outputs and pass gates
- M1949 must keep reset rollout measured execution profile tuning ranking paper and level3 claims blocked

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

- milestone: m1949-executable-v2-task-quality-offtrack-support-repair-anchor-fallback-geometry-calibration-design
- type: gate
- checkpoint: docs/m1949-executable-v2-task-quality-offtrack-support-repair-anchor-fallback-geometry-calibration-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: task_quality_anchor_fallback_geometry_calibration_design_admit_implementation
- reason: M1949 designs a no-rollout label-preserving calibration artifact for stable-AEB anchor fallback geometry with explicit selected-surface support floors and guardrails

## Next Blocker

m1949-executable-v2-task-quality-offtrack-support-repair-anchor-fallback-geometry-calibration-design
