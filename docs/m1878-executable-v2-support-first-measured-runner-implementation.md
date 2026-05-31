# M1878 Executable V2 Support-First Measured Runner Implementation

- status: completed
- decision: `support_first_measured_runner_implementation_pass_admit_execution_command_design`
- branch: `paper_route_executable_v2_support_first_measured_execution`
- parent design: `docs/m1877-executable-v2-support-first-measured-runner-execution-design.md`
- runner: `src/autodrift/executable_v2_support_first_measured_runner_execution.py`
- tests: `tests/test_executable_v2_support_first_measured_runner_execution.py`
- real measured rollout run in M1878: false
- policy action executed in M1878: false
- training/replay/PPO: false

## Purpose

M1878 implements the support-first measured runner wrapper required by M1877.
The implementation reuses the shared one-cell rollout helper but owns the
support-first loaders, metadata passthrough fields, support-first aggregates,
metric completeness checks, failure rows, and resumability state.

## Implemented Runner Contract

The runner loads:

```text
support_first_measured_executable_specs
support_first_measured_workload_matrix.csv
```

and indexes executable specs by `task_source_id`. Each completed episode row
preserves:

```text
support_first_workload_id
support_first_v2_panel_spec_id
support_first_materialized_v2_panel_spec_id
source_scenario_spec_id
controller_profile_name
scenario_profile_name
scenario_profile_group
role_panel_id
v2_role_surface_id
surface_variant
hidden_dynamics_bucket
road_boundary_bucket
obstacle_timing_bucket
obstacle_lateral_bucket
sampled_obstacle_label
allowed_labels_metadata_only
```

The wrapper also enforces the diagnostic claim boundary:

```text
controller_family_ranking_claim_made: false
paper_level_claim_made: false
level3_self_id_claim_made: false
training/replay/PPO/promoted/private_holdout: false
```

## Output Artifacts Defined

The runner writes:

```text
summary.json
episode_rows.csv
failure_rows.csv
run_state.json
profile_aggregate.csv
controller_profile_aggregate.csv
role_panel_aggregate.csv
role_surface_aggregate.csv
surface_variant_aggregate.csv
scenario_profile_aggregate.csv
hidden_dynamics_bucket_aggregate.csv
road_boundary_bucket_aggregate.csv
obstacle_timing_bucket_aggregate.csv
obstacle_lateral_bucket_aggregate.csv
sampled_obstacle_label_aggregate.csv
outcome_aggregate.csv
termination_reason_aggregate.csv
controller_profile_role_panel_aggregate.csv
controller_profile_role_surface_aggregate.csv
profile_outcome_aggregate.csv
role_panel_outcome_aggregate.csv
role_surface_outcome_aggregate.csv
profile_hidden_dynamics_worst_bucket.csv
metric_completeness_summary.csv
metric_completeness_failures.csv
```

## Focused Verification

Command:

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q tests/test_executable_v2_support_first_measured_runner_execution.py
```

Result:

```text
4 passed in 2.20s
```

The tests monkeypatch `run_workload_cell`, `_load_profile_cache`, and profile
discovery. They verify:

- pass summary over a toy support-first workload;
- support-first metadata and controller profile identity are preserved;
- required aggregates and metric completeness artifacts are written;
- resume skips completed workload ids without duplicate episode rows;
- row-level exceptions are persisted in `failure_rows.csv`;
- the loader rejects a non-support-first JSON key.

## Claim Boundary

Supported by M1878:

```text
support-first measured runner wrapper exists
focused tests passed
support-first metadata, aggregates, failure rows, and resume behavior are implemented
M1879 execution-command design is admissible
```

Not supported by M1878:

```text
real 2160-episode measured rollout result
controller-family ranking
paper-level benchmark evidence
current-response / finite-window / GRU comparison result
level3 self-identification evidence
```

## Decision

M1878 passes as infrastructure. The next step is M1879: fix the exact
support-first measured runner execution command and pass criteria before
running the real 2160-episode public diagnostic workload.
