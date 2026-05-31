# M1902 Executable V2 Support-First Task-Quality Repair-Axis Materialization

- status: completed
- decision: `task_quality_repair_axis_materialization_pass_route_to_result_audit`
- manifest: `experiments/manifests/m1902-executable-v2-support-first-task-quality-repair-axis-materialization.json`
- helper: `src/autodrift/executable_v2_support_first_task_quality_repair_axis_materialization.py`
- focused tests: `2 passed`
- summary: `runs/m1902_executable_v2_support_first_task_quality_repair_axis_materialization/summary.json`
- reset/rollout in M1902: false
- measured execution in M1902: false
- training/replay/PPO: false
- controller-family ranking claim made: false
- paper-level claim made: false
- level3 self-ID claim made: false

## Command

```bash
PYTHONPATH=src python -m autodrift.executable_v2_support_first_task_quality_repair_axis_materialization \
  --episode-rows runs/m1895_executable_v2_support_first_repaired_bounded_smoke_execution/episode_rows.csv \
  --role-surface-conflict-aggregate runs/m1899_executable_v2_support_first_clearance_containment_conflict_localization/role_surface_conflict_aggregate.csv \
  --output-dir runs/m1902_executable_v2_support_first_task_quality_repair_axis_materialization \
  --target-source-spec-count 16 \
  --target-controller-profile-count 12 \
  --target-repair-axis-variant-count 8 \
  --target-matrix-row-count 1536 \
  --target-original-retained-row-count 192 \
  --next-blocker m1903-executable-v2-support-first-task-quality-repair-axis-materialization-result-audit
```

## Result

M1902 passes as a no-rollout materialization artifact:

```text
result_class: task_quality_repair_axis_materialization_pass
source episode rows read: 960
base original rows: 192
source specs: 16
controller profiles: 12
role surfaces: 8
repair-axis variants: 8
repair-axis matrix rows: 1536 / 1536
original_retained rows: 192
geometry rollout variant rows scheduled for later design: 960
role-surface axis target rows: 25
duplicate axis keys: 0
guardrail violation count: 0
```

Variant counts:

```text
original_retained: 192
role_semantics_only: 192
post_clearance_recovery_window_plus: 192
post_obstacle_containment_corridor_plus: 192
post_clearance_recovery_corridor_combo: 192
contained_clearance_gap_plus: 192
contained_reaction_distance_plus: 192
mitigation_scored_semantics: 192
```

Axis counts:

```text
baseline_and_semantics_retention: 384
post_clearance_containment_recovery: 576
contained_collision_clearance_feasibility: 384
unavoidable_mitigation_semantics: 192
```

Applicability counts:

```text
all: 384
targeted: 960
diagnostic_control: 192
```

All pre-registered checks passed:

```text
target_source_spec_count_passed: true
target_controller_profile_count_passed: true
target_repair_axis_variant_count_passed: true
target_matrix_row_count_passed: true
target_original_retained_row_count_passed: true
expected_matrix_row_count_passed: true
all_controller_profiles_represented: true
all_role_surfaces_represented: true
all_variants_nonempty: true
original_baseline_retained: true
duplicate_axis_key_count_zero: true
guardrail_violation_count_zero: true
```

## Artifacts

M1902 wrote:

```text
runs/m1902_executable_v2_support_first_task_quality_repair_axis_materialization/summary.json
runs/m1902_executable_v2_support_first_task_quality_repair_axis_materialization/task_quality_repair_axis_matrix.csv
runs/m1902_executable_v2_support_first_task_quality_repair_axis_materialization/task_quality_repair_axis_spec.json
runs/m1902_executable_v2_support_first_task_quality_repair_axis_materialization/role_surface_axis_target_map.csv
runs/m1902_executable_v2_support_first_task_quality_repair_axis_materialization/duplicate_axis_keys.csv
```

The matrix is still diagnostic materialization, not execution. Rows with
`execution_row_kind == rollout_geometry_variant` are scheduled candidates for a
later execution design; no environment reset or rollout was started in M1902.

## Implementation Note

The helper originally counted historical M1895 parent rollout flags as M1902
guardrail violations. That was wrong because M1902 consumes prior execution
provenance but does not run rollout itself. The implementation now applies
M1902 guardrails to rows produced by the M1902 materializer, and the focused
test covers historical parent rollout flags.

## Decision

Route to:

```text
m1903-executable-v2-support-first-task-quality-repair-axis-materialization-result-audit
```

M1903 must audit the materialized matrix before any execution design. Direct
measured execution, controller-family ranking, training, PPO, paper-level
claims, and level3 self-ID claims remain blocked.

## Claim Boundary

Supported:

- the M1901 eight-variant repair-axis matrix was materialized;
- baseline support-first metadata, all controller profiles, all role surfaces,
  and the original baseline are preserved;
- no reset, rollout, training, PPO, ranking, paper, or self-ID claim was made.

Unsupported:

- task-quality repair success;
- controller-family ranking;
- policy improvement claim;
- paper-level benchmark result;
- level3 self-identification evidence.
