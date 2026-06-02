# M2420 Paper-Route Current-Sim Dual-Axis Source-Linked Bounded Repair-Plan Materialization Implementation

- status: completed
- result_class: `current_sim_dual_axis_source_linked_bounded_repair_plan_materialization_pass`
- manifest: `experiments/manifests/m2420-paper-route-current-sim-dual-axis-source-linked-bounded-repair-plan-materialization-implementation.json`
- implementation: `src/autodrift/paper_route_current_sim_dual_axis_source_linked_bounded_repair_plan_materialization.py`
- tests: `tests/test_paper_route_current_sim_dual_axis_source_linked_bounded_repair_plan_materialization.py`
- output: `runs/m2420_paper_route_current_sim_dual_axis_source_linked_bounded_repair_plan_materialization/summary.json`
- rerun/new rollout: `false`
- repair execution/training/replay/PPO: `false`
- source-linked family/profile/controller ranking: `false`
- winner selected: `false`
- paper-level/FW-vs-GRU/level3 self-ID/scenario-redesign/training-repair/current-sim verdict claims: `false`

## Command

```bash
PYTHONPATH=src OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
  python -m autodrift.paper_route_current_sim_dual_axis_source_linked_bounded_repair_plan_materialization \
  --source-dir runs/m2417_paper_route_current_sim_dual_axis_source_linked_offtrack_containment_actionable_target_consolidation \
  --output-dir runs/m2420_paper_route_current_sim_dual_axis_source_linked_bounded_repair_plan_materialization \
  --next-blocker m2421-paper-route-current-sim-dual-axis-source-linked-bounded-repair-plan-materialization-result-audit
```

## Result

Summary:

```text
result_class: current_sim_dual_axis_source_linked_bounded_repair_plan_materialization_pass
source_result_class: current_sim_dual_axis_source_linked_offtrack_containment_actionable_target_consolidation_pass
source_consolidated_row_count: 2844
target_consolidated_row_count: 2844
repair_plan_row_count: 2844
offtrack_repair_plan_row_count: 59
collision_guardrail_plan_row_count: 30
r4_mitigation_plan_row_count: 43
max_step_noncompletion_plan_row_count: 1
speed_too_low_plan_row_count: 1
diagnostic_monitoring_row_count: 2733
family_membership_diagnostic_row_count: 110
diagnostic_axis_repair_plan_count: 0
family_axis_repair_plan_count: 0
profile_axis_repair_plan_count: 0
r4_ordinary_repair_plan_count: 0
collision_guardrail_as_plain_repair_count: 0
max_step_as_plain_repair_count: 0
speed_too_low_as_plain_repair_count: 0
repair_execution_allowed_count: 0
training_allowed_count: 0
ranking_admissible_count: 0
winner_selected_count: 0
guardrail_violation_count: 0
```

Plan route counts:

```text
collision_guardrail_constraint: 7
diagnostic_monitoring_only: 2623
family_membership_diagnostic_monitoring: 110
max_step_noncompletion_guardrail: 1
offtrack_repair_plan: 36
offtrack_repair_plan_with_collision_guardrail: 23
r4_mitigation_semantics_guardrail: 43
speed_too_low_guardrail: 1
```

Lever family counts:

```text
collision_non_regression_guardrail: 7
geometry_timing_containment: 5
hidden_dynamics_actuator_response_robustness: 26
low_speed_progress_guardrail: 1
non_ranking_diagnostic_monitor: 2623
noncompletion_horizon_guardrail: 1
outcome_failure_surface_containment: 1
role_conditioned_containment: 17
role_semantics_containment: 10
source_linked_family_membership_diagnostic: 110
unavoidable_mitigation_semantics: 43
```

Source-table counts:

```text
episode_rows: 2734
episode_family_membership_rows: 110
```

## Artifacts

```text
runs/m2420_paper_route_current_sim_dual_axis_source_linked_bounded_repair_plan_materialization/summary.json
runs/m2420_paper_route_current_sim_dual_axis_source_linked_bounded_repair_plan_materialization/repair_plan_rows.csv
runs/m2420_paper_route_current_sim_dual_axis_source_linked_bounded_repair_plan_materialization/offtrack_repair_plan_rows.csv
runs/m2420_paper_route_current_sim_dual_axis_source_linked_bounded_repair_plan_materialization/collision_guardrail_plan_rows.csv
runs/m2420_paper_route_current_sim_dual_axis_source_linked_bounded_repair_plan_materialization/r4_mitigation_plan_rows.csv
runs/m2420_paper_route_current_sim_dual_axis_source_linked_bounded_repair_plan_materialization/max_step_noncompletion_plan_rows.csv
runs/m2420_paper_route_current_sim_dual_axis_source_linked_bounded_repair_plan_materialization/speed_too_low_plan_rows.csv
runs/m2420_paper_route_current_sim_dual_axis_source_linked_bounded_repair_plan_materialization/diagnostic_monitoring_rows.csv
runs/m2420_paper_route_current_sim_dual_axis_source_linked_bounded_repair_plan_materialization/family_membership_diagnostic_rows.csv
runs/m2420_paper_route_current_sim_dual_axis_source_linked_bounded_repair_plan_materialization/claim_boundary.csv
```

## Interpretation

M2420 turns M2417 source-linked target categories into a bounded repair-plan
artifact. It does not claim that any repair has worked.

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

max-step and speed-too-low guardrails:
  rows that prevent a later route from hiding offtrack by timing out or by
  stopping below useful maneuver speed.

family-membership diagnostics:
  overlapping source-linked membership rows that remain non-ranking monitoring.

diagnostic monitoring:
  profile/reset/global and other diagnostic rows that remain non-ranking
  monitoring surfaces.
```

Every plan row names candidate levers, acceptance gates, stop rules, and
non-regression guardrails. These are planning constraints, not executed
controller changes.

## Claim Boundary

Supported:

```text
M2420 materialized a bounded, non-ranking source-linked repair-plan artifact
from M2417 rows.

Offtrack, collision, R4, max-step, speed-too-low, diagnostic, and
family-membership rows are separated with explicit guardrails.
```

Blocked:

```text
repair execution
scenario redesign executed
training repair success
source-linked family ranking
support-policy/controller-family ranking
winner selection
paper-level benchmark result
finite-window-vs-GRU conclusion
level3 self-identification
current-sim verdict
```

## Validation

```text
PYTHONPATH=src OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 python -m pytest -q \
  tests/test_paper_route_current_sim_dual_axis_source_linked_bounded_repair_plan_materialization.py

4 passed
```

## Next

Next milestone:

```text
m2421-paper-route-current-sim-dual-axis-source-linked-bounded-repair-plan-materialization-result-audit
```

M2421 should audit whether the M2420 repair-plan artifact admits exactly one
bounded implementation route, should pivot to scenario-quality reassessment, or
should stop for user review. It must not execute repair, train, rerun measured
validation, rank families/profiles, overwrite configs, or make paper/self-ID or
current-sim verdict claims.
