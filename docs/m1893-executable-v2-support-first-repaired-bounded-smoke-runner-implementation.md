# M1893 Executable V2 Support-First Repaired Bounded-Smoke Runner Implementation

- status: completed
- decision: `support_first_repaired_bounded_smoke_runner_implementation_pass_admit_execution_command_design`
- branch: `paper_route_executable_v2_support_first_measured_execution`
- parent design: `docs/m1891-executable-v2-support-first-repaired-bounded-smoke-execution-design.md`
- parent synthesis: `docs/m1892-executable-v2-support-first-measured-execution-branch-synthesis.md`
- runner: `src/autodrift/executable_v2_support_first_repaired_bounded_smoke_execution.py`
- tests: `tests/test_executable_v2_support_first_repaired_bounded_smoke_execution.py`
- real measured rollout run in M1893: false
- policy action executed in M1893: false
- training/replay/PPO: false

## Purpose

M1893 implements the repaired bounded-smoke execution wrapper specified by
M1891 and admitted again by M1892 synthesis. This is still an infrastructure
milestone: focused tests use monkeypatched rollout helpers and do not run the
real `576`-episode repaired smoke.

## Implemented Runner Contract

The wrapper loads:

```text
support_first_repaired_measured_executable_specs
repaired_measured_workload_matrix.csv
repaired_measured_import_rows.csv
source episode rows from M1880
```

It runs only rows with:

```text
execution_row_kind == rollout_geometry_variant
```

and writes new rollout rows to:

```text
rollout_episode_rows.csv
```

It imports original and semantics-only rows from source episode metrics into:

```text
import_episode_rows.csv
```

then combines rollout and import rows into:

```text
episode_rows.csv
```

The wrapper makes imported rows unique by using `repaired_import_row_id` as the
combined-panel `workload_id`, while preserving `base_workload_id` and
`import_source_episode_workload_id`.

## Provenance And Metadata

Every combined panel row preserves support-first and repair metadata including:

```text
repair_row_id
repair_source_key
repair_variant_id
repair_variant_kind
geometry_variant_id
success_semantics_variant_id
role_semantics_id
base_workload_id
base_support_first_workload_id
base_task_source_id
base_support_first_v2_panel_spec_id
execution_row_kind
semantic_recompute_required
```

Rollout rows mark:

```text
environment_rollout_started: true
measured_rollout_started: true
policy_action_executed: true
imported_episode_row: false
```

Imported rows mark:

```text
environment_rollout_started: false
measured_rollout_started: false
policy_action_executed: false
imported_episode_row: true
```

They also retain source flags as:

```text
source_environment_rollout_started
source_measured_rollout_started
source_policy_action_executed
```

This keeps provenance explicit during later post-execution audit.

## Output Artifacts Implemented

The wrapper writes:

```text
summary.json
episode_rows.csv
rollout_episode_rows.csv
import_episode_rows.csv
failure_rows.csv
import_failure_rows.csv
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
repair_variant_aggregate.csv
repair_variant_kind_aggregate.csv
geometry_variant_aggregate.csv
success_semantics_variant_aggregate.csv
execution_row_kind_aggregate.csv
controller_profile_repair_variant_aggregate.csv
controller_profile_role_surface_repair_variant_aggregate.csv
role_surface_repair_variant_aggregate.csv
repair_variant_outcome_aggregate.csv
outcome_aggregate.csv
termination_reason_aggregate.csv
import_rollout_alignment.csv
profile_hidden_dynamics_worst_bucket.csv
metric_completeness_summary.csv
metric_completeness_failures.csv
```

It also checks target counts for:

```text
576 rollout episodes
384 import episodes
960 combined panel rows
12 controller profiles
16 selected source specs
48 repaired executable specs
4 role panels
8 role surfaces
5 repair variants
3 rollout variants
2 import variants
```

The real target counts are defaults. Focused tests use smaller target counts.

## Focused Verification

Command:

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q tests/test_executable_v2_support_first_repaired_bounded_smoke_execution.py
```

Result:

```text
4 passed in 2.05s
```

Compile check:

```text
python -m compileall -q src tests
```

Result:

```text
passed
```

The focused tests verify:

- rollout and import rows merge into a combined panel;
- imported rows keep source metrics but row-level new-rollout flags are false;
- repair metadata and provenance survive in output rows;
- repaired aggregate and alignment artifacts are written;
- resume skips completed rollout rows while rebuilding deterministic imports;
- missing import source rows produce `import_failure_rows.csv`;
- the loader rejects the old non-repaired JSON key.

## Claim Boundary

Supported by M1893:

```text
support-first repaired bounded-smoke runner wrapper exists
focused tests passed
rollout/import provenance, repair metadata, repaired aggregates, and resume behavior are implemented
M1894 execution-command design is admissible
```

Not supported by M1893:

```text
real 576-rollout repaired bounded-smoke result
repaired task-quality conclusion
controller-family ranking
paper-level benchmark evidence
current-response / finite-window / GRU verdict
level3 self-identification evidence
```

## Decision

M1893 passes as infrastructure. The next step is M1894: fix the exact repaired
bounded-smoke execution command and pass criteria before running the real
`576`-rollout plus `384`-import public diagnostic workload.
