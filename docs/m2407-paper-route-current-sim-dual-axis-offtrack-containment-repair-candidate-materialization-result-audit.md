# M2407 Paper-Route Current-Sim Dual-Axis Offtrack Containment Repair Candidate Materialization Result Audit

- status: completed
- decision: `offtrack_containment_repair_candidate_materialization_accepted_route_to_reset_load_validation_adapter`
- manifest: `experiments/manifests/m2407-paper-route-current-sim-dual-axis-offtrack-containment-repair-candidate-materialization-result-audit.json`
- parent implementation: `docs/m2406-paper-route-current-sim-dual-axis-offtrack-containment-repair-candidate-materialization-implementation.md`
- parent summary: `runs/m2406_paper_route_current_sim_dual_axis_offtrack_containment_repair_candidate_materialization/summary.json`
- rerun/new rollout in M2407: `false`
- repair execution/training/replay/PPO: `false`
- active config overwrite: `false`
- support-policy/controller-family/effective-candidate ranking: `false`
- winner selected: `false`
- paper-level/FW-vs-GRU/level3 self-ID/scenario-redesign/training-repair/current-sim verdict claims: `false`

## Audit Result

M2407 accepts M2406 as a complete run-dir-only repair-candidate materialization
artifact.

Accepted evidence:

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
guardrail_metadata_missing_count: 0
active_config_overwrite_count: 0
repair_execution_allowed_count: 0
training_allowed_count: 0
ranking_admissible_count: 0
winner_selected_count: 0
guardrail_violation_count: 0
```

Candidate families:

```text
geometry_timing_containment: 1
hidden_dynamics_response_containment: 1
general_offtrack_boundary_containment: 1
role_conditioned_containment: 1
```

## Boundary Checks

Run-dir boundary:

```text
candidate_overlay_written_count: 4
candidate_overlay_outside_run_dir_count: 0
active_config_overwrite_count: 0
active_config_overwritten: false
```

Guardrail metadata:

```text
candidate_guardrail_metadata rows: 8
per candidate:
  collision_non_regression source rows: 65
  r4_mitigation_semantics source rows: 57
```

Claim boundary:

```text
artifact_only_offtrack_containment_repair_candidate_materialization: admissible
active_config_overwrite: blocked
repair_execution: blocked
scenario_redesign_executed: blocked
training_repair_success: blocked
candidate_ranking: blocked
current_sim_verdict: blocked
```

M2406 satisfies the requirements for a bounded adapter-level validation route.
It still does not prove that any candidate improves driving.

## Route Decision

Decision:

```text
offtrack_containment_repair_candidate_materialization_accepted_route_to_reset_load_validation_adapter
```

Next milestone:

```text
m2408-paper-route-current-sim-dual-axis-offtrack-containment-candidate-reset-load-validation-adapter-implementation
```

M2408 should validate that each run-dir-only overlay is structurally loadable,
references existing guardrail artifacts, preserves claim boundaries, and can be
linked back to source repair-plan rows. It should not execute repair, overwrite
active configs, run measured rollout, train, replay, rank candidates, select a
winner, or make paper/self-ID/current-sim verdict claims.

The validation should be adapter-level and bounded:

```text
overlay JSON load: required
overlay path under M2406 run dir: required
source row keys present: required
collision and R4 guardrail metadata present: required
guardrail artifact refs exist: required
candidate count remains compact: required
ranking and winner flags remain false: required
environment step/policy action: forbidden
```

## Why Direct Adapter Implementation Is Admissible

A separate design milestone is not needed here. M2406 outputs are already small
and structured:

```text
4 overlay JSON files
4 overlay table rows
8 guardrail metadata rows
claim boundary table
copied offtrack/collision/R4/diagnostic source artifacts
```

The next adapter can be implemented as a read-only structural/load validation
over those artifacts. It is not a rollout or repair execution route.

## Failure Taxonomy

Observed:

```text
candidate_validation_ready_surface_identified: 4 run-dir-only overlays
guardrail_metadata_surface_identified: 8 rows
driver_outcome_failure: offtrack_dominated_failure remains from M2397
```

Not observed:

```text
metric_artifact
lineage_invalid
contract_violation
missing_guardrail_metadata
active_config_overwrite
candidate/profile ranking
repair execution
scenario redesign execution
training repair success
```

Risk to manage next:

```text
mistaking structural adapter validation for driver improvement
turning compact candidates into rankings
validating overlays while ignoring guardrail refs
leaking from run-dir-only overlays into active configs
```

## Claim Boundary

Supported:

```text
M2406 candidate materialization is complete and validation-ready at the
adapter-structure level.

M2407 admits one bounded reset/load validation adapter implementation route.
```

Blocked:

```text
repair execution
measured rollout
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
