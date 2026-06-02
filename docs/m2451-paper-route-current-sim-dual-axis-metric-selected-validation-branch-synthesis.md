# M2451 Paper-Route Current-Sim Dual-Axis Metric-Selected Validation Branch Synthesis

- status: completed
- synthesis decision: `promote_to_next_branch`
- route decision: `promote_to_scenario_quality_discriminant_panel`
- manifest: `experiments/manifests/m2451-paper-route-current-sim-dual-axis-metric-selected-validation-branch-synthesis.json`
- synthesized branch: M2443-M2450 metric-selected validation branch
- next branch: `paper_route_current_sim_dual_axis_scenario_quality_discriminant`
- rerun/reset/new measured rollout/repair/training/replay/PPO: `false`
- actual success improvement claim: `false`
- candidate/controller/profile/checkpoint/target ranking and winner selection: `false`
- paper/FW-vs-GRU/level3 self-ID/scenario-redesign/training-repair/current-sim verdict claims: `false`

## Evidence Summary

M2443-M2450 converted the soft-boundary metric route into a fresh measured
validation result and then localized that result into target/guardrail artifacts.

```text
M2443:
  preflight pass
  workload: 350 reset targets x 15 selected checkpoints = 5250 cells
  reset_success: 350/350
  policy_action_count: 0
  actor observation shape changed: 0

M2444:
  accepted preflight and admitted bounded measured validation.

M2445:
  fresh metric-selected measured validation pass
  episodes: 5250/5250
  actual_success_rate: 0.06685714285714285
  hard_offtrack_failure_rate: 0.7468571428571429
  soft_offtrack_violation_rate: 0.0032380952380952383
  boundary_tolerated_success_rate: 0.0
  collision_rate: 0.1761904761904762

M2446:
  accepted the measured artifact but classified old-row relabel as
  non-predictive of true soft-boundary execution.

M2447:
  artifact-only outcome localization pass
  localization rows: 65
  dominant pattern: hard_offtrack_dominated

M2448:
  accepted localization as actionable for target consolidation, not direct
  repair or training.

M2449:
  target consolidation pass
  hard_offtrack_target_row_count: 21
  guardrail_row_count: 56
  diagnostic_axis_repair_target_count: 0
  ranking/winner/guardrail violations: 0

M2450:
  accepted M2449 but classified the target surface as broad and task-quality
  related, routing to branch synthesis.
```

## Supported Claims

Supported:

```text
The metric-selected validation route is executable and complete over the 5250
episode denominator.

The fresh metric-selected result is hard-offtrack dominated, not converted into
actual success by the 0.20 m soft-boundary tolerance.

Old hard-termination-row relabeling was diagnostic, not predictive of
closed-loop recovery under true soft-boundary execution.

The hard-offtrack blocker can be summarized into compact target rows with
separate collision, soft-boundary, and monitoring guardrails.

Profile, pack, family/checkpoint, global, termination, and outcome axes remain
diagnostic-only and non-ranking.
```

This advances scenario/task-quality evidence and process discipline. It does
not advance driver capability, self-identification proof, or a current-sim
verdict.

## Falsified Claims

Falsified or blocked:

```text
Old-row soft-boundary relabel predicts fresh actual success:
  falsified by M2445/M2446.

The 0.20 m tolerance alone fixes current-sim validation:
  falsified by actual_success_rate 0.06685714285714285 and
  hard_offtrack_failure_rate 0.7468571428571429.

The target surface is narrow enough for direct repair:
  blocked by M2449/M2450 because targets span role, hidden dynamics,
  geometry/timing, and scenario-label axes.

Target consolidation proves scenario redesign or training repair success:
  blocked because no scenario redesign, repair, or training was executed.

Controller/profile/checkpoint ranking from diagnostic rows:
  blocked by claim boundaries and diagnostic-axis repair target count 0.

Current-sim, paper, FW-vs-GRU, or level3 self-ID verdict:
  blocked because this branch is task-quality validation, not a final
  comparative driver study or history-necessity study.
```

## Failure Taxonomy Summary

Observed:

```text
metric_artifact:
  old-row relabel was useful for diagnosing boundary semantics but not
  predictive of fresh closed-loop recovery.

scenario_sampling_failure / task-quality blocker:
  fresh measured validation remains broad hard-offtrack dominated, including
  ordinary stable/avoidable and AES-feasible target surfaces.

local_search_guard_risk:
  after preflight, measured validation, localization, and consolidation, another
  target-table edit would be local search without a new evidence axis.
```

Not observed:

```text
contract_violation:
  actor observation shape and human-view contract remained unchanged.

behavior_regression from training:
  no training or repair was run.

private holdout misuse:
  no private holdout was used.
```

## Public Gate Overfit Risk

Risk level before synthesis: `high`.

Reason:

```text
The branch has already consumed the metric-selected validation path through
preflight, measured execution, localization, audit, target consolidation, and
audit. Continuing with more artifact-only relabeling in the same branch would
optimize the process around the M2445/M2449 public artifacts rather than answer
whether the scenario distribution, controller family, or task formulation is
the blocker.
```

Mitigation:

```text
Close this branch with promote_to_next_branch.

Start a named scenario-quality discriminant branch whose first artifact is a
panel, not a repair or training run.

Require the next panel to separate stable avoidable, AES feasible,
drift-required, unavoidable, hidden-dynamics, geometry/timing, and collision
guardrail cases without ranking profiles or selecting winners.
```

## Actual Progress Versus Process Overhead

Actual progress:

```text
The project now knows that soft-boundary metric support and old-row relabeling
were insufficient. Fresh execution under the selected metric remains
hard-offtrack dominated.

The blocker has been reduced from raw 5250 episode rows to 21 target rows plus
guardrail tables, but the target surface is broad enough to require a new
scenario-quality evidence branch.
```

Process overhead:

```text
high but justified
```

Reason:

```text
The branch avoided a premature training/repair loop and turned a metric
assumption into a measured negative result with bounded target artifacts.
Further progress now requires a new evidence axis.
```

## Next Branch Decision

Synthesis decision:

```text
promote_to_next_branch
```

Closed branch:

```text
paper_route_current_sim_dual_axis_task_boundary_metric_redesign
```

Next branch:

```text
paper_route_current_sim_dual_axis_scenario_quality_discriminant
```

Next milestone:

```text
m2452-paper-route-current-sim-dual-axis-scenario-quality-discriminant-panel
```

M2452 should build a new artifact-only panel from M2445 episode rows and M2449
target/guardrail rows. It should distinguish scenario-quality blockers from
repair-plan candidates by separating:

```text
stable/avoidable hard-offtrack
AES-feasible hard-offtrack
drift-required hard-offtrack
R4 unavoidable collision/mitigation guardrails
hidden-dynamics collision-dominated cases
geometry/timing hard-offtrack cases
soft-boundary diagnostic-only cases
profile/pack/checkpoint monitoring axes
```

M2452 must not rerun, repair, train, rank, select winners, or make current-sim,
paper, FW-vs-GRU, level3 self-ID, scenario-redesign, or training-repair verdict
claims.
