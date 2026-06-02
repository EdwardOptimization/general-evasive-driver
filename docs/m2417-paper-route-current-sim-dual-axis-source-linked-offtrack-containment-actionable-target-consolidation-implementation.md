# M2417 Paper-Route Current-Sim Dual-Axis Source-Linked Offtrack Containment Actionable Target Consolidation Implementation

- status: completed
- result_class: `current_sim_dual_axis_source_linked_offtrack_containment_actionable_target_consolidation_pass`
- manifest: `experiments/manifests/m2417-paper-route-current-sim-dual-axis-source-linked-offtrack-containment-actionable-target-consolidation-implementation.json`
- parent audit: `docs/m2416-paper-route-current-sim-dual-axis-source-linked-offtrack-containment-measured-outcome-localization-result-audit.md`
- parent summary: `runs/m2415_paper_route_current_sim_dual_axis_source_linked_offtrack_containment_measured_outcome_localization/summary.json`
- implementation: `src/autodrift/paper_route_current_sim_dual_axis_source_linked_offtrack_containment_actionable_target_consolidation.py`
- focused tests: `3 passed`
- summary: `runs/m2417_paper_route_current_sim_dual_axis_source_linked_offtrack_containment_actionable_target_consolidation/summary.json`
- rerun/new rollout in M2417: `false`
- repair execution/training/replay/PPO: `false`
- family/profile/controller ranking and winner selection: `false`
- paper/FW-vs-GRU/level3 self-ID/scenario-redesign/training-repair/current-sim verdict claims: `false`

## Implementation Result

M2417 materialized artifact-only target consolidation from M2415 localization
slices. It did not rerun measured validation or localization. It only reads
M2415 CSV/JSON artifacts and writes compact target/guardrail tables.

Summary:

```text
result_class: current_sim_dual_axis_source_linked_offtrack_containment_actionable_target_consolidation_pass
source_slice_row_count: 2844
target_slice_row_count: 2844
consolidated_row_count: 2844
offtrack_repair_target_row_count: 59
collision_guardrail_row_count: 30
r4_mitigation_semantics_row_count: 43
max_step_noncompletion_row_count: 1
speed_too_low_row_count: 1
diagnostic_guardrail_row_count: 2733
family_membership_diagnostic_row_count: 110
diagnostic_axis_repair_target_count: 0
family_axis_repair_target_count: 0
profile_axis_repair_target_count: 0
r4_ordinary_repair_target_count: 0
ranking_admissible_count: 0
winner_selected_count: 0
guardrail_violation_count: 0
```

Consolidated route counts:

```text
collision_guardrail: 7
diagnostic_guardrail: 2611
diagnostic_only: 12
max_step_noncompletion_target: 1
offtrack_repair_target: 36
offtrack_repair_target_with_collision_guardrail: 23
r4_mitigation_semantics: 43
source_linked_family_diagnostic_guardrail: 110
speed_too_low_target: 1
```

Actionability-class counts:

```text
diagnostic_guardrail: 2611
geometry_timing: 6
hidden_dynamics: 7
max_step_noncompletion: 1
outcome_failure_surface: 3
r4_mitigation_semantics: 43
role_conditioned_geometry_timing: 30
role_conditioned_hidden_dynamics: 19
role_semantics: 13
source_linked_family_membership_diagnostic: 110
speed_too_low: 1
```

Source-table counts:

```text
episode_rows: 2734
episode_family_membership_rows: 110
```

## Consolidation Semantics

M2417 intentionally keeps overlapping family-membership rows diagnostic. Any
row sourced from `episode_family_membership_rows`, or any `family_id` axis row,
is routed to `source_linked_family_diagnostic_guardrail` rather than a repair
target. Profile and reset-target slices also remain diagnostic. This prevents
the source-linked panel from becoming an implicit family/profile ranking.

The actionable tables are:

```text
offtrack_repair_target_rows.csv
collision_guardrail_rows.csv
r4_mitigation_semantics_rows.csv
max_step_noncompletion_rows.csv
speed_too_low_rows.csv
diagnostic_guardrail_rows.csv
family_membership_diagnostic_rows.csv
claim_boundary.csv
```

Offtrack target rows are now compact enough for result audit and later repair
planning. Collision guardrails, R4 mitigation semantics, max-step
noncompletion, and speed-too-low rows are kept separate so a later repair route
cannot hide one blocker by improving another.

## Claim Boundary

Supported:

```text
M2417 generated source-linked actionable target and guardrail artifacts from
M2415 localization rows.
```

Blocked:

```text
candidate family ranking
support/profile/controller ranking
winner selection
repair execution
scenario redesign executed
training repair success
paper-level benchmark result
finite-window-vs-GRU conclusion
level3 self-identification
current-sim verdict
```

## Route Decision

Decision:

```text
source_linked_actionable_target_consolidation_pass_route_to_result_audit
```

Next milestone:

```text
m2418-paper-route-current-sim-dual-axis-source-linked-offtrack-containment-actionable-target-consolidation-result-audit
```

M2418 should audit whether M2417 target consolidation is complete and whether
the next valid route is branch synthesis, bounded repair-plan materialization,
stop, or pivot. It must not rerun rollout/localization, execute repair, train,
rank families/profiles/controllers, select a winner, or make paper/self-ID/
current-sim verdict claims.

## Failure Taxonomy

Observed:

```text
behavior_regression: source measured outcome remains offtrack-dominated
repair_target_surface_identified: 59 offtrack repair-target rows
collision_guardrail_surface_identified: 30 rows
R4_mitigation_semantics_surface_identified: 43 rows
max_step_noncompletion_surface_identified: 1 row
speed_too_low_surface_identified: 1 row
```

Not observed:

```text
metric_artifact
lineage_invalid
contract_violation
source_table_loss
family/profile ranking
repair execution
scenario redesign execution
training repair success
winner selection
```
