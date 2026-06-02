# M2418 Paper-Route Current-Sim Dual-Axis Source-Linked Offtrack Containment Actionable Target Consolidation Result Audit

- status: completed
- decision: `source_linked_actionable_target_consolidation_accepted_route_to_branch_synthesis`
- manifest: `experiments/manifests/m2418-paper-route-current-sim-dual-axis-source-linked-offtrack-containment-actionable-target-consolidation-result-audit.json`
- parent implementation: `docs/m2417-paper-route-current-sim-dual-axis-source-linked-offtrack-containment-actionable-target-consolidation-implementation.md`
- parent summary: `runs/m2417_paper_route_current_sim_dual_axis_source_linked_offtrack_containment_actionable_target_consolidation/summary.json`
- rerun/consolidation rerun/repair/training/replay/PPO: `false`
- family/profile/controller ranking and winner selection: `false`
- paper/FW-vs-GRU/level3 self-ID/scenario-redesign/training-repair/current-sim verdict claims: `false`

## Audit Result

M2418 accepts M2417 as a complete artifact-only target-consolidation pass.

Accepted evidence:

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
offtrack_repair_target: 36
offtrack_repair_target_with_collision_guardrail: 23
collision_guardrail: 7
r4_mitigation_semantics: 43
max_step_noncompletion_target: 1
speed_too_low_target: 1
source_linked_family_diagnostic_guardrail: 110
diagnostic_guardrail: 2611
diagnostic_only: 12
```

M2418 accepts the important guardrail: all family-membership and profile rows
remain diagnostic. The consolidation did not create family rankings, support
policy rankings, candidate winners, repair execution, scenario redesign, or
training-repair claims.

## Route Readiness

M2417 creates useful target tables for later planning:

```text
offtrack repair targets:
  59 rows across geometry, hidden-dynamics, role-conditioned, role-semantic,
  and outcome-failure surfaces.

collision guardrails:
  30 rows, including 23 rows coupled to offtrack repair targets.

R4 mitigation semantics:
  43 rows that must remain separate from ordinary offtrack repair.

max-step and speed-too-low:
  1 row each, preserved as separate noncompletion/low-speed targets.

diagnostics:
  2733 diagnostic rows, including 110 overlapping family-membership rows.
```

These are compact enough to support a repair-plan route, but the branch should
not enter another ordinary repair-planning milestone immediately after
consolidation. The source-linked branch now has reset evidence, measured
validation, outcome localization, target consolidation, and audits. It needs a
branch synthesis before the next materialization step.

## Failure Taxonomy

Observed:

```text
driver_outcome_failure: inherited offtrack-dominated measured outcome
repair_target_surface_identified: 59 offtrack target rows
collision_guardrail_surface_identified: 30 rows
R4_mitigation_semantics_surface_identified: 43 rows
max_step_noncompletion_surface_identified: 1 row
speed_too_low_surface_identified: 1 row
local_search_risk: another ordinary artifact-only step would continue the same source-linked branch without synthesis
```

Not observed:

```text
metric_artifact
lineage_invalid
contract_violation
source_table_loss
family/profile/controller ranking
winner selection
repair execution
scenario redesign execution
training repair success
current-sim verdict claim
```

## Claim Boundary

Supported:

```text
M2417 target consolidation is complete and preserves offtrack, collision
guardrail, R4, max-step, speed-too-low, family diagnostic, and diagnostic-only
categories.

M2418 routes to branch synthesis before repair-plan materialization.
```

Blocked:

```text
candidate family ranking
support/profile/controller ranking
winner selection
repair execution
training repair success
scenario redesign executed
paper-level benchmark result
finite-window-vs-GRU conclusion
level3 self-identification
current-sim verdict
```

## Route Decision

Decision:

```text
source_linked_actionable_target_consolidation_accepted_route_to_branch_synthesis
```

Next milestone:

```text
m2419-paper-route-current-sim-dual-axis-source-linked-offtrack-containment-measured-validation-branch-synthesis
```

M2419 should synthesize M2410-M2418 and decide whether to continue to bounded
source-linked repair-plan materialization, pivot to scenario-quality
reassessment, stop for review, or promote to a new branch. It must not rerun
reset/rollout/localization/consolidation, execute repair, train, rank, or make
paper/self-ID/current-sim verdict claims.
