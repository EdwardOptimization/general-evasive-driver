# m1980-executable-v2-task-quality-calibrated-repaired-outcome-support-repair-template-implementation Research Review

## Summary

- Generated at UTC: 20260531T121530Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: task_quality_calibrated_outcome_support_repair_templates_pass_route_to_audit
- Decision reason: M1980 template tests 2 passed and no-rollout artifact pass 192 candidates exact quotas split 112/80 no holdout no actor labels guardrail 0

## Hypothesis

The M1979 repair design can be materialized into a deterministic 192-candidate no-rollout template artifact with clean guardrails.

## Lineage

- parent_checkpoint: not_applicable_task_quality_calibrated_repaired_outcome_support_repair_template
- parent_dataset: docs/m1979-executable-v2-task-quality-calibrated-repaired-outcome-support-repair-design.md, runs/m1977_executable_v2_task_quality_calibrated_repaired_measured_outcome_localization/summary.json, runs/m1977_executable_v2_task_quality_calibrated_repaired_measured_outcome_localization/offtrack_dominance_rows.csv, runs/m1977_executable_v2_task_quality_calibrated_repaired_measured_outcome_localization/collision_dominance_rows.csv, runs/m1977_executable_v2_task_quality_calibrated_repaired_measured_outcome_localization/success_source_rows.csv
- parent_config: experiments/manifests/m1979-executable-v2-task-quality-calibrated-repaired-outcome-support-repair-design.json
- parent_objective: implement deterministic no-rollout calibrated outcome-support repair template generator
- derived_from: m1979-executable-v2-task-quality-calibrated-repaired-outcome-support-repair-design
- blocked_by: repair templates have not yet been materialized
- supersedes: manual ad hoc repair candidate selection
- invalidates: None

## Success Criteria

- focused template tests pass
- configs/executable_v2_task_quality_calibrated_outcome_support_repair_candidates_v0.json exists
- candidate_source_count equals 192
- repair-axis quota counts match M1979
- public_debug_count equals 112
- public_gate_count equals 80
- paper_holdout_candidate_count equals 0
- labels_enter_actor_input_count equals 0
- profile_specific_tuning_count equals 0
- guardrail_violation_count equals 0

## Failure Criteria

- template artifact is missing
- candidate source count differs from 192
- repair-axis quotas fail
- labels enter actor input
- profile-specific tuning ranking paper or self-ID claims are made
- environment reset rollout or measured execution is run

## Evidence Gates

- M1980 must implement only no-rollout template generation
- M1980 must produce exactly 192 candidate source templates with designed quotas
- M1980 must preserve no-label-to-actor and no-ranking guardrails
- M1980 must keep reset rollout measured execution ranking paper and self-ID claims blocked

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
- do not claim paper-level evidence
- do not claim level3 self-identification

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1980-executable-v2-task-quality-calibrated-repaired-outcome-support-repair-template-implementation
- type: infrastructure
- checkpoint: configs/executable_v2_task_quality_calibrated_outcome_support_repair_candidates_v0.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: task_quality_calibrated_outcome_support_repair_templates_pass_route_to_audit
- reason: M1980 template tests 2 passed and no-rollout artifact pass 192 candidates exact quotas split 112/80 no holdout no actor labels guardrail 0

## Next Blocker

m1980-executable-v2-task-quality-calibrated-repaired-outcome-support-repair-template-implementation
