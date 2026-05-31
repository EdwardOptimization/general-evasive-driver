# M1983 Executable V2 Task-Quality Calibrated Repaired Outcome-Support Source-Mining Implementation

- status: completed
- decision: `task_quality_calibrated_outcome_support_source_mining_pass_route_to_result_audit`
- result class: `task_quality_calibrated_outcome_support_source_mining_pass`
- implementation: `src/autodrift/executable_v2_task_quality_calibrated_outcome_support_source_mining.py`
- focused tests: `2 passed`
- summary: `runs/m1983_executable_v2_task_quality_calibrated_outcome_support_source_mining/summary.json`
- source-mining execution: `true`
- reset/rollout/measured execution: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Commands

Focused tests:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q \
  tests/test_executable_v2_task_quality_calibrated_outcome_support_source_mining.py
```

Result:

```text
2 passed
```

No-rollout source mining:

```bash
PYTHONPATH=src python -m autodrift.executable_v2_task_quality_calibrated_outcome_support_source_mining \
  --repair-templates configs/executable_v2_task_quality_calibrated_outcome_support_repair_candidates_v0.json \
  --executable-task-specs runs/m1969_executable_v2_task_quality_calibrated_materialization_preflight_repaired/executable_task_specs.json \
  --anchor-fallback-geometry runs/m1950_executable_v2_task_quality_offtrack_support_repair_anchor_fallback_geometry_calibration/selected_anchor_fallback_geometry.json \
  --output-dir runs/m1983_executable_v2_task_quality_calibrated_outcome_support_source_mining \
  --next-blocker m1984-executable-v2-task-quality-calibrated-repaired-outcome-support-source-mining-result-audit
```

Return code:

```text
0
```

## Result

M1983 passes the M1982 no-rollout source-mining gates:

```text
result_class: task_quality_calibrated_outcome_support_source_mining_pass
input_template_count: 192
source_candidate_count: 192
resolution_failure_count: 0
accepted_cell_count_total: 8358
supported_source_count: 184
public_gate_supported_source_count: 73
unsupported_source_count: 8
guardrail_violation_count: 0
```

Repair-axis support:

```text
offtrack_anchor_relief: 64 / 64 supported, 4032 accepted cells
offtrack_boundary_relief_extension: 32 / 32 supported, 2464 accepted cells
success_support_expansion: 43 / 48 supported, 993 accepted cells
collision_mitigation_relief: 29 / 32 supported, 725 accepted cells
mitigation_metric_isolation: 16 / 16 supported, 144 accepted cells
```

The M1982 floors all pass:

```text
offtrack_anchor_relief_supported_source_count >= 32: pass
offtrack_boundary_relief_extension_supported_source_count >= 8: pass
success_support_expansion_supported_source_count >= 24: pass
collision_mitigation_relief_supported_source_count >= 8: pass
mitigation_metric_isolation_source_count == 16: pass
```

Split and provenance:

```text
source_split_counts:
  public_debug: 112
  public_gate: 80

public_gate_supported_source_count: 73

geometry_source_counts:
  m1969::parent_task_source_id: 48
  m1950_calibrated_anchor_fallback::post_friction_step: 60
  m1950_calibrated_anchor_fallback::steady_surface: 4
  axis_role_fallback::offtrack_boundary_relief_extension::stable_aes_only: 32
  axis_role_fallback::collision_mitigation_relief::unavoidable_mitigation: 31
  axis_role_fallback::collision_mitigation_relief::drift_required_recovery: 1
  axis_role_fallback::mitigation_metric_isolation::unavoidable_mitigation: 15
  axis_role_fallback::mitigation_metric_isolation::drift_required_recovery: 1

calibrated_anchor_fallback_used_count: 64
```

## Unsupported Rows

The remaining `8` unsupported source rows are localized:

```text
success_support_expansion: 5 unsupported
collision_mitigation_relief: 3 unsupported
offtrack_anchor_relief: 0 unsupported
offtrack_boundary_relief_extension: 0 unsupported
mitigation_metric_isolation: 0 unsupported
```

Dominant failure causes:

```text
label_role_mismatch:
  success-support rows with exact M1969 geometry that no longer classify as the
  requested role under the M1983 scan window.

friction_timing_filter_only:
  two post-friction-step unavoidable collision-relief rows whose accepted
  labels exist but fail the minimum time-after-friction-step filter.
```

These failures do not block the M1982 support floors, but M1984 should audit
whether the `8` unsupported rows should be excluded from materialization,
repaired, or kept as diagnostics.

## Artifacts

M1983 wrote:

```text
runs/m1983_executable_v2_task_quality_calibrated_outcome_support_source_mining/summary.json
runs/m1983_executable_v2_task_quality_calibrated_outcome_support_source_mining/outcome_support_source_rows.csv
runs/m1983_executable_v2_task_quality_calibrated_outcome_support_source_mining/outcome_support_accepted_cells.csv
runs/m1983_executable_v2_task_quality_calibrated_outcome_support_source_mining/outcome_support_blocked_rows.csv
runs/m1983_executable_v2_task_quality_calibrated_outcome_support_source_mining/resolution_failure_rows.csv
runs/m1983_executable_v2_task_quality_calibrated_outcome_support_source_mining/repair_axis_aggregate.csv
runs/m1983_executable_v2_task_quality_calibrated_outcome_support_source_mining/split_aggregate.csv
runs/m1983_executable_v2_task_quality_calibrated_outcome_support_source_mining/role_surface_aggregate.csv
runs/m1983_executable_v2_task_quality_calibrated_outcome_support_source_mining/claim_boundary.csv
```

## Supported Claims

M1983 supports:

- the M1980 `192`-candidate outcome-support repair templates can be mapped into
  a no-rollout source-supported accepted-cell set;
- the previous offtrack-only blocker is repaired at source-mining level:
  offtrack anchor relief and offtrack-boundary relief extension both have full
  source support;
- collision-mitigation relief has enough source support for an audit to decide
  bounded materialization;
- all guardrails remain clean and no labels enter actor inputs.

M1983 does not support:

- executable reset validity;
- measured rollout success;
- controller-family ranking;
- finite-window vs GRU conclusion;
- policy improvement;
- paper-level benchmark result;
- level3 self-identification.

## Next

Next milestone:

```text
m1984-executable-v2-task-quality-calibrated-repaired-outcome-support-source-mining-result-audit
```

M1984 should audit the supported and unsupported rows before any
materialization, reset validation, measured execution, or ranking decision.
