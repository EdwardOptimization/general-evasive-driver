# m1895-executable-v2-support-first-repaired-bounded-smoke-execution Research Review

## Summary

- Generated at UTC: 20260531T042935Z
- Type: gate
- Gate tier: process
- Promotion decision: support_first_repaired_bounded_smoke_execution_pass_route_to_result_audit
- Decision reason: M1895 execution pass 576 rollout rows 384 imports 960 total failure 0 import failure 0 metric complete guardrail 0; interpretation deferred

## Hypothesis

The fixed repaired bounded-smoke workload can execute completely and materialize 576 rollout rows plus 384 imported rows with complete metrics and clean guardrails.

## Lineage

- parent_checkpoint: not_applicable_repaired_bounded_smoke_execution
- parent_dataset: docs/m1894-executable-v2-support-first-repaired-bounded-smoke-execution-command-design.md, runs/m1889_executable_v2_support_first_repaired_runner_adapter_preflight/repaired_measured_executable_specs.json, runs/m1889_executable_v2_support_first_repaired_runner_adapter_preflight/repaired_measured_workload_matrix.csv, runs/m1889_executable_v2_support_first_repaired_runner_adapter_preflight/repaired_measured_import_rows.csv, runs/m1880_executable_v2_support_first_measured_runner_execution/episode_rows.csv
- parent_config: experiments/manifests/m1894-executable-v2-support-first-repaired-bounded-smoke-execution-command-design.json
- parent_objective: run the fixed repaired bounded-smoke public diagnostic workload
- derived_from: m1894-executable-v2-support-first-repaired-bounded-smoke-execution-command-design
- blocked_by: M1894 command design must complete before real repaired bounded-smoke execution
- supersedes: direct repaired bounded-smoke execution without exact command design
- invalidates: None

## Success Criteria

- runs/m1895_executable_v2_support_first_repaired_bounded_smoke_execution/summary.json exists
- summary result_class is executable_v2_support_first_repaired_bounded_smoke_execution_pass
- rollout_episode_count is 576
- import_episode_count is 384
- total_panel_row_count is 960
- failure_count and import_failure_count are 0
- metric_completeness_passed is true
- guardrail_violation_count is 0
- controller-family ranking and paper claims remain blocked

## Failure Criteria

- summary is missing
- execution command diverges from M1894
- target counts fail
- metric completeness fails
- guardrail violations occur
- interpretation or ranking is claimed before audit

## Evidence Gates

- M1895 must run the exact M1894 command
- M1895 must produce 576 rollout rows, 384 import rows, and 960 total panel rows
- M1895 must preserve all guardrails and claim boundaries
- M1895 must defer interpretation to M1896 result audit
- M1895 must keep controller-family ranking blocked

## Holdout Policy

- not_used

## Forbidden Shortcuts

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

- milestone: m1895-executable-v2-support-first-repaired-bounded-smoke-execution
- type: gate
- checkpoint: runs/m1895_executable_v2_support_first_repaired_bounded_smoke_execution/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: support_first_repaired_bounded_smoke_execution_pass_route_to_result_audit
- reason: M1895 execution pass 576 rollout rows 384 imports 960 total failure 0 import failure 0 metric complete guardrail 0; interpretation deferred

## Next Blocker

m1896-executable-v2-support-first-repaired-bounded-smoke-execution-result-audit
