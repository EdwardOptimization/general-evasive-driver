# M2419 Paper-Route Current-Sim Dual-Axis Source-Linked Offtrack Containment Measured Validation Branch Synthesis

- status: completed
- synthesis decision: `continue`
- route decision: `continue_to_source_linked_bounded_repair_plan_materialization`
- manifest: `experiments/manifests/m2419-paper-route-current-sim-dual-axis-source-linked-offtrack-containment-measured-validation-branch-synthesis.json`
- parent synthesis: `docs/m2409-paper-route-current-sim-dual-axis-repair-plan-materialization-branch-synthesis.md`
- parent reset summary: `runs/m2410_paper_route_current_sim_dual_axis_source_linked_offtrack_containment_reset_evidence/summary.json`
- parent measured summary: `runs/m2413_paper_route_current_sim_dual_axis_source_linked_offtrack_containment_measured_validation/summary.json`
- parent localization summary: `runs/m2415_paper_route_current_sim_dual_axis_source_linked_offtrack_containment_measured_outcome_localization/summary.json`
- parent consolidation summary: `runs/m2417_paper_route_current_sim_dual_axis_source_linked_offtrack_containment_actionable_target_consolidation/summary.json`
- rerun/new rollout in M2419: `false`
- reset/repair/training/replay/PPO: `false`
- family/profile/controller ranking and winner selection: `false`
- paper/FW-vs-GRU/level3 self-ID/scenario-redesign/training-repair/current-sim verdict claims: `false`

## Evidence Summary

M2410-M2418 converted the four source-linked offtrack containment family
surface into reset evidence, a measured validation panel, outcome localization,
and compact target/guardrail consolidation.

Reset evidence:

```text
M2410 result_class: current_sim_dual_axis_source_linked_offtrack_containment_reset_evidence_pass
matched_family_count: 4
source_linked_scenario_reference_count: 3505
unique_reset_target_count: 350
environment_reset_success_count: 350
guardrail_violation_count: 0
```

Measured validation:

```text
M2413 result_class: current_sim_dual_axis_source_linked_offtrack_containment_measured_validation_pass
episode_count: 5250
selected_checkpoint_count: 15
failure_count: 0
validation_failure_count: 0
guardrail_violation_count: 0
role_success_rate: 0.06685714285714285
offtrack_rate: 0.7424761904761905
collision_rate: 0.1761904761904762
dominant_failure_mode: offtrack_dominated_failure
```

Outcome localization:

```text
M2415 result_class: current_sim_dual_axis_source_linked_offtrack_containment_measured_outcome_localization_pass
source_episode_count: 5250
source_family_membership_row_count: 18300
slice_row_count: 2844
offtrack_target_slice_count: 272
collision_guardrail_slice_count: 114
r4_mitigation_semantics_slice_count: 49
max_step_noncompletion_slice_count: 325
speed_too_low_slice_count: 124
guardrail_violation_count: 0
```

Target consolidation:

```text
M2417 result_class: current_sim_dual_axis_source_linked_offtrack_containment_actionable_target_consolidation_pass
consolidated_row_count: 2844
offtrack_repair_target_row_count: 59
collision_guardrail_row_count: 30
r4_mitigation_semantics_row_count: 43
max_step_noncompletion_row_count: 1
speed_too_low_row_count: 1
diagnostic_guardrail_row_count: 2733
family_membership_diagnostic_row_count: 110
family_axis_repair_target_count: 0
profile_axis_repair_target_count: 0
ranking_admissible_count: 0
winner_selected_count: 0
guardrail_violation_count: 0
```

## Supported Claims

Supported:

```text
The source-linked family surface is reset-valid at the concrete env-config
level.

The source-linked measured panel is complete and clean enough to interpret
outcome quality.

The measured outcome remains poor and offtrack-dominated; this is not a
metadata, validation, or guardrail artifact.

The offtrack blocker has been localized and consolidated into bounded target
categories with collision, R4, max-step, speed-too-low, and diagnostic
guardrails separated.

Family-membership and profile rows remained diagnostic and were not converted
into rankings, winners, or repair targets.

The next admissible route is bounded repair-plan materialization, not repair
execution.
```

This advances scenario/task-quality evidence and workflow evidence. It is not
engineering driver improvement, controller-family comparison, self-ID evidence,
or a paper/current-sim verdict.

