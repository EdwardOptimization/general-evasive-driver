# M2404 Paper-Route Current-Sim Dual-Axis Bounded Repair-Plan Materialization Implementation

- status: completed
- result_class: `current_sim_dual_axis_bounded_repair_plan_materialization_pass`
- manifest: `experiments/manifests/m2404-paper-route-current-sim-dual-axis-bounded-repair-plan-materialization-implementation.json`
- implementation: `src/autodrift/paper_route_current_sim_dual_axis_bounded_repair_plan_materialization.py`
- tests: `tests/test_paper_route_current_sim_dual_axis_bounded_repair_plan_materialization.py`
- output: `runs/m2404_paper_route_current_sim_dual_axis_bounded_repair_plan_materialization/summary.json`
- rerun/new rollout: `false`
- repair execution/training/replay/PPO: `false`
- support-policy/controller-family/effective-candidate ranking: `false`
- winner selected: `false`
- paper-level/FW-vs-GRU/level3 self-ID/scenario-redesign/training-repair/current-sim verdict claims: `false`

## Command

```bash
PYTHONPATH=src python -m autodrift.paper_route_current_sim_dual_axis_bounded_repair_plan_materialization \
  --source-dir runs/m2401_paper_route_current_sim_dual_axis_effective_candidate_actionable_target_consolidation \
  --output-dir runs/m2404_paper_route_current_sim_dual_axis_bounded_repair_plan_materialization \
  --next-blocker m2405-paper-route-current-sim-dual-axis-bounded-repair-plan-materialization-result-audit
```

## Result

Summary:

```text
result_class: current_sim_dual_axis_bounded_repair_plan_materialization_pass
source_result_class: current_sim_dual_axis_effective_candidate_actionable_target_consolidation_pass
source_consolidated_row_count: 1313
target_consolidated_row_count: 1313
repair_plan_row_count: 1313
offtrack_repair_plan_row_count: 203
collision_guardrail_plan_row_count: 65
r4_mitigation_plan_row_count: 57
diagnostic_monitoring_row_count: 1048
diagnostic_axis_repair_plan_count: 0
r4_ordinary_repair_plan_count: 0
collision_guardrail_as_plain_repair_count: 0
repair_execution_allowed_count: 0
training_allowed_count: 0
ranking_admissible_count: 0
winner_selected_count: 0
guardrail_violation_count: 0
```

Plan route counts:

```text
collision_guardrail_constraint: 5
diagnostic_monitoring_only: 1048
offtrack_repair_plan: 143
offtrack_repair_plan_with_collision_guardrail: 60
r4_mitigation_semantics_guardrail: 57
```

Lever family counts:

```text
collision_non_regression_guardrail: 5
geometry_timing_containment: 6
hidden_dynamics_actuator_response_robustness: 88
non_ranking_diagnostic_monitor: 1048
offtrack_containment_general: 79
offtrack_containment_repair_family: 3
role_conditioned_containment: 17
role_semantics_containment: 10
unavoidable_mitigation_semantics: 57
```

## Artifacts

```text
runs/m2404_paper_route_current_sim_dual_axis_bounded_repair_plan_materialization/summary.json
runs/m2404_paper_route_current_sim_dual_axis_bounded_repair_plan_materialization/repair_plan_rows.csv
runs/m2404_paper_route_current_sim_dual_axis_bounded_repair_plan_materialization/offtrack_repair_plan_rows.csv
runs/m2404_paper_route_current_sim_dual_axis_bounded_repair_plan_materialization/collision_guardrail_plan_rows.csv
runs/m2404_paper_route_current_sim_dual_axis_bounded_repair_plan_materialization/r4_mitigation_plan_rows.csv
runs/m2404_paper_route_current_sim_dual_axis_bounded_repair_plan_materialization/diagnostic_monitoring_rows.csv
runs/m2404_paper_route_current_sim_dual_axis_bounded_repair_plan_materialization/claim_boundary.csv
```

## Interpretation

M2404 turns M2401 target categories into a bounded repair-plan artifact. It
does not claim that any repair has worked.

The materialized plan separates:

```text
offtrack repair plans:
  rows where a later implementation may try to reduce road departure or improve
  road-margin tails.

offtrack repair plans with collision guardrails:
  rows where offtrack improvement is admissible only if same-row collision
  guardrails do not regress.

collision guardrail constraints:
  pure collision-heavy rows that cannot be treated as ordinary offtrack repair.

R4 mitigation semantics:
  unavoidable/mitigation rows that must be evaluated with separate mitigation
  semantics, not ordinary avoidable-success scoring.

diagnostic monitoring:
  candidate/profile/pack/global and other diagnostic rows that remain
  non-ranking monitoring surfaces.
```

Every plan row names candidate levers, acceptance gates, stop rules, and
non-regression guardrails. These are planning constraints, not executed
controller changes.

## Claim Boundary

Supported:

```text
M2404 materialized a bounded, non-ranking repair-plan artifact from M2401 rows.

Offtrack, collision, R4, and diagnostic monitoring rows are separated with
explicit guardrails.
```

Blocked:

```text
repair execution
scenario redesign executed
training repair success
effective-candidate ranking
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
  tests/test_paper_route_current_sim_dual_axis_bounded_repair_plan_materialization.py

4 passed
```

## Next

Next milestone:

```text
m2405-paper-route-current-sim-dual-axis-bounded-repair-plan-materialization-result-audit
```

M2405 should audit whether the M2404 repair-plan artifact admits exactly one
bounded implementation route, should pivot to scenario-quality reassessment, or
should stop for user review. It must not execute repair, train, rerun measured
validation, rank candidates/profiles, overwrite configs, or make paper/self-ID
or current-sim verdict claims.
