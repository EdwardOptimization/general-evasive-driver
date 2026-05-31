# m1952-executable-v2-task-quality-offtrack-support-repair-calibrated-source-mining-implementation Research Review

## Summary

- Generated at UTC: 20260531T095222Z
- Type: infrastructure
- Gate tier: process
- Promotion decision: task_quality_calibrated_source_mining_pass_route_to_result_audit
- Decision reason: M1952 calibrated no-rollout source-mining passes with support 130 accepted cells 5981 anchor 64/64 public-gate support 40 calibrated fallback uses 64 split 32/32 and guardrail 0

## Hypothesis

Applying the M1950 calibrated fallback artifact to the full source-mining adapter will repair the anchor-neighborhood gate while preserving non-anchor support and guardrails.

## Lineage

- parent_checkpoint: not_applicable_task_quality_offtrack_support_calibrated_source_mining
- parent_dataset: docs/m1951-executable-v2-task-quality-offtrack-support-repair-calibrated-source-mining-application-design.md, runs/m1950_executable_v2_task_quality_offtrack_support_repair_anchor_fallback_geometry_calibration/selected_anchor_fallback_geometry.json, configs/executable_v2_task_quality_offtrack_support_repair_candidates_v0.json, runs/m1928_executable_v2_task_quality_scenario_redesign_materialization_preflight/executable_task_specs.json
- parent_config: experiments/manifests/m1951-executable-v2-task-quality-offtrack-support-repair-calibrated-source-mining-application-design.json
- parent_objective: implement calibrated fallback artifact input and rerun no-rollout offtrack-support source mining
- derived_from: m1951-executable-v2-task-quality-offtrack-support-repair-calibrated-source-mining-application-design
- blocked_by: M1951 requires artifact-provenanced calibrated fallback application before rerunning full source mining
- supersedes: manual source-mining rerun with patched constants, rerunning M1947 without calibrated fallback artifact
- invalidates: None

## Success Criteria

- focused tests pass
- runs/m1952_executable_v2_task_quality_offtrack_support_repair_calibrated_source_mining/summary.json exists
- result_class is evaluated
- calibrated_anchor_fallback_used_count equals 64
- source-kind support gates are evaluated
- guardrail violation count is zero

## Failure Criteria

- focused tests fail
- calibrated source-mining summary is missing
- calibrated fallback provenance is missing
- source-kind gate failure is not routed to audit
- reset rollout ranking or paper-level claims are made

## Evidence Gates

- M1952 must implement --anchor-fallback-geometry support with tests
- M1952 must run only no-rollout source mining
- M1952 must preserve the original M1947 source-kind support gates
- M1952 must write calibrated fallback provenance metrics
- M1952 must keep reset rollout measured execution profile tuning ranking paper and level3 claims blocked

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

- milestone: m1952-executable-v2-task-quality-offtrack-support-repair-calibrated-source-mining-implementation
- type: infrastructure
- checkpoint: runs/m1952_executable_v2_task_quality_offtrack_support_repair_calibrated_source_mining/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: task_quality_calibrated_source_mining_pass_route_to_result_audit
- reason: M1952 calibrated no-rollout source-mining passes with support 130 accepted cells 5981 anchor 64/64 public-gate support 40 calibrated fallback uses 64 split 32/32 and guardrail 0

## Next Blocker

m1952-executable-v2-task-quality-offtrack-support-repair-calibrated-source-mining-implementation
