# M1910 Executable V2 Support-First Task-Quality Repair-Axis Measured Wrapper Command Design

- status: completed
- decision: `task_quality_repair_axis_measured_wrapper_command_design_admit_cli_implementation`
- branch: `paper_route_repair_axis_measured_wrapper`
- parent implementation: `docs/m1909-executable-v2-support-first-task-quality-repair-axis-measured-wrapper-implementation.md`
- real M1902 workload run: `false`
- environment reset/rollout/measured execution in M1910: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Design Result

M1909 added the measured wrapper extension point, but the current module CLI is
still dry-run-only. M1910 therefore fixes the real-execution command contract
and target gates, while routing the next step to CLI implementation rather than
direct measured execution.

## Exact Command Contract

The later measured execution command should be:

```bash
PYTHONPATH=src python -m autodrift.executable_v2_support_first_task_quality_repair_axis_execution \
  --task-quality-repair-axis-matrix runs/m1902_executable_v2_support_first_task_quality_repair_axis_materialization/task_quality_repair_axis_matrix.csv \
  --source-episode-rows runs/m1895_executable_v2_support_first_repaired_bounded_smoke_execution/episode_rows.csv \
  --output-dir runs/m1912_executable_v2_support_first_task_quality_repair_axis_measured_wrapper_execution \
  --eval-seed-base 191200 \
  --measured-execution
```

M1911 must implement the `--measured-execution` CLI mode before this command is
run. The execution milestone should not improvise a new command.

## Target Counts

Targets derived from the M1906 real-matrix preflight:

```text
matrix_row_count: 1536
measured_rollout_row_count: 960
import_postprocess_row_count: 576
combined_panel_row_count: 1536
failure_count: 0
controller_profile_count: 12
source_spec_count: 16
role_surface_count: 8
repair_axis_variant_count: 8

execution_row_kind_counts:
  rollout_geometry_variant: 960
  import_existing_episode: 192
  postprocess_existing_episode: 384

task_quality_axis_counts:
  baseline_and_semantics_retention: 384
  contained_collision_clearance_feasibility: 384
  post_clearance_containment_recovery: 576
  unavoidable_mitigation_semantics: 192

repair_axis_variant_counts:
  contained_clearance_gap_plus: 192
  contained_reaction_distance_plus: 192
  mitigation_scored_semantics: 192
  original_retained: 192
  post_clearance_recovery_corridor_combo: 192
  post_clearance_recovery_window_plus: 192
  post_obstacle_containment_corridor_plus: 192
  role_semantics_only: 192
```

## Required Artifacts For Execution

The measured execution run must write:

- `summary.json`
- `rollout_episode_rows.csv`
- `import_postprocess_episode_rows.csv`
- `episode_rows.csv`
- `failure_rows.csv`
- `task_quality_axis_aggregate.csv`
- `repair_axis_variant_aggregate.csv`
- `execution_row_kind_aggregate.csv`

M1911 should add CLI-focused mocked tests that verify these paths without
running the real M1902 workload.

## Pass Gates For Later Execution

The measured execution milestone may pass only if:

- result class is a real measured execution pass, not a mock pass;
- all target counts above match exactly;
- failure count is `0`;
- guardrail violation count is `0`;
- actor input contract changed is `false`;
- profile-specific tuning is `false`;
- controller-family ranking claim made is `false`;
- paper-level claim made is `false`;
- level3 self-ID claim made is `false`;
- ranking remains blocked until a separate result audit.

## Failure Gates

The measured execution milestone must fail or route to repair if:

- any target count is ambiguous or mismatched;
- any rollout row cannot be joined into the combined panel;
- any import/postprocess row cannot be joined to its source episode;
- the CLI changes actor inputs or controller profile definitions;
- the run emits controller ranking or paper-level claims before audit.

## Supported Claims

Supported:

- the measured-wrapper execution command contract is fixed;
- target counts and expected artifacts are fixed;
- direct execution is still blocked until the CLI mode exists.

Unsupported:

- real measured execution success;
- task-quality repair success;
- controller-family ranking;
- policy improvement;
- paper-level benchmark result;
- level3 self-identification.

## Next

Next milestone:

```text
m1911-executable-v2-support-first-task-quality-repair-axis-measured-wrapper-cli-implementation
```

M1911 should implement the measured CLI mode and focused mocked tests. It must
not run the real M1902 workload.
