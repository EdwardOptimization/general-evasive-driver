# M1903 Executable V2 Support-First Task-Quality Repair-Axis Materialization Result Audit

- status: completed
- decision: `task_quality_repair_axis_materialization_audit_admit_execution_design`
- audited summary: `runs/m1902_executable_v2_support_first_task_quality_repair_axis_materialization/summary.json`
- reset/rollout in M1903: false
- measured execution in M1903: false
- training/replay/PPO: false
- controller-family ranking claim made: false
- paper-level claim made: false
- level3 self-ID claim made: false

## Artifact Integrity

M1902 passes the materialization audit:

```text
result_class: task_quality_repair_axis_materialization_pass
source_episode_row_count: 960
base_original_row_count: 192
source_spec_count: 16
controller_profile_count: 12
role_surface_count: 8
repair_axis_variant_count: 8
repair_axis_matrix_row_count: 1536
expected_repair_axis_matrix_row_count: 1536
original_retained_row_count: 192
duplicate_axis_key_count: 0
guardrail_violation_count: 0
```

All count gates passed:

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

M1902 wrote the required artifacts:

```text
summary.json
task_quality_repair_axis_matrix.csv
task_quality_repair_axis_spec.json
role_surface_axis_target_map.csv
duplicate_axis_keys.csv
```

## Matrix Interpretation

M1902 produced the intended eight-variant repair-axis matrix:

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

The panel is execution-ready as a diagnostic workload, but not ranking-ready.
It keeps source/profile comparability and supports later slicing by axis,
variant, role surface, and target/control applicability.

## Why Direct Execution Is Still Blocked

The materialized matrix has mixed row kinds:

```text
rollout_geometry_variant rows: 960
import_existing_episode / postprocess_existing_episode rows: 576
```

The existing repaired bounded-smoke runner cannot be used directly because the
new matrix:

- uses `task_quality_repair_axis_matrix.csv`, not the M1889 repaired workload
  schema;
- needs to run only geometry variants;
- needs to import or postprocess three non-geometry variants from M1895 source
  episode rows;
- needs to preserve new axis fields such as `task_quality_axis_id`,
  `repair_axis_variant_id`, `axis_applicability`, target conflict class, and
  source conflict class;
- needs aggregate outputs by repair axis, axis variant, applicability, and role
  surface.

Therefore the correct next step is execution design, not direct measured
execution.

## Decision

Route to:

```text
m1904-executable-v2-support-first-task-quality-repair-axis-execution-design
```

M1904 should design a wrapper/protocol for later execution:

```text
run:
  execution_row_kind == rollout_geometry_variant
  expected rows: 960

import/postprocess:
  execution_row_kind in {import_existing_episode, postprocess_existing_episode}
  expected rows: 576

combined panel:
  expected rows: 1536
```

M1904 must not run rollout. It should specify the wrapper contract, metadata
preservation, import/postprocess joins, pass gates, and output artifacts before
any real execution.

## Claim Boundary

Supported:

- M1902 materialization is count-complete and guardrail-clean;
- the axis-separated matrix is ready for execution design;
- controller ranking remains blocked.

Unsupported:

- task-quality repair success;
- controller-family ranking;
- policy improvement claim;
- paper-level benchmark result;
- level3 self-identification evidence.
