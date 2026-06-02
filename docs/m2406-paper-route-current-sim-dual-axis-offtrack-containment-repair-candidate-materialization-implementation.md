# M2406 Paper-Route Current-Sim Dual-Axis Offtrack Containment Repair Candidate Materialization Implementation

- status: completed
- result_class: `current_sim_dual_axis_offtrack_containment_repair_candidate_materialization_pass`
- manifest: `experiments/manifests/m2406-paper-route-current-sim-dual-axis-offtrack-containment-repair-candidate-materialization-implementation.json`
- implementation: `src/autodrift/paper_route_current_sim_dual_axis_offtrack_containment_repair_candidate_materialization.py`
- tests: `tests/test_paper_route_current_sim_dual_axis_offtrack_containment_repair_candidate_materialization.py`
- output: `runs/m2406_paper_route_current_sim_dual_axis_offtrack_containment_repair_candidate_materialization/summary.json`
- rerun/new rollout: `false`
- repair execution/training/replay/PPO: `false`
- active config overwrite: `false`
- support-policy/controller-family/effective-candidate ranking: `false`
- winner selected: `false`
- paper-level/FW-vs-GRU/level3 self-ID/scenario-redesign/training-repair/current-sim verdict claims: `false`

## Command

```bash
PYTHONPATH=src python -m autodrift.paper_route_current_sim_dual_axis_offtrack_containment_repair_candidate_materialization \
  --source-dir runs/m2404_paper_route_current_sim_dual_axis_bounded_repair_plan_materialization \
  --output-dir runs/m2406_paper_route_current_sim_dual_axis_offtrack_containment_repair_candidate_materialization \
  --next-blocker m2407-paper-route-current-sim-dual-axis-offtrack-containment-repair-candidate-materialization-result-audit
```

## Result

Summary:

```text
result_class: current_sim_dual_axis_offtrack_containment_repair_candidate_materialization_pass
source_offtrack_repair_plan_row_count: 203
assigned_offtrack_repair_plan_row_count: 203
unassigned_offtrack_repair_plan_row_count: 0
candidate_count: 4
candidate_overlay_written_count: 4
candidate_overlay_outside_run_dir_count: 0
collision_guardrail_source_row_count: 65
r4_mitigation_source_row_count: 57
diagnostic_monitoring_source_row_count: 1048
guardrail_metadata_row_count: 8
active_config_overwrite_count: 0
repair_execution_allowed_count: 0
training_allowed_count: 0
ranking_admissible_count: 0
winner_selected_count: 0
guardrail_violation_count: 0
```

Candidate families:

```text
c01_geometry_timing_containment
c02_hidden_dynamics_response_containment
c03_general_offtrack_boundary_containment
c04_role_conditioned_containment
```

Each candidate is a run-dir-only overlay JSON. None is an active config, trained
policy, replay result, or promoted candidate.

## Artifacts

```text
runs/m2406_paper_route_current_sim_dual_axis_offtrack_containment_repair_candidate_materialization/summary.json
runs/m2406_paper_route_current_sim_dual_axis_offtrack_containment_repair_candidate_materialization/repair_candidate_overlays.csv
runs/m2406_paper_route_current_sim_dual_axis_offtrack_containment_repair_candidate_materialization/repair_candidate_overlays/*.json
runs/m2406_paper_route_current_sim_dual_axis_offtrack_containment_repair_candidate_materialization/candidate_guardrail_metadata.csv
runs/m2406_paper_route_current_sim_dual_axis_offtrack_containment_repair_candidate_materialization/offtrack_repair_plan_rows.csv
runs/m2406_paper_route_current_sim_dual_axis_offtrack_containment_repair_candidate_materialization/collision_guardrail_plan_rows.csv
runs/m2406_paper_route_current_sim_dual_axis_offtrack_containment_repair_candidate_materialization/r4_mitigation_plan_rows.csv
runs/m2406_paper_route_current_sim_dual_axis_offtrack_containment_repair_candidate_materialization/diagnostic_monitoring_rows.csv
runs/m2406_paper_route_current_sim_dual_axis_offtrack_containment_repair_candidate_materialization/claim_boundary.csv
```

## Interpretation

M2406 converts the M2404 repair-plan rows into a compact candidate set. The
mapping is complete: all 203 offtrack repair-plan rows are assigned to one of
four candidate families.

The candidates are intentionally not ranked. Their purpose is to define the next
reset/load validation surface:

```text
geometry/timing containment:
  centerline, early/mid timing, and recovery-window style rows.

hidden-dynamics response containment:
  weak-brake, slow-steer, and hidden-dynamics robustness rows.

general offtrack boundary containment:
  general offtrack-containment and repair-family rows.

role-conditioned containment:
  role-family and role-conditioned offtrack rows.
```

Every candidate carries collision and R4 guardrail metadata. The guardrail
metadata points to concrete output artifacts, not missing paths.

## Claim Boundary

Supported:

```text
M2406 materialized compact run-dir-only offtrack containment repair-candidate
overlays with collision and R4 guardrail metadata.
```

Blocked:

```text
active config overwrite
repair execution
scenario redesign executed
training repair success
candidate ranking
controller-family ranking
winner selection
paper-level benchmark result
finite-window-vs-GRU conclusion
level3 self-identification
current-sim verdict
```

## Validation

```text
PYTHONPATH=src OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 python -m pytest -q \
  tests/test_paper_route_current_sim_dual_axis_offtrack_containment_repair_candidate_materialization.py

4 passed
```

## Next

Next milestone:

```text
m2407-paper-route-current-sim-dual-axis-offtrack-containment-repair-candidate-materialization-result-audit
```

M2407 should audit whether the run-dir-only overlays are complete enough to
admit a reset/load validation adapter. It must not run rollout, execute repair,
train, rank candidates, overwrite active configs, or make current-sim or paper
verdict claims.
