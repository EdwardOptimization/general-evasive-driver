# M2403 Paper-Route Current-Sim Dual-Axis Effective Candidate Measured Validation Branch Synthesis

- status: completed
- synthesis decision: `continue`
- route decision: `continue_to_bounded_repair_plan_materialization`
- manifest: `experiments/manifests/m2403-paper-route-current-sim-dual-axis-effective-candidate-measured-validation-branch-synthesis.json`
- parent synthesis: `docs/m2392-paper-route-current-sim-dual-axis-effective-config-materialization-branch-synthesis.md`
- parent measured summary: `runs/m2397_paper_route_current_sim_dual_axis_effective_candidate_measured_validation/summary.json`
- parent localization summary: `runs/m2399_paper_route_current_sim_dual_axis_effective_candidate_measured_outcome_localization/summary.json`
- parent consolidation summary: `runs/m2401_paper_route_current_sim_dual_axis_effective_candidate_actionable_target_consolidation/summary.json`
- rerun/new rollout in M2403: `false`
- repair execution/training/replay/PPO: `false`
- support-policy/controller-family/effective-candidate ranking: `false`
- winner selected: `false`
- paper-level/FW-vs-GRU/level3 self-ID/scenario-redesign/training-repair/current-sim verdict claims: `false`

## Evidence Summary

M2393-M2402 converted run-dir-only effective candidate artifacts into a complete
measured-validation and target-localization evidence chain.

Reset readiness:

```text
M2394 result_class: current_sim_dual_axis_effective_candidate_reset_validation_adapter_pass
source_candidate_config_count: 54
candidate_scenario_reference_count: 2049
unique_reset_target_count: 350
environment_reset_success_count: 350
candidate_reset_pass_count: 54
environment_step_count: 0
guardrail_violation_count: 0
```

Measured validation:

```text
M2397 result_class: current_sim_dual_axis_effective_candidate_measured_validation_pass
episode_count: 30735
source_candidate_count: 54
unique_pack_scenario_count: 350
selected_checkpoint_count: 15
failure_count: 0
validation_failure_count: 0
metadata_missing_count: 0
metric_completeness_failure_count: 0
actor_contract_violation_count: 0
guardrail_violation_count: 0
success_rate: 0.04054010086220921
offtrack_rate: 0.8425898812428827
collision_rate: 0.10157800553115341
dominant_failure_mode: offtrack_dominated_failure
```

Outcome localization:

```text
M2399 result_class: current_sim_dual_axis_effective_candidate_measured_outcome_localization_pass
source_episode_count: 30735
slice_row_count: 1313
offtrack_target_slice_count: 1132
collision_guardrail_slice_count: 364
r4_mitigation_semantics_slice_count: 57
diagnostic_only_slice_count: 96
high_priority_offtrack_slice_count: 658
guardrail_violation_count: 0
```

Target consolidation:

```text
M2401 result_class: current_sim_dual_axis_effective_candidate_actionable_target_consolidation_pass
source_slice_row_count: 1313
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

## Supported Claims

Supported:

```text
The effective-candidate artifacts are reset-valid and measured-valid at the
artifact level.

The measured panel is complete and clean enough to interpret outcome quality.

The current outcome quality is poor and offtrack-dominated, not a metric or
lineage artifact.

The offtrack blocker has been localized into bounded target categories, with
separate collision guardrails and R4 mitigation semantics.

Candidate, profile, pack, and global axes remained diagnostic-only and were not
converted into rankings or repair targets.

The next admissible route is bounded repair-plan materialization, not direct
repair execution.
```

This is scenario/task-quality evidence and workflow evidence. It is not driver
performance success and not self-identification evidence.

## Falsified Claims

Falsified or blocked by the branch:

```text
effective candidates solve the current-sim driver outcome blocker:
  falsified for this panel by success_rate 0.04054 and offtrack_rate 0.84259.

