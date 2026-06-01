# M2183 Paper-Route Current-Sim Repeat Measured Execution Command Design

- status: completed
- decision: `current_sim_repeat_measured_execution_command_design_admit_implementation_and_run`
- manifest: `experiments/manifests/m2183-paper-route-current-sim-repeat-measured-execution-command-design.json`
- training in M2183: `false`
- measured execution in M2183: `false`
- controller-family ranking claim made: `false`
- winner selected: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Inputs

Executable specs:

```text
runs/m2151_paper_route_current_sim_controlled_comparison_executable_spec_materialization/executable_task_specs.json
```

Repeat workload:

```text
runs/m2177_paper_route_current_sim_training_seed_repeat_materialization/combined_new_repeat_materialized_workload.csv
```

Audited counts:

```text
workload rows: 640
unique task specs: 40
unique profiles: 8
training repeat groups: 2
```

The workload has first-class repeat metadata columns:

```text
training_repeat_id
training_seed_group
profile_training_seed
profile_checkpoint_source_profile
checkpoint_materialization_mode
base_workload_id
```

## Frozen Command

M2184 may run only this command:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.paper_route_current_sim_controlled_comparison_measured_runner \
  --executable-task-specs runs/m2151_paper_route_current_sim_controlled_comparison_executable_spec_materialization/executable_task_specs.json \
  --workload runs/m2177_paper_route_current_sim_training_seed_repeat_materialization/combined_new_repeat_materialized_workload.csv \
  --output-dir runs/m2184_paper_route_current_sim_repeat_measured_execution \
  --eval-seed-base 218400 \
  --device cpu \
  --no-resume \
  --target-episode-count 640 \
  --target-spec-count 40 \
  --target-profile-count 8 \
  --next-blocker m2185-paper-route-current-sim-repeat-measured-execution-result-audit
```

Expected output:

```text
runs/m2184_paper_route_current_sim_repeat_measured_execution/summary.json
```

## Pass Gates for M2184

M2184 should be considered an execution pass only if:

```text
episode_count == 640
failure_count == 0
metadata_missing_count == 0
metric_completeness_failure_count == 0
spec_count == 40
profile_count == 8
task_family/profile/history quotas pass
training_repeat_aggregate.csv exists
guardrail_violation_count == 0
```

## Claim Boundary

M2183 only freezes the command. It does not execute rollout.

Still blocked:

```text
repeat measured execution result;
profile ranking;
winner selection;
finite-window vs GRU verdict;
paper-level benchmark evidence;
level3 self-identification.
```

## Next Step

M2184 may execute the frozen command. Interpretation and comparison remain
blocked until M2185 audits the result.
