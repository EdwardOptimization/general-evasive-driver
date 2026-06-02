# M2347 Paper-Route Current-Sim Dual-Axis Redesign Calibration Materialization Implementation

- status: completed
- result_class: `current_sim_dual_axis_redesign_calibration_materialization_pass`
- manifest: `experiments/manifests/m2347-paper-route-current-sim-dual-axis-redesign-calibration-materialization-implementation.json`
- parent design: `docs/m2346-paper-route-current-sim-dual-axis-redesign-calibration-design.md`
- implementation: `src/autodrift/paper_route_current_sim_dual_axis_redesign_calibration_materialization.py`
- tests: `tests/test_paper_route_current_sim_dual_axis_redesign_calibration_materialization.py`
- output: `runs/m2347_paper_route_current_sim_dual_axis_redesign_calibration_materialization/summary.json`
- reset/rollout/policy action in M2347: `false`
- measured execution in M2347: `false`
- training/replay/PPO in M2347: `false`
- support-policy ranking claim made: `false`
- controller-family ranking claim made: `false`
- winner selected: `false`
- paper-level claim made: `false`
- finite-window vs GRU conclusion made: `false`
- level3 self-ID claim made: `false`
- scenario redesign executed claim made: `false`

## Command

```bash
PYTHONPATH=src python -m autodrift.paper_route_current_sim_dual_axis_redesign_calibration_materialization \
  --input-dir runs/m2343_paper_route_current_sim_scenario_support_redesign_consolidation \
  --config configs/paper_route_current_sim_scenario_task_family_v0.json \
  --output-dir runs/m2347_paper_route_current_sim_dual_axis_redesign_calibration_materialization
```

Focused validation:

```text
PYTHONPATH=src python -m pytest tests/test_paper_route_current_sim_dual_axis_redesign_calibration_materialization.py -q
1 passed

python -m compileall -q src tests
passed
```

## Output Artifacts

```text
runs/m2347_paper_route_current_sim_dual_axis_redesign_calibration_materialization/summary.json
runs/m2347_paper_route_current_sim_dual_axis_redesign_calibration_materialization/calibration_candidate_rows.csv
runs/m2347_paper_route_current_sim_dual_axis_redesign_calibration_materialization/geometry_timing_candidate_rows.csv
runs/m2347_paper_route_current_sim_dual_axis_redesign_calibration_materialization/hidden_range_candidate_rows.csv
runs/m2347_paper_route_current_sim_dual_axis_redesign_calibration_materialization/combined_axis_candidate_rows.csv
runs/m2347_paper_route_current_sim_dual_axis_redesign_calibration_materialization/secondary_coverage_rows.csv
runs/m2347_paper_route_current_sim_dual_axis_redesign_calibration_materialization/calibration_config_candidates.json
runs/m2347_paper_route_current_sim_dual_axis_redesign_calibration_materialization/claim_boundary.csv
```

## Result Summary

M2347 materializes the M2346 candidate schema cleanly:

```text
input_redesign_row_count: 26
geometry_timing_input_row_count: 13
hidden_range_input_row_count: 13
secondary_coverage_input_row_count: 9
secondary_coverage_tracked_count: 9
rows_without_candidate_count: 0
actor_contract_violation_count: 0
inactive_secondary_violation_count: 0
guardrail_violation_count: 0
```

Candidate counts:

```text
calibration_candidate_count: 53
geometry_timing_candidate_count: 28
hidden_range_candidate_count: 13
combined_axis_candidate_count: 12
```

The 9 secondary coverage-materialization rows are copied with:

```text
active_for_calibration: false
blocked_by: dual_axis_redesign_calibration_not_materialized
```

## Interpretation

M2347 makes the next task-quality step concrete:

- The 26-row redesign blocker now has artifact-only G/H/GH candidate rows.
- The 13/13 axis split is preserved.
- No redesign candidate is treated as executed or validated.
- The active scenario config is read as reference only and is not overwritten.
- Support-policy coverage materialization remains inactive.

This is still task-quality infrastructure, not controller evidence.

## Claim Boundary

Allowed claim:

```text
M2347 materializes bounded artifact-only dual-axis calibration candidates.
```

Blocked claims:

```text
scenario redesign executed;
support-policy ranking;
controller-family comparison readiness;
residual support solved;
paper-level evidence;
finite-window vs GRU conclusion;
level3 self-identification evidence.
```

## Follow-Up

M2348 should audit the M2347 candidate artifacts before any validation rerun or
active config materialization:

```text
experiments/manifests/m2348-paper-route-current-sim-dual-axis-redesign-calibration-materialization-result-audit.json
```
