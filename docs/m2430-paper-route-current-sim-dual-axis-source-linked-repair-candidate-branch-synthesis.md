# M2430 Paper-Route Current-Sim Dual-Axis Source-Linked Repair-Candidate Branch Synthesis

- status: completed
- synthesis decision: `pivot`
- route decision: `pivot_to_current_sim_dual_axis_task_quality_decision_branch`
- manifest: `experiments/manifests/m2430-paper-route-current-sim-dual-axis-source-linked-repair-candidate-branch-synthesis.json`
- synthesized branch: M2425-M2429 source-linked repair-candidate reset/reindex branch
- rerun/reset/new measured rollout/repair/training/replay/PPO: `false`
- candidate/support/controller ranking and winner selection: `false`
- paper/FW-vs-GRU/level3 self-ID/scenario-redesign/training-repair/current-sim verdict claims: `false`

## Evidence Summary

M2425-M2429 closed the source-linked repair-candidate evidence loop without
producing driver improvement evidence.

Reset-only evidence:

```text
M2426 result_class: current_sim_dual_axis_source_linked_repair_candidate_reset_evidence_fail_closed
candidate_overlay_load_count: 4
candidate_family_count: 4
matched_family_count: 3
family_without_match_count: 1
source_effective_candidate_count: 54
matched_effective_candidate_count: 54
source_linked_scenario_reference_count: 2049
unique_reset_target_count: 350
unmatched_source_key_count: 5
environment_reset_attempt_count: 350
environment_reset_success_count: 350
environment_step_count: 0
policy_action_executed: false
guardrail_violation_count: 0
```

The unmatched c04 source key remains:

```text
c04_source_linked_outcome_failure_surface_containment
episode_rows:outcome_bucket:off_track_noncollision_noncompletion
matched_effective_candidate_count: 0
```

Reset-key lineage:

```text
M2427 verified M2426 reset keys exactly equal M2413 measured reset keys.
M2426 reset targets not in M2413: 0
M2413 reset targets not in M2426: 0
```

Measured reindex evidence:

```text
M2428 result_class: current_sim_dual_axis_source_linked_repair_candidate_measured_reindex_pass
source_episode_count: 5250
selected_checkpoint_count: 15
source_reset_target_count: 350
source_measured_reset_target_count: 350
exact_reset_key_coverage: true
reindexed_membership_row_count: 13050
matched_candidate_family_count: 3
expected_matched_candidate_family_count: 3
excluded_candidate_count: 1
c04_included_as_measured: false
ranking_admissible_count: 0
winner_selected_count: 0
guardrail_violation_count: 0
```

Matched candidate outcomes:

```text
c01_source_linked_geometry_timing_containment:
  success_rate: 0.06689655172413793
  collision_rate: 0.16114942528735632
  offtrack_rate: 0.7583908045977011
  dominant_failure_mode: offtrack_dominated_failure

c02_source_linked_hidden_dynamics_response_containment:
  success_rate: 0.06
  collision_rate: 0.09547619047619048
  offtrack_rate: 0.8269047619047619
  dominant_failure_mode: offtrack_dominated_failure

c03_source_linked_role_conditioned_containment:
  success_rate: 0.078
  collision_rate: 0.08933333333333333
  offtrack_rate: 0.8162222222222222
  dominant_failure_mode: offtrack_dominated_failure
```

## Supported Claims

Supported:

```text
The M2425-M2429 branch completed source-linked repair-candidate reset and
measured-result reindex evidence without violating guardrails.

The matched c01/c02/c03 subset is executable and already measured through the
M2413 denominator; no rerun was needed.

The c04 outcome-failure-surface candidate remains a source-coverage gap, not an
executable measured family.

The matched subset remains offtrack-dominated across all three candidate slices.

The correct next step is a branch pivot, not another artifact-only local repair
or direct training/PPO.
```

This advances workflow and scenario/task-quality evidence. It does not advance
engineering driver performance, mechanism evidence for history dependence, or a
paper/current-sim verdict.

## Falsified Claims

Falsified or blocked:

