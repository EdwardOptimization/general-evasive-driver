# M2423 Paper-Route Current-Sim Dual-Axis Source-Linked Repair-Candidate Materialization Result Audit

- status: completed
- decision: `source_linked_repair_candidate_materialization_accepted_route_to_reset_load_validation_adapter`
- manifest: `experiments/manifests/m2423-paper-route-current-sim-dual-axis-source-linked-repair-candidate-materialization-result-audit.json`
- parent implementation: `docs/m2422-paper-route-current-sim-dual-axis-source-linked-repair-candidate-materialization-implementation.md`
- parent summary: `runs/m2422_paper_route_current_sim_dual_axis_source_linked_repair_candidate_materialization/summary.json`
- rerun/new rollout/reset/load validation in M2423: `false`
- repair execution/training/replay/PPO: `false`
- active config overwrite: `false`
- source-linked family/profile/candidate/controller ranking: `false`
- winner selected: `false`
- paper-level/FW-vs-GRU/level3 self-ID/scenario-redesign/training-repair/current-sim verdict claims: `false`

## Audit Result

M2423 accepts M2422 as a complete run-dir-only source-linked
repair-candidate materialization artifact.

Accepted evidence:

```text
result_class: current_sim_dual_axis_source_linked_repair_candidate_materialization_pass
source_repair_plan_row_count: 2844
source_offtrack_repair_plan_row_count: 59
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

Candidate families:

```text
source_linked_geometry_timing_containment: 1
source_linked_hidden_dynamics_response_containment: 1
source_linked_role_conditioned_containment: 1
source_linked_outcome_failure_surface_containment: 1
```

Offtrack source lever families:

```text
geometry_timing_containment: 5
hidden_dynamics_actuator_response_robustness: 26
role_conditioned_containment: 17
role_semantics_containment: 10
outcome_failure_surface_containment: 1
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
candidate_guardrail_metadata rows: 24
per candidate:
  collision_non_regression source rows: 30
  r4_mitigation_semantics source rows: 43
  max_step_noncompletion source rows: 1
  speed_too_low source rows: 1
  diagnostic_monitoring source rows: 2733
  source_linked_family_membership_diagnostic source rows: 110
```

Claim boundary:

```text
artifact_only_source_linked_repair_candidate_materialization: admissible
active_config_overwrite: blocked
repair_execution: blocked
scenario_redesign_executed: blocked
training_repair_success: blocked
source_linked_family_ranking: blocked
support_policy_ranking: blocked
candidate_ranking: blocked
current_sim_verdict: blocked
```

M2422 satisfies the requirements for a bounded adapter-level validation route.
It still does not prove that any candidate improves driving.

## Route Decision

Decision:

```text
source_linked_repair_candidate_materialization_accepted_route_to_reset_load_validation_adapter
```

Next milestone:

```text
m2424-paper-route-current-sim-dual-axis-source-linked-candidate-reset-load-validation-adapter-implementation
```

M2424 should validate that each run-dir-only source-linked overlay is
structurally loadable, references existing guardrail artifacts, preserves claim
boundaries, and can be linked back to source repair-plan rows. It should not
execute repair, overwrite active configs, run measured rollout, train, replay,
rank candidates/families/profiles, select a winner, or make paper/self-ID or
current-sim verdict claims.

The validation should be adapter-level and bounded:

```text
overlay JSON load: required
overlay path under M2422 run dir: required
source row keys present: required
table/payload candidate id, family, and source-row counts match: required
collision, R4, max-step, speed-too-low, diagnostic, and family guardrail refs exist: required
diagnostic and family rows remain monitoring-only: required
candidate count remains compact: required
ranking and winner flags remain false: required
environment step/policy action: forbidden
```

## Why Direct Adapter Implementation Is Admissible

A separate design milestone is not needed here. M2422 outputs are small and
structured:

```text
4 overlay JSON files
4 overlay table rows
24 guardrail metadata rows
claim boundary table
copied offtrack/collision/R4/max-step/speed-too-low/diagnostic/family source artifacts
```

The next adapter can be implemented as a read-only structural/load validation
over those artifacts. It is not a rollout, reset panel, measured validation, or
repair execution route.

## Failure Taxonomy

Observed:

```text
candidate_validation_ready_surface_identified: 4 run-dir-only source-linked overlays
guardrail_metadata_surface_identified: 24 rows
driver_outcome_failure: offtrack_dominated_failure remains from M2413
```

Not observed:

```text
metric_artifact
lineage_invalid
contract_violation
missing_guardrail_metadata
active_config_overwrite
candidate/family/profile ranking
repair execution
scenario redesign execution
training repair success
```

Risk to manage next:

```text
mistaking structural adapter validation for driver improvement
turning compact candidates or family diagnostics into rankings
validating overlays while ignoring max-step/speed-too-low or diagnostic refs
leaking from run-dir-only overlays into active configs
```

## Claim Boundary

Supported:

```text
M2422 candidate materialization is complete and validation-ready at the
adapter-structure level.

M2423 admits one bounded read-only reset/load validation adapter implementation
route.
```

Blocked:

```text
reset/load validation result
repair execution
measured rollout
scenario redesign executed
training repair success
candidate ranking
source-linked family ranking
controller-family ranking
winner selection
paper-level benchmark result
finite-window-vs-GRU conclusion
level3 self-identification
current-sim verdict
```
