# M1950 Executable V2 Task-Quality Offtrack Support Repair Anchor Fallback Geometry Calibration Implementation

- status: completed
- decision: `task_quality_anchor_fallback_geometry_calibration_pass_route_to_calibrated_source_mining_application_design`
- result class: `task_quality_anchor_fallback_geometry_calibration_pass`
- branch: `paper_route_task_quality_offtrack_support_repair`
- implementation: `src/autodrift/executable_v2_task_quality_offtrack_support_repair_anchor_fallback_geometry_calibration.py`
- focused tests: `2 passed`
- summary: `runs/m1950_executable_v2_task_quality_offtrack_support_repair_anchor_fallback_geometry_calibration/summary.json`
- reset/rollout/measured execution in M1950: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Command

```bash
PYTHONPATH=src python -m autodrift.executable_v2_task_quality_offtrack_support_repair_anchor_fallback_geometry_calibration \
  --repair-templates configs/executable_v2_task_quality_offtrack_support_repair_candidates_v0.json \
  --blocked-rows runs/m1947_executable_v2_task_quality_offtrack_support_repair_source_mining/repair_blocked_rows.csv \
  --output-dir runs/m1950_executable_v2_task_quality_offtrack_support_repair_anchor_fallback_geometry_calibration \
  --next-blocker m1951-executable-v2-task-quality-offtrack-support-repair-calibrated-source-mining-application-design
```

Return code:

```text
0
```

## Result

M1950 implemented and ran the no-rollout calibration step. It produced a
label-correct fallback geometry artifact for both stable-AEB anchor surfaces:

```text
input_anchor_template_count: 64
blocked_anchor_row_count: 64
candidate_fallback_count: 144
selected_surface_count: 2
selected_supported_anchor_count_total: 64
selected_supported_anchor_count_by_surface:
  post_friction_step: 32
  steady_surface: 32
selected_accepted_cell_count_total: 4032
guardrail_violation_count: 0
```

Selected fallback geometry:

```text
post_friction_step:
  speed_ref: 18.0
  mu: 0.40
  obstacle_distance: 52.0
  obstacle_half_width: 0.75
  center_label: aeb_feasible
  supported_anchor_count: 32
  accepted_cell_count_total: 2016

steady_surface:
  speed_ref: 18.0
  mu: 0.40
  obstacle_distance: 52.0
  obstacle_half_width: 0.75
  center_label: aeb_feasible
  supported_anchor_count: 32
  accepted_cell_count_total: 2016
```

The selected geometry is farther from the old fallback than the old M1946
default, but it is label-correct. The old fallback was rejected because it
classified stable-AEB anchors as `aes_feasible`.

## Artifacts

```text
runs/m1950_executable_v2_task_quality_offtrack_support_repair_anchor_fallback_geometry_calibration/summary.json
runs/m1950_executable_v2_task_quality_offtrack_support_repair_anchor_fallback_geometry_calibration/selected_anchor_fallback_geometry.json
runs/m1950_executable_v2_task_quality_offtrack_support_repair_anchor_fallback_geometry_calibration/anchor_fallback_candidates.csv
runs/m1950_executable_v2_task_quality_offtrack_support_repair_anchor_fallback_geometry_calibration/anchor_calibration_source_rows.csv
runs/m1950_executable_v2_task_quality_offtrack_support_repair_anchor_fallback_geometry_calibration/anchor_calibration_accepted_cells.csv
runs/m1950_executable_v2_task_quality_offtrack_support_repair_anchor_fallback_geometry_calibration/anchor_calibration_blocked_rows.csv
runs/m1950_executable_v2_task_quality_offtrack_support_repair_anchor_fallback_geometry_calibration/claim_boundary.csv
```

## Supported Claims

M1950 supports:

- a focused no-rollout calibration tool exists and is test-covered;
- M1947's failed stable-AEB anchor fallback can be replaced with
  label-correct geometry for both surface variants;
- the selected fallback geometry gives `64/64` supported anchor rows in the
  calibration context;
- the next step can design how to apply this calibrated fallback to the full
  M1947 source-mining adapter.

## Unsupported Claims

Still unsupported:

- repaired full source-mining pass;
- reset validity for the repaired source set;
- measured execution readiness;
- controller-family ranking;
- finite-window vs GRU conclusion;
- paper-level benchmark result;
- level3 self-identification.

## Next

Next milestone:

```text
m1951-executable-v2-task-quality-offtrack-support-repair-calibrated-source-mining-application-design
```

M1951 should design the adapter path for consuming
`selected_anchor_fallback_geometry.json` and rerunning the no-rollout
source-mining gate. It should preserve M1947 source-kind gates and keep ranking,
paper, and self-ID claims blocked.
