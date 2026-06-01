# M2172 Paper-Route Current-Sim Checkpoint/Profile Materialization Result Audit

- status: completed
- decision: `current_sim_checkpoint_profile_materialization_audit_admit_measured_execution_command_design`
- manifest: `experiments/manifests/m2172-paper-route-current-sim-checkpoint-profile-materialization-result-audit.json`
- audited summary: `runs/m2171_paper_route_current_sim_checkpoint_profile_materialization/summary.json`
- audited profile rows: `runs/m2171_paper_route_current_sim_checkpoint_profile_materialization/profile_checkpoint_rows.csv`
- audited workload: `runs/m2171_paper_route_current_sim_checkpoint_profile_materialization/materialized_workload.csv`
- real M2151 measured execution in M2172: `false`
- policy actions executed in M2172: `false`
- training/replay/PPO in M2172: `false`
- controller-family ranking claim made: `false`
- winner selected: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Audit Checks

M2172 audits M2171 without rerunning training or measured execution.

Summary checks:

```text
result_class = current_sim_checkpoint_profile_materialization_pass
profile_count = 8
trainable_profile_count = 7
alias_profile_count = 1
training_command_count = 7
successful_training_command_count = 7
failed_training_command_count = 0
materialized_workload_count = 320
checkpoint_path_present_count = 320
checkpoint_path_missing_count = 0
checkpoint_path_exists_count = 320
guardrail_violation_count = 0
```

Independent CSV checks:

```text
profile_rows = 8
workload_rows = 320
missing_checkpoint_paths = 0
nonexistent_checkpoint_paths = 0
reset_alias_matches_online = true
reset_training_started = false
unique_checkpoint_paths = 7
```

The `unique_checkpoint_paths == 7` count is expected because
`L3_reset_control` intentionally shares the `L3_online_gru` checkpoint.

## Supported Claims

Supported:

```text
The M2151 current-sim workload now has existing checkpoint paths for all 320
rows.
```

Supported:

```text
The current-sim checkpoint panel follows the M2170 fairness rule: seven
profiles train from their frozen configs, and the reset-control profile aliases
the online-GRU weights.
```

Supported:

```text
The checkpoint/profile materialization output is clean enough to admit a
measured-execution command design milestone.
```

## Still Unsupported

Still unsupported:

```text
driver performance;
controller-family ranking;
winner selection;
finite-window vs GRU verdict;
paper-level benchmark evidence;
level3 self-identification.
```

No measured execution has been run on the M2171 materialized workload yet.

## Failure Taxonomy

Closed blocker:

```text
checkpoint/profile materialization gap:
  checkpoint_path_missing_count changed from 320 in M2165 to 0 in M2171.
```

No evidence of:

```text
contract_violation
profile_specific_tuning
private_holdout_contamination
metric_artifact
controller ranking overclaim
```

## Decision

Decision: `current_sim_checkpoint_profile_materialization_audit_admit_measured_execution_command_design`.

M2173 may design the measured execution command over:

```text
executable_task_specs:
  runs/m2151_paper_route_current_sim_controlled_comparison_executable_spec_materialization/executable_task_specs.json

materialized workload:
  runs/m2171_paper_route_current_sim_checkpoint_profile_materialization/materialized_workload.csv

runner:
  python -m autodrift.paper_route_current_sim_controlled_comparison_measured_runner
```

M2173 must not run measured execution. It should freeze the command, output
directory, eval seed base, targets, and claim boundary for a later execution
milestone.
