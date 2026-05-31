# m1956-executable-v2-task-quality-calibrated-source-materialization-selector-implementation Research Review

## Summary

- Generated at UTC: 20260531T101648Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: task_quality_calibrated_materialization_selector_pass_route_to_preflight_command_design
- Decision reason: M1956 selector pass selected 80 supported sources from M1952 with expected workload 960 source-kind quota pass calibrated anchor 16/16 success surface 12/12 duplicate 0 guardrail 0

## Hypothesis

The M1955 deterministic selector can create an 80-source calibrated materialization subset from M1952 supported source rows while preserving source-kind, role, surface, and calibrated-anchor provenance quotas.

## Lineage

- parent_checkpoint: not_applicable_task_quality_calibrated_source_materialization_selector
- parent_dataset: docs/m1955-executable-v2-task-quality-calibrated-source-materialization-design.md, runs/m1952_executable_v2_task_quality_offtrack_support_repair_calibrated_source_mining/repair_source_rows.csv, runs/m1952_executable_v2_task_quality_offtrack_support_repair_calibrated_source_mining/repair_accepted_cells.csv, runs/m1952_executable_v2_task_quality_offtrack_support_repair_calibrated_source_mining/summary.json
- parent_config: experiments/manifests/m1955-executable-v2-task-quality-calibrated-source-materialization-design.json
- parent_objective: implement deterministic calibrated source materialization selector and emit source-only subset
- derived_from: m1955-executable-v2-task-quality-calibrated-source-materialization-design
- blocked_by: M1955 defines materialization quotas but no selector or subset artifact exists
- supersedes: manual selection from M1952 calibrated source rows, direct reset validation over all M1952 supported source rows without source-kind balancing
- invalidates: None

## Success Criteria

- configs/executable_v2_task_quality_calibrated_materialization_subset_v0.json exists
- runs/m1956_executable_v2_task_quality_calibrated_source_materialization_selector/summary.json exists
- selected_source_count is 80
- source-kind quotas are anchor 32 success 24 offtrack 8 mitigation 16
- calibrated anchor selected count is 32 with 16 post-friction-step and 16 steady-surface
- success-stabilizer selected count is 24 with 12 post-friction-step and 12 steady-surface
- all 16 mitigation-isolation supported rows are selected
- selected_supported_source_count is 80
- duplicate_candidate_source_id_count is 0
- labels_enter_actor_input_count is 0
- ranking_admissible_by_default_count is 0
- profile_specific_tuning_count is 0
- guardrail_violation_count is 0
- focused tests pass
- no reset rollout measured execution training replay PPO ranking or paper-level claim is made

## Failure Criteria

- subset artifact is missing
- summary is missing
- selection counts fail
- calibrated-anchor provenance checks fail
- actor-input or ranking guardrails fail
- reset rollout measured execution training replay or PPO is run
- controller ranking or paper-level claims are made

## Evidence Gates

- M1956 must select exactly 80 supported M1952 source rows
- M1956 must match M1955 source-kind quotas 32 anchor 24 success 8 offtrack 16 mitigation
- M1956 must preserve calibrated-anchor provenance with 16 post-friction and 16 steady calibrated anchors
- M1956 must preserve success-stabilizer role-surface quotas and all mitigation-isolation rows
- M1956 must write source-only selector artifacts and summary without reset rollout measured execution or ranking
- M1956 must keep controller-family ranking paper claims and level3 self-ID blocked

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

- milestone: m1956-executable-v2-task-quality-calibrated-source-materialization-selector-implementation
- type: infrastructure
- checkpoint: configs/executable_v2_task_quality_calibrated_materialization_subset_v0.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: task_quality_calibrated_materialization_selector_pass_route_to_preflight_command_design
- reason: M1956 selector pass selected 80 supported sources from M1952 with expected workload 960 source-kind quota pass calibrated anchor 16/16 success surface 12/12 duplicate 0 guardrail 0

## Next Blocker

m1956-executable-v2-task-quality-calibrated-source-materialization-selector-implementation
