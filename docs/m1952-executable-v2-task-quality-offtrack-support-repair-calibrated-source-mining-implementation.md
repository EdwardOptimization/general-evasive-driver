# M1952 Executable V2 Task-Quality Offtrack Support Repair Calibrated Source-Mining Implementation

- status: completed
- decision: `task_quality_calibrated_source_mining_pass_route_to_result_audit`
- result class: `task_quality_offtrack_support_repair_source_mining_pass`
- branch: `paper_route_task_quality_offtrack_support_repair`
- implementation: `src/autodrift/executable_v2_task_quality_offtrack_support_repair_source_mining.py`
- focused tests: `5 passed`
- summary: `runs/m1952_executable_v2_task_quality_offtrack_support_repair_calibrated_source_mining/summary.json`
- reset/rollout/measured execution in M1952: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Command

```bash
PYTHONPATH=src python -m autodrift.executable_v2_task_quality_offtrack_support_repair_source_mining \
  --repair-templates configs/executable_v2_task_quality_offtrack_support_repair_candidates_v0.json \
  --executable-task-specs runs/m1928_executable_v2_task_quality_scenario_redesign_materialization_preflight/executable_task_specs.json \
  --anchor-fallback-geometry runs/m1950_executable_v2_task_quality_offtrack_support_repair_anchor_fallback_geometry_calibration/selected_anchor_fallback_geometry.json \
  --output-dir runs/m1952_executable_v2_task_quality_offtrack_support_repair_calibrated_source_mining \
  --next-blocker m1953-executable-v2-task-quality-offtrack-support-repair-calibrated-source-mining-result-audit
```

Return code:

```text
0
```

## Result

The calibrated no-rollout source-mining run passed the full source-kind gate:

```text
result_class: task_quality_offtrack_support_repair_source_mining_pass
input_template_count: 160
source_candidate_count: 160
resolution_failure_count: 0
accepted_cell_count_total: 5981
supported_source_count: 130
public_gate_supported_source_count: 40
guardrail_violation_count: 0
```

Source-kind support:

```text
anchor_neighborhood:        64 / 64 supported
success_stabilizer:        39 / 48 supported
offtrack_boundary_relief:  11 / 32 supported
mitigation_isolation_check: 16 / 16 supported
```

Calibrated fallback provenance:

```text
calibrated_anchor_fallback_used_count: 64
calibrated_anchor_fallback_used_by_surface:
  post_friction_step: 32
  steady_surface: 32
```

Relative to M1947, the calibrated fallback fixed the localized blocker:

```text
anchor_neighborhood_supported_source_count: 0 -> 64
supported_source_count: 66 -> 130
accepted_cell_count_total: 1949 -> 5981
```

Non-anchor support did not regress:

```text
success_stabilizer:        39 -> 39
offtrack_boundary_relief:  11 -> 11
mitigation_isolation_check: 16 -> 16
public_gate_supported_source_count: 40 -> 40
```

## Implementation Notes

The adapter now accepts:

```text
--anchor-fallback-geometry <selected_anchor_fallback_geometry.json>
```

It applies calibrated fallback only to:

```text
repair_source_kind == anchor_neighborhood
source_role_semantics == stable_aeb
sampled_obstacle_label == aeb_feasible
surface_variant in {post_friction_step, steady_surface}
no exact M1928 source geometry resolved
```

Rows using the calibrated artifact are marked with:

```text
base_geometry_source = m1950_calibrated_anchor_fallback::<surface_variant>
```

All exact-source and non-anchor rows preserve the M1947 behavior.

## Supported Claims

M1952 supports:

- the artifact-provenanced calibrated fallback input path exists and is
  test-covered;
- the full no-rollout offtrack-support repair source-mining pass is now
  recovered;
- the previous M1947 blocker was indeed localized to stable-AEB anchor fallback
  geometry;
- the branch can move to result audit before any reset/materialized execution.

## Unsupported Claims

Still unsupported:

- reset validity for the repaired source set;
- measured execution readiness;
- controller-family ranking;
- finite-window vs GRU conclusion;
- paper-level benchmark result;
- level3 self-identification.

## Next

Next milestone:

```text
m1953-executable-v2-task-quality-offtrack-support-repair-calibrated-source-mining-result-audit
```

M1953 should audit M1952 and choose the next route. Because the offtrack-support
repair branch is at the workflow synthesis cadence, it should route to branch
synthesis before another narrow implementation or execution milestone.
