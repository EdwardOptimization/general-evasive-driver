# M2422 Paper-Route Current-Sim Dual-Axis Source-Linked Repair-Candidate Materialization Implementation

- status: completed
- result_class: `current_sim_dual_axis_source_linked_repair_candidate_materialization_pass`
- manifest: `experiments/manifests/m2422-paper-route-current-sim-dual-axis-source-linked-repair-candidate-materialization-implementation.json`
- implementation: `src/autodrift/paper_route_current_sim_dual_axis_source_linked_repair_candidate_materialization.py`
- tests: `tests/test_paper_route_current_sim_dual_axis_source_linked_repair_candidate_materialization.py`
- output: `runs/m2422_paper_route_current_sim_dual_axis_source_linked_repair_candidate_materialization/summary.json`
- rerun/new rollout/reset/repair execution/training/replay/PPO: `false`
- active config overwrite/source-linked family/profile/controller ranking: `false`
- winner selected: `false`
- paper-level/FW-vs-GRU/level3 self-ID/scenario-redesign/training-repair/current-sim verdict claims: `false`

## Command

```bash
PYTHONPATH=src OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
  python -m autodrift.paper_route_current_sim_dual_axis_source_linked_repair_candidate_materialization \
  --source-dir runs/m2420_paper_route_current_sim_dual_axis_source_linked_bounded_repair_plan_materialization \
  --output-dir runs/m2422_paper_route_current_sim_dual_axis_source_linked_repair_candidate_materialization \
  --next-blocker m2423-paper-route-current-sim-dual-axis-source-linked-repair-candidate-materialization-result-audit
```

## Result

Summary:

```text
result_class: current_sim_dual_axis_source_linked_repair_candidate_materialization_pass
source_result_class: current_sim_dual_axis_source_linked_bounded_repair_plan_materialization_pass
source_repair_plan_row_count: 2844
source_offtrack_repair_plan_row_count: 59
target_offtrack_repair_plan_row_count: 59
assigned_offtrack_repair_plan_row_count: 59
unassigned_offtrack_repair_plan_row_count: 0
candidate_count: 4
candidate_overlay_written_count: 4
candidate_overlay_outside_run_dir_count: 0
collision_guardrail_source_row_count: 30
r4_mitigation_source_row_count: 43
max_step_source_row_count: 1
speed_too_low_source_row_count: 1
diagnostic_monitoring_source_row_count: 2733
family_membership_diagnostic_source_row_count: 110
guardrail_metadata_row_count: 24
guardrail_metadata_missing_count: 0
diagnostic_rows_monitoring_only: true
family_rows_monitoring_only: true
active_config_overwrite_count: 0
repair_execution_allowed_count: 0
training_allowed_count: 0
ranking_admissible_count: 0
winner_selected_count: 0
guardrail_violation_count: 0
```

Candidate overlays:

```text
c01_source_linked_geometry_timing_containment:
  source rows: 5
  with collision guardrail: 4

c02_source_linked_hidden_dynamics_response_containment:
  source rows: 26
  with collision guardrail: 9

c03_source_linked_role_conditioned_containment:
  source rows: 27
  with collision guardrail: 10

c04_source_linked_outcome_failure_surface_containment:
  source rows: 1
  with collision guardrail: 0
```

Offtrack source lever families:

```text
geometry_timing_containment: 5
hidden_dynamics_actuator_response_robustness: 26
outcome_failure_surface_containment: 1
role_conditioned_containment: 17
role_semantics_containment: 10
```

## Artifacts

```text
runs/m2422_paper_route_current_sim_dual_axis_source_linked_repair_candidate_materialization/summary.json
runs/m2422_paper_route_current_sim_dual_axis_source_linked_repair_candidate_materialization/repair_candidate_overlays.csv
runs/m2422_paper_route_current_sim_dual_axis_source_linked_repair_candidate_materialization/candidate_guardrail_metadata.csv
runs/m2422_paper_route_current_sim_dual_axis_source_linked_repair_candidate_materialization/repair_candidate_overlays/*.json
runs/m2422_paper_route_current_sim_dual_axis_source_linked_repair_candidate_materialization/repair_plan_rows.csv
runs/m2422_paper_route_current_sim_dual_axis_source_linked_repair_candidate_materialization/offtrack_repair_plan_rows.csv
runs/m2422_paper_route_current_sim_dual_axis_source_linked_repair_candidate_materialization/collision_guardrail_plan_rows.csv
runs/m2422_paper_route_current_sim_dual_axis_source_linked_repair_candidate_materialization/r4_mitigation_plan_rows.csv
runs/m2422_paper_route_current_sim_dual_axis_source_linked_repair_candidate_materialization/max_step_noncompletion_plan_rows.csv
runs/m2422_paper_route_current_sim_dual_axis_source_linked_repair_candidate_materialization/speed_too_low_plan_rows.csv
runs/m2422_paper_route_current_sim_dual_axis_source_linked_repair_candidate_materialization/diagnostic_monitoring_rows.csv
runs/m2422_paper_route_current_sim_dual_axis_source_linked_repair_candidate_materialization/family_membership_diagnostic_rows.csv
runs/m2422_paper_route_current_sim_dual_axis_source_linked_repair_candidate_materialization/claim_boundary.csv
```

## Interpretation

M2422 converts the M2420 repair-plan surface into four compact, run-dir-only
source-linked candidate overlays. It does not execute a repair and does not
choose a winner.

Every candidate carries six guardrail/metadata families:

```text
collision_non_regression
r4_mitigation_semantics
max_step_noncompletion
speed_too_low
diagnostic_monitoring
source_linked_family_membership_diagnostic
```

The 110 family-membership diagnostic rows remain monitoring-only and
non-ranking. M2422 deliberately does not create a direct repair candidate from
the family-membership diagnostic surface; that surface is overlapping metadata,
not a source-linked family ranking result.

## Claim Boundary

Supported:

```text
M2422 materialized four run-dir-only source-linked repair-candidate overlays.

All 59 offtrack repair-plan rows are assigned to compact non-ranking candidate
overlays.

Collision, R4, max-step, speed-too-low, diagnostic, and family-membership
metadata are preserved with each candidate.
```

Blocked:

```text
reset/load validation result
repair execution
scenario redesign executed
training repair success
source-linked family ranking
support-policy/controller-family ranking
candidate ranking
winner selection
paper-level benchmark result
finite-window-vs-GRU conclusion
level3 self-identification
current-sim verdict
```

## Validation

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q \
  tests/test_paper_route_current_sim_dual_axis_source_linked_repair_candidate_materialization.py

5 passed
```

## Next

Next milestone:

```text
m2423-paper-route-current-sim-dual-axis-source-linked-repair-candidate-materialization-result-audit
```

M2423 should audit whether M2422 is complete enough to admit read-only
reset/load validation adapter implementation, should pivot to artifact repair
if the candidate overlay schema is incomplete, or should stop for user review
if the only path requires ranking, active config overwrite, hidden/oracle actor
inputs, repair execution, or verdict claims.