M2397 can be used for effective-candidate ranking:
  blocked by non-ranking guardrails and diagnostic-only profile/candidate axes.

L3_online_gru success aggregate proves finite-window-vs-GRU:
  blocked because this was not a controlled controller-family verdict protocol.

M2393-M2402 provides level3 self-identification:
  blocked because no wrong-history/reset/finite-window history-necessity test
  was run in this branch.

scenario redesign or training repair has succeeded:
  blocked because no redesign, repair execution, training, replay, or PPO ran.

current-sim verdict is ready:
  blocked because measured outcome quality is still offtrack-dominated.
```

## Failure Taxonomy Summary

Observed failure classes:

```text
driver_outcome_failure: offtrack_dominated_failure
task_quality_blocker: effective-candidate panel does not yet produce acceptable closed-loop success
collision_guardrail_signal: collision-heavy R4 and selected R2/R5/weak-brake slices
repair_target_surface_identified: 203 offtrack repair target rows
R4_mitigation_semantics_surface_identified: 57 rows
```

Not observed in this branch:

```text
metric_artifact
lineage_invalid
contract_violation
artifact-construction scenario_sampling_failure
candidate/profile ranking
winner selection
repair execution
training repair success
```

## Public Gate Overfit Risk

Risk level: `medium`.

Why:

```text
The branch used a single measured panel and then repeatedly reanalyzed its
public artifacts. The reanalysis produced useful target categories, but another
ordinary localization/consolidation milestone would be local search rather than
new evidence.
```

Mitigation required for the next branch:

```text
M2404 may materialize a bounded repair plan from M2401 targets, but must not
rank candidates/profiles, tune a specific winner, or execute repair.

Every proposed repair lever must name the guardrail it must preserve: collision
guardrails, R4 mitigation semantics, no actor input change, and no hidden/oracle
feature injection.

If the repair plan is mostly scenario semantics rather than driver/controller
repair, the next audit should pivot to scenario-quality reassessment instead of
training.
```

## Actual Progress Versus Process Overhead

Actual capability changed:

```text
Before this branch, effective candidate artifacts were run-dir materializations
without reset and measured outcome evidence.

After this branch, the project has reset validation, a complete 30735-episode
measured panel, outcome localization, and compact target/guardrail categories
for the next repair-plan step.
```

Process overhead:

```text
medium
```

Reason:

```text
The branch spent 10 milestones, but most of them produced new artifacts or
audited boundaries that prevented ranking and verdict shortcuts. Continuing
with another ordinary reanalysis would become local search, so synthesis is the
right boundary.
```

Paper verdict delta:

```text
moved from unmeasured effective-candidate artifacts to a clean negative
current-sim outcome diagnosis with bounded repair targets.
```

It does not move the paper route to a positive controller result.

## Next Branch Decision

Synthesis decision:

```text
continue
```

Bounded next route:

```text
m2404-paper-route-current-sim-dual-axis-bounded-repair-plan-materialization-implementation
```

M2404 should materialize an artifact-only repair plan from M2401 target and
guardrail rows. It should produce tables that map:

```text
offtrack repair target categories -> candidate repair levers and acceptance gates
collision guardrail rows -> non-regression constraints
R4 mitigation semantics -> separate mitigation metrics and stop rules
diagnostic rows -> non-ranking monitoring only
```

M2404 must not execute repair, train, rerun measured validation, rank
candidates/profiles, overwrite active configs, or claim scenario redesign or
training repair success.

Stop conditions for the next route:

```text
stop if repair levers cannot be separated from candidate/profile ranking
stop if offtrack repair would ignore collision or R4 guardrails
stop if the plan requires actor input contract changes
stop if the plan mostly changes scenario semantics rather than driver behavior
stop if another artifact-only step is proposed after M2404 without a result audit
```

The next result audit should decide whether the materialized plan admits a
single bounded implementation experiment, pivots to scenario-quality
reassessment, or stops for user review.