## Falsified Claims

Falsified or blocked:

```text
source-linked offtrack containment families solve the current-sim driver
outcome blocker:
  falsified for this panel by role_success_rate 0.06686 and offtrack_rate
  0.74248.

M2413 can be used for family/profile ranking:
  blocked by overlapping family-membership rows and non-ranking guardrails.

M2417 target consolidation is repair execution:
  blocked because no repair lever, active config overwrite, training, replay,
  PPO, or rollout rerun occurred.

L3 online GRU or finite-window-vs-GRU conclusion is supported:
  blocked because this branch has no controlled controller-family comparison
  and no history intervention.

scenario redesign or training repair has succeeded:
  blocked because no redesign, repair execution, training, replay, or PPO ran.

current-sim verdict is ready:
  blocked because outcome quality is still offtrack-dominated.
```

## Failure Taxonomy Summary

Observed failure classes:

```text
driver_outcome_failure: offtrack_dominated_failure
task_quality_blocker: source-linked panel does not yet produce acceptable closed-loop success
repair_target_surface_identified: 59 offtrack target rows
collision_guardrail_signal: 30 guardrail rows
R4_mitigation_semantics_surface_identified: 43 rows
max_step_noncompletion_surface_identified: 1 row
speed_too_low_surface_identified: 1 row
```

Not observed in this branch:

```text
metric_artifact
lineage_invalid
contract_violation
artifact-construction scenario_sampling_failure
family/profile/controller ranking
winner selection
repair execution
training repair success
hidden/oracle actor-input injection
```

## Public Gate Overfit Risk

Risk level: `medium`.

Why:

```text
The branch repeatedly reprocessed one public source-linked measured panel. The
sequence produced useful reset, measured, localization, and consolidation
artifacts, but another ordinary reanalysis step would be local search rather
than new evidence.
```

Mitigation required for the next branch:

```text
M2420 may materialize a bounded repair plan from M2417 targets, but it must not
rank source-linked families, profiles, or checkpoints.

Every proposed repair lever must preserve collision guardrails, R4 mitigation
semantics, max-step and speed-too-low stop rules, no actor input change, and no
hidden/oracle actor-feature injection.

If the plan is mostly scenario semantics rather than executable repair
material, the next audit should pivot to scenario-quality reassessment instead
of training.
```

## Actual Progress Versus Process Overhead

Actual capability changed:

```text
Before this branch, the four offtrack containment families were compact
semantic overlays with read-only adapter validation.

After this branch, the project has source-linked concrete reset evidence, a
complete 5250-episode measured panel, outcome localization, and compact
source-linked repair-target/guardrail categories.
```

Process overhead:

```text
medium
```

Reason:

```text
The branch used nine milestones from M2410 through M2418. Most steps produced
new reset, measured, localization, or consolidation artifacts, but continuing
with another ordinary artifact reanalysis would now be local search. Synthesis
is the right boundary before repair-plan materialization.
```

Paper verdict delta:

```text
moved from reset-ready source-linked families to a clean negative current-sim
outcome diagnosis with bounded repair targets.
```

It does not move the paper route to a positive controller result.

## Next Branch Decision

Synthesis decision:

```text
continue
```

Bounded next route:

```text
m2420-paper-route-current-sim-dual-axis-source-linked-bounded-repair-plan-materialization-implementation
```

M2420 should materialize an artifact-only source-linked repair plan from M2417
target and guardrail rows. It should produce tables that map:

```text
offtrack repair target categories -> bounded repair levers and acceptance gates
collision guardrail rows -> non-regression constraints
R4 mitigation semantics -> separate mitigation metrics and stop rules
max-step/speed-too-low rows -> noncompletion and low-speed stop rules
diagnostic rows -> non-ranking monitoring only
family-membership rows -> overlapping source diagnostics only
```

M2420 must not execute repair, train, rerun measured validation, rank families
or profiles, overwrite active configs, or claim scenario redesign or training
repair success.

Stop conditions for the next route:

```text
stop if repair levers cannot be separated from family/profile ranking
stop if offtrack repair would ignore collision, R4, max-step, or speed-too-low
guardrails
stop if the plan requires actor input contract changes
stop if the plan only restates M2417 tables without choosing bounded repair
levers and acceptance gates
```
