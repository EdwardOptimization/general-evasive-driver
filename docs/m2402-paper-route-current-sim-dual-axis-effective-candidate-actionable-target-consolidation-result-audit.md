# M2402 Paper-Route Current-Sim Dual-Axis Effective Candidate Actionable Target Consolidation Result Audit

- status: completed
- decision: `effective_candidate_actionable_target_consolidation_accepted_route_to_branch_synthesis`
- manifest: `experiments/manifests/m2402-paper-route-current-sim-dual-axis-effective-candidate-actionable-target-consolidation-result-audit.json`
- parent implementation: `docs/m2401-paper-route-current-sim-dual-axis-effective-candidate-actionable-target-consolidation-implementation.md`
- parent summary: `runs/m2401_paper_route_current_sim_dual_axis_effective_candidate_actionable_target_consolidation/summary.json`
- rerun/new rollout in M2402: `false`
- repair execution/training/replay/PPO: `false`
- support-policy/controller-family/effective-candidate ranking: `false`
- winner selected: `false`
- paper-level/FW-vs-GRU/level3 self-ID/scenario-redesign/training-repair/current-sim verdict claims: `false`

## Audit Result

M2402 accepts M2401 as a complete target-consolidation artifact.

Accepted evidence:

```text
result_class: current_sim_dual_axis_effective_candidate_actionable_target_consolidation_pass
source_slice_row_count: 1313
target_slice_row_count: 1313
consolidated_row_count: 1313
offtrack_repair_target_row_count: 203
collision_guardrail_row_count: 65
r4_mitigation_semantics_row_count: 57
diagnostic_guardrail_row_count: 1034
diagnostic_axis_repair_target_count: 0
r4_ordinary_repair_target_count: 0
ranking_admissible_count: 0
winner_selected_count: 0
guardrail_violation_count: 0
```

M2401 fixed the most important consolidation risk: candidate, profile, pack,
and global slices remained diagnostic guardrails and did not become repair
targets.

## Route Readiness

The consolidated targets are meaningful:

```text
offtrack repair targets:
  centerline
  early_far
  priority_offtrack_containment_repair
  mid timing
  slow_steer_actuator
  offtrack_containment_repair

collision guardrails:
  R5 right_offset
  R5 late_close
  R2 right_offset
  guarded weak_brake
  guarded same_scene_balanced_panel

R4 mitigation semantics:
  R4_unavoidable_mitigation
  unavoidable obstacle label
  guarded R4
  R4 centerline
  R4 early_far
```

These are ready for repair-plan reasoning, but not directly for repair
execution. The branch has also reached the synthesis cadence since M2392.
Therefore M2402 routes to branch synthesis before any repair-plan
materialization.

## Failure Taxonomy

Observed:

```text
driver_outcome_failure: offtrack_dominated_failure
repair_target_surface_identified: 203 offtrack target rows
collision_guardrail_surface_identified: 65 guardrail rows
R4_mitigation_semantics_surface_identified: 57 rows
```

Not observed:

```text
metric_artifact
lineage_invalid
contract_violation
candidate/profile ranking
repair execution
scenario redesign execution
training repair success
```

Local-search status:

```text
synthesis required before continuing:
  M2393-M2402 formed a long reset/measurement/localization/consolidation chain.
  The next ordinary step would start repair planning, so the branch needs a
  synthesis checkpoint first.
```

## Claim Boundary

Supported:

```text
M2401 produced a compact, guarded target-consolidation artifact from M2399
localization rows.

The next valid step is branch synthesis before repair-plan materialization.
```

Blocked:

```text
effective-candidate ranking
controller-family ranking
winner selection
repair execution
training repair success
paper-level benchmark result
finite-window-vs-GRU conclusion
level3 self-identification
scenario redesign executed
current-sim verdict
```

## Route Decision

Decision:

```text
effective_candidate_actionable_target_consolidation_accepted_route_to_branch_synthesis
```

Next milestone:

```text
m2403-paper-route-current-sim-dual-axis-effective-candidate-measured-validation-branch-synthesis
```

M2403 should synthesize M2393-M2402 and decide whether the next branch should
continue to bounded repair-plan materialization, pivot to scenario-quality
reassessment, stop for user review, or promote to a new branch. It must not run
rollout, execute repair, train, rank, or make paper/self-ID/current-sim verdict
claims.