```text
The source-linked repair-candidate branch improved the driver:
  blocked by offtrack-dominated measured reindex results.

The branch is ready for candidate-family ranking:
  blocked because all matched slices are diagnostic-only and offtrack-dominated.

All four candidate families have measured coverage:
  blocked because c04 has zero matched effective candidates.

Another ordinary reindex/adapter/audit will add meaningful evidence:
  blocked by local-search guard; the same offtrack blocker has repeated.

Direct training/PPO from this branch is justified:
  blocked because the available evidence is task-quality negative, not a repair
  objective or promotion candidate.

Current-sim, paper-level, finite-window-vs-GRU, or level3 self-ID verdict:
  blocked because this branch contains no fair controller comparison, no
  history intervention, no private holdout, and no driver improvement.
```

## Failure Taxonomy Summary

Observed:

```text
driver_outcome_failure:
  c01/c02/c03 measured slices remain offtrack-dominated.

source_coverage_gap:
  c04 outcome-failure-surface containment has zero executable source coverage.

local_search_guard_triggered:
  continuing with another source-linked adapter/reindex/audit would be local
  search rather than evidence expansion.
```

Not observed:

```text
lineage_invalid
contract_violation
metric_artifact in M2428
scenario_sampling_failure in the reset/reindex artifacts
active config overwrite
repair execution
training repair success
replay/PPO
candidate/profile/controller ranking
winner selection
hidden/oracle actor-input injection
```

## Public Gate Overfit Risk

Risk level: `high` if this branch continues as source-linked local repair.

Why:

```text
The branch has repeatedly transformed the same public current-sim offtrack
surface through reset evidence, candidate overlays, measured reindexing, and
audits. The transformations were useful for provenance and guardrails, but the
measured outcome stayed offtrack-dominated.
```

Required mitigation:

```text
Do not add another source-linked repair-candidate adapter, reindex, or
candidate-ranking step.

Do not train or run PPO from this branch.

Move to a task-quality decision branch that compares the repeated offtrack
pattern across existing measured panels and decides whether current-sim task
semantics need reassessment before more repair.
```

## Actual Progress Versus Process Overhead

Actual capability changed:

```text
Before M2425, the project had four compact source-linked repair-candidate
overlays that were structurally loadable but not reset/materialized as measured
evidence.

After M2429, the project knows that 3/4 candidate families reset cleanly,
exactly match an existing measured denominator, and still produce
offtrack-dominated measured slices; it also knows c04 is not covered.
```

Process overhead:

```text
medium-high
```

Reason:

```text
The branch made real lineage and guardrail progress, but several consecutive
steps were artifact transformations around the same public offtrack surface.
Another same-family artifact step would not change the paper-route verdict
distance.
```

Paper verdict delta:

```text
positive for task-quality diagnosis, negative/neutral for driver capability.
```

It brings the paper route closer to a current-sim task-quality decision, not to
a positive driver or self-ID result.

## Next Branch Decision

Synthesis decision:

```text
pivot
```

New branch:

```text
paper_route_current_sim_dual_axis_task_quality_decision
```

Next milestone:

```text
m2431-paper-route-current-sim-dual-axis-task-quality-decision-panel-implementation
```

M2431 should build a decision panel from existing measured artifacts:

```text
M2362 repaired-pack measured execution
M2397 effective-candidate measured validation
M2413 source-linked measured validation
M2428 matched repair-candidate measured reindex
M2426 c04 source-coverage caveat
```

Allowed M2431 claims:

```text
current-sim task-quality decision panel generation
cross-artifact offtrack-dominance reanalysis
c04 source-coverage gap preservation
route recommendation for task-semantics reassessment versus more local repair
```

Blocked M2431 claims:

```text
new measured rollout
repair execution
training/PPO
candidate/controller ranking
winner selection
paper-level benchmark result
finite-window-vs-GRU conclusion
level3 self-identification
scenario redesign executed
training repair success
current-sim verdict
```

If M2431 confirms repeated offtrack dominance across the existing panels, the
next audit should decide a task-semantics reassessment route before any more
source-linked local repair.
