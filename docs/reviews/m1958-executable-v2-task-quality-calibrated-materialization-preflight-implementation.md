# m1958-executable-v2-task-quality-calibrated-materialization-preflight-implementation Research Review

## Summary

- Generated at UTC: 20260531T102844Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: task_quality_calibrated_materialization_preflight_pass_route_to_reset_command_design
- Decision reason: M1958 no-reset preflight pass creates 80 executable specs and 960 planned workload rows with missing accepted 0 contract 0 forbidden-key 0 missing profile 0 guardrail 0

## Hypothesis

A focused no-reset preflight adapter can convert the M1956 calibrated source subset into 80 executable task specs and 960 planned workload rows while preserving source metadata, accepted-cell provenance, and guardrails.

## Lineage

- parent_checkpoint: not_applicable_task_quality_calibrated_materialization_preflight
- parent_dataset: docs/m1957-executable-v2-task-quality-calibrated-materialization-preflight-command-design.md, configs/executable_v2_task_quality_calibrated_materialization_subset_v0.json, runs/m1956_executable_v2_task_quality_calibrated_source_materialization_selector/summary.json, runs/m1952_executable_v2_task_quality_offtrack_support_repair_calibrated_source_mining/repair_accepted_cells.csv, runs/m1674_controller_family_one_seed_public_pilot
- parent_config: experiments/manifests/m1957-executable-v2-task-quality-calibrated-materialization-preflight-command-design.json
- parent_objective: implement focused no-reset calibrated materialization preflight adapter
- derived_from: m1957-executable-v2-task-quality-calibrated-materialization-preflight-command-design
- blocked_by: M1957 determines the M1928 preflight is not an exact schema match for M1956 selected sources
- supersedes: attempting to reuse M1928 materialization preflight without schema adaptation
- invalidates: None

## Success Criteria

- runs/m1958_executable_v2_task_quality_calibrated_materialization_preflight/summary.json exists
- runs/m1958_executable_v2_task_quality_calibrated_materialization_preflight/executable_task_specs.json exists
- runs/m1958_executable_v2_task_quality_calibrated_materialization_preflight/planned_workload.csv exists
- result_class is task_quality_calibrated_materialization_preflight_pass
- executable_task_spec_count is 80
- planned_workload_cell_count is 960
- missing_accepted_cell_count is 0
- forbidden_key_violation_count is 0
- contract_violation_count is 0
- guardrail_violation_count is 0
- focused tests pass
- no reset rollout measured execution training replay PPO ranking or paper-level claim is made

## Failure Criteria

- summary is missing
- executable task specs are missing
- planned workload is missing
- target counts fail
- accepted-cell provenance is missing
- contract or forbidden-key checks fail
- reset rollout measured execution training replay or PPO is run
- controller ranking or paper-level claims are made

## Evidence Gates

- M1958 must implement the focused calibrated materialization preflight adapter
- M1958 must create exactly 80 executable task specs and 960 planned workload rows
- M1958 must preserve M1956 source metadata and M1952 accepted-cell provenance
- M1958 must pass human-view contract and forbidden-key checks without reset or rollout
- M1958 must keep controller-family ranking paper claims and level3 self-ID blocked

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

- milestone: m1958-executable-v2-task-quality-calibrated-materialization-preflight-implementation
- type: infrastructure
- checkpoint: runs/m1958_executable_v2_task_quality_calibrated_materialization_preflight/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: task_quality_calibrated_materialization_preflight_pass_route_to_reset_command_design
- reason: M1958 no-reset preflight pass creates 80 executable specs and 960 planned workload rows with missing accepted 0 contract 0 forbidden-key 0 missing profile 0 guardrail 0

## Next Blocker

m1958-executable-v2-task-quality-calibrated-materialization-preflight-implementation
