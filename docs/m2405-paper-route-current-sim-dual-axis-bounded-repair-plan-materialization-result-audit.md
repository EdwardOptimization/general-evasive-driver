# M2405 Paper-Route Current-Sim Dual-Axis Bounded Repair-Plan Materialization Result Audit

- status: completed
- decision: `bounded_repair_plan_materialization_accepted_route_to_offtrack_containment_candidate_materialization`
- manifest: `experiments/manifests/m2405-paper-route-current-sim-dual-axis-bounded-repair-plan-materialization-result-audit.json`
- parent implementation: `docs/m2404-paper-route-current-sim-dual-axis-bounded-repair-plan-materialization-implementation.md`
- parent summary: `runs/m2404_paper_route_current_sim_dual_axis_bounded_repair_plan_materialization/summary.json`
- rerun/new rollout in M2405: `false`
- repair execution/training/replay/PPO: `false`
- support-policy/controller-family/effective-candidate ranking: `false`
- winner selected: `false`
- paper-level/FW-vs-GRU/level3 self-ID/scenario-redesign/training-repair/current-sim verdict claims: `false`

## Audit Result

M2405 accepts M2404 as a complete bounded repair-plan materialization artifact.

Accepted evidence:

```text
result_class: current_sim_dual_axis_bounded_repair_plan_materialization_pass
source_consolidated_row_count: 1313
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

## Guardrail Separation

M2404 preserves the separation required by M2403:

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

diagnostic rows:
  remain diagnostic_monitoring_only and cannot rank candidates, profiles, packs,
  or controller families.
```

This is enough to admit one bounded implementation route. It is not enough to
claim repair success or current-sim progress.

## Route Decision

M2405 chooses:

```text
bounded_repair_plan_materialization_accepted_route_to_offtrack_containment_candidate_materialization
```

Next milestone:

```text
m2406-paper-route-current-sim-dual-axis-offtrack-containment-repair-candidate-materialization-implementation
```

M2406 should materialize run-dir-only repair candidate overlays from the M2404
plan. It should keep the candidate family compact and non-ranking. The
candidate overlays should target offtrack containment first and carry collision
and R4 guardrail metadata forward.

M2406 must not:

```text
run rollout
execute repair
train or replay
run PPO
overwrite active configs
rank candidates or profiles
select a winner
claim scenario redesign executed
claim training repair success
claim current-sim or paper-level verdict
```

## Why Not Pivot Yet

M2404 does not show that the only admissible route is scenario semantics. The
plan includes driver/controller-facing lever families:

```text
hidden_dynamics_actuator_response_robustness: 88
offtrack_containment_general: 79
role_conditioned_containment: 17
role_semantics_containment: 10
geometry_timing_containment: 6
offtrack_containment_repair_family: 3
```

That is enough to build a compact offtrack containment candidate set before
pivoting to scenario-quality reassessment. The pivot remains a fallback if the
candidate materialization would require active config overwrites, ranking, or
changes that are mostly task semantics.

## Failure Taxonomy

Observed:

```text
driver_outcome_failure: offtrack_dominated_failure remains from M2397
repair_plan_surface_identified: 203 offtrack repair-plan rows
collision_guardrail_surface_identified: 65 rows
R4_mitigation_semantics_surface_identified: 57 rows
diagnostic_monitoring_surface_identified: 1048 rows
```

Not observed:

```text
metric_artifact
lineage_invalid
contract_violation
guardrail separation failure
candidate/profile ranking
repair execution
scenario redesign execution
training repair success
```

Risk to manage next:

```text
materializing too many repair candidates
turning diagnostic rows into rankings
fixing offtrack by increasing collision or breaking R4 semantics
overwriting active configs instead of writing run-dir-only overlays
```

## Claim Boundary

Supported:

```text
M2404 produced a complete bounded repair-plan artifact.

M2405 admits one run-dir-only offtrack containment repair-candidate
materialization route.
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
