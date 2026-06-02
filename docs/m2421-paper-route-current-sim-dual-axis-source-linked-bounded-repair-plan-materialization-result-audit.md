# M2421 Paper-Route Current-Sim Dual-Axis Source-Linked Bounded Repair-Plan Materialization Result Audit

- status: completed
- decision: `source_linked_bounded_repair_plan_materialization_accepted_route_to_repair_candidate_materialization`
- manifest: `experiments/manifests/m2421-paper-route-current-sim-dual-axis-source-linked-bounded-repair-plan-materialization-result-audit.json`
- parent implementation: `docs/m2420-paper-route-current-sim-dual-axis-source-linked-bounded-repair-plan-materialization-implementation.md`
- parent summary: `runs/m2420_paper_route_current_sim_dual_axis_source_linked_bounded_repair_plan_materialization/summary.json`
- rerun/new rollout in M2421: `false`
- repair execution/training/replay/PPO: `false`
- source-linked family/profile/controller ranking: `false`
- winner selected: `false`
- paper-level/FW-vs-GRU/level3 self-ID/scenario-redesign/training-repair/current-sim verdict claims: `false`

## Audit Result

M2421 accepts M2420 as a complete source-linked bounded repair-plan
materialization artifact.

Accepted evidence:

```text
result_class: current_sim_dual_axis_source_linked_bounded_repair_plan_materialization_pass
source_consolidated_row_count: 2844
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

## Guardrail Separation

M2420 preserves the separation required by M2419:

```text
offtrack repair rows:
  admissible only as repair-plan candidates, not executed changes.

offtrack-with-collision rows:
  retain same-row collision guardrail requirements.

pure collision rows:
  remain collision_guardrail_constraint and are not plain offtrack repair.

R4 rows:
  remain r4_mitigation_semantics_guardrail and are not ordinary avoidable
  success rows.

max-step and speed-too-low rows:
  remain noncompletion/progress guardrails and are not ordinary offtrack repair.

family-membership rows:
  remain overlapping source diagnostics and cannot rank families.

diagnostic rows:
  remain diagnostic_monitoring_only and cannot rank profiles, reset targets,
  source-linked families, or controller families.
```

This is enough to admit one bounded implementation route. It is not enough to
claim repair success, scenario redesign, or current-sim progress.

## Route Decision

M2421 chooses:

```text
source_linked_bounded_repair_plan_materialization_accepted_route_to_repair_candidate_materialization
```

Next milestone:

```text
m2422-paper-route-current-sim-dual-axis-source-linked-repair-candidate-materialization-implementation
```

M2422 should materialize run-dir-only source-linked repair candidate overlays
from the M2420 plan. It should keep the candidate family compact and
non-ranking. Candidate overlays should target offtrack containment first and
carry collision, R4, max-step, speed-too-low, diagnostic, and family-membership
metadata forward.

M2422 must not:

```text
run rollout
execute repair
train or replay
run PPO
overwrite active configs
rank candidates, families, or profiles
select a winner
claim scenario redesign executed
claim training repair success
claim current-sim or paper-level verdict
```

## Why Not Pivot Yet

M2420 does not show that the only admissible route is scenario semantics. The
plan includes driver/controller-facing lever families:

```text
hidden_dynamics_actuator_response_robustness: 26
role_conditioned_containment: 17
role_semantics_containment: 10
geometry_timing_containment: 5
outcome_failure_surface_containment: 1
```

That is enough to build a compact source-linked offtrack containment candidate
set before pivoting to scenario-quality reassessment. The pivot remains a
fallback if candidate materialization would require active config overwrites,
ranking, actor input changes, or mostly task semantics.

## Failure Taxonomy

Observed:

```text
driver_outcome_failure: offtrack_dominated_failure remains from M2413
repair_plan_surface_identified: 59 offtrack repair-plan rows
collision_guardrail_surface_identified: 30 rows
R4_mitigation_semantics_surface_identified: 43 rows
max_step_noncompletion_surface_identified: 1 row
speed_too_low_surface_identified: 1 row
family_membership_diagnostic_surface_identified: 110 rows
```

Not observed:

```text
metric_artifact
lineage_invalid
contract_violation
guardrail separation failure
source-linked family/profile ranking
repair execution
scenario redesign execution
training repair success
```

Risk to manage next:

```text
materializing too many repair candidates
turning diagnostic or family rows into rankings
fixing offtrack by increasing collision, breaking R4 semantics, timing out, or
stopping below useful maneuver speed
overwriting active configs instead of writing run-dir-only overlays
```

## Claim Boundary

Supported:

```text
M2420 produced a complete source-linked bounded repair-plan artifact.

M2421 admits one run-dir-only source-linked repair-candidate materialization
route.
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
