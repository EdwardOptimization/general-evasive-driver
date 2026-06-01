# M2204 Paper-Route Current-Sim Offtrack-Support Measured-Execution Implementation and Run

- status: completed
- decision: `current_sim_offtrack_support_measured_execution_metadata_validation_fail_route_to_audit`
- manifest: `experiments/manifests/m2204-paper-route-current-sim-offtrack-support-measured-execution-implementation-and-run.json`
- run artifact: `runs/m2204_paper_route_current_sim_offtrack_support_measured_execution/summary.json`
- command return code: `0`
- real measured execution: `false`
- environment rollout started: `false`
- policy actions executed: `false`
- training/replay/PPO in M2204: `false`
- controller-family ranking claim made: `false`
- winner selected: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Command

M2204 ran the frozen M2203 command:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.paper_route_current_sim_controlled_comparison_measured_runner \
  --executable-task-specs runs/m2194_paper_route_current_sim_offtrack_support_candidate_materialization/repaired_executable_task_specs.json \
  --workload runs/m2200_paper_route_current_sim_offtrack_support_measured_readiness/materialized_workload.csv \
  --output-dir runs/m2204_paper_route_current_sim_offtrack_support_measured_execution \
  --eval-seed-base 220400 \
  --device cpu \
  --no-resume \
  --target-episode-count 2304 \
  --target-spec-count 288 \
  --target-profile-count 8 \
  --next-blocker m2205-paper-route-current-sim-offtrack-support-measured-execution-result-audit
```

## Result

The runner failed closed during metadata validation before environment rollout:

```text
result_class: current_sim_controlled_comparison_measured_execution_incomplete_or_fail
episode_count: 0
target_episode_count: 2304
spec_count: 0
target_spec_count: 288
profile_count: 0
target_profile_count: 8
failure_count: 0
metadata_missing_count: 2304
metric_completeness_failure_count: 0
guardrail_violation_count: 0
environment_rollout_started: false
policy_action_executed: false
measured_rollout_started: false
```

Validation failure rows show the same missing repeat-metadata fields across all
`2304` workload rows:

```text
missing_repeat_metadata_field: training_repeat_id                    2304
missing_repeat_metadata_field: training_seed_group                   2304
missing_repeat_metadata_field: profile_training_seed                 2304
missing_repeat_metadata_field: profile_checkpoint_source_profile     2304
missing_repeat_metadata_field: base_workload_id                      2304
```

The direct interpretation is narrow:

```text
The measured runner currently requires repeat-workload metadata even when the
input workload is a non-repeat checkpoint-complete repaired panel.
```

This is a pre-rollout metadata validation failure, not driver-performance
evidence.

## Artifacts

Written artifacts:

```text
runs/m2204_paper_route_current_sim_offtrack_support_measured_execution/summary.json
runs/m2204_paper_route_current_sim_offtrack_support_measured_execution/failure_rows.csv
runs/m2204_paper_route_current_sim_offtrack_support_measured_execution/validation_failure_rows.csv
runs/m2204_paper_route_current_sim_offtrack_support_measured_execution/metadata_missing_rows.csv
runs/m2204_paper_route_current_sim_offtrack_support_measured_execution/metric_completeness_failures.csv
runs/m2204_paper_route_current_sim_offtrack_support_measured_execution/profile_aggregate.csv
runs/m2204_paper_route_current_sim_offtrack_support_measured_execution/profile_level_aggregate.csv
runs/m2204_paper_route_current_sim_offtrack_support_measured_execution/history_representation_aggregate.csv
runs/m2204_paper_route_current_sim_offtrack_support_measured_execution/task_family_aggregate.csv
runs/m2204_paper_route_current_sim_offtrack_support_measured_execution/outcome_aggregate.csv
runs/m2204_paper_route_current_sim_offtrack_support_measured_execution/termination_reason_aggregate.csv
runs/m2204_paper_route_current_sim_offtrack_support_measured_execution/claim_boundary.csv
runs/m2204_paper_route_current_sim_offtrack_support_measured_execution/run_state.json
```

No `episode_rows.csv` artifact was produced because no rollout started.

## Claim Boundary

Supported by M2204:

```text
The frozen measured-execution command failed closed before rollout on missing
repeat-metadata fields, with no guardrail violation and no policy action
execution.
```

Unsupported by M2204:

```text
measured rollout success;
controller-family ranking;
policy performance comparison;
finite-window vs GRU verdict;
paper-level benchmark evidence;
level3 self-identification.
```

## Next

M2205 must audit whether this is a workload materialization metadata gap, a
measured-runner validation overreach for non-repeat workloads, or a required
normalization step. It must not repair or rerun before classifying the failure.
