# M2462 Paper-Route Current-Sim Dual-Axis Scenario-Quality Discriminant Branch Synthesis

- status: completed
- synthesis decision: `continue`
- route decision: `continue_to_concrete_overlay_reset_validation_design`
- manifest: `experiments/manifests/m2462-paper-route-current-sim-dual-axis-scenario-quality-discriminant-branch-synthesis.json`
- synthesized branch: M2452-M2461 scenario-quality discriminant branch
- next milestone: `m2463-paper-route-current-sim-dual-axis-scenario-quality-concrete-overlay-reset-validation-design`
- reset/rollout/policy action/scenario-redesign execution/repair/training/replay/PPO: `false`
- ranking/winner selection: `false`
- actual-success improvement/paper/FW-vs-GRU/level3 self-ID/scenario-redesign/training-repair/current-sim verdict claims: `false`

## Evidence Summary

M2452-M2461 converted the M2445/M2449 hard-offtrack-dominated measured result
into a bounded scenario-quality reset-readiness route. It did not produce new
closed-loop driver evidence.

```text
M2452:
  discriminant panel pass
  episode_count: 5250
  panel_row_count: 71
  scenario_quality_blocker_count: 7
  possible_repair_plan_candidate_count: 19
  collision_mitigation_guardrail_count: 52
  hidden_dynamics_guardrail_count: 9
  geometry_timing_guardrail_count: 7
  monitoring_only_count: 41
  ranking/winner/guardrail violations: 0

M2453:
  accepted the panel and blocked direct repair/training because stable/AES rows
  were road-boundary dominated:
    R0 actual_success_rate: 0.06111111111111111
    R0 hard_offtrack_rate: 0.9333333333333333
    R1 actual_success_rate: 0.3288888888888889
    R1 hard_offtrack_rate: 0.66

M2454:
  designed role-specific scenario-quality protocol for stable feasibility,
  stable AES, geometry/timing, handling-limit, hidden-dynamics, and mitigation
  guardrails.

M2455:
  materialization pass
  candidate_row_count: 30
  stable_feasibility_support_count: 3
  stable_aes_support_count: 3
  geometry_timing_guardrail_count: 7
  handling_limit_guardrail_count: 5
  hidden_dynamics_guardrail_count: 9
  mitigation_guardrail_count: 3
  guardrail/ranking/winner violations: 0

M2456:
  accepted protocol materialization and required reset/static preflight mapping
  before measured rollout.

M2457:
  designed fail-closed reset/static preflight: all rows get static checks, but
  only rows with concrete numeric overlays can enter reset validation.

M2458:
  adapter static pass, reset blocked
  source_candidate_row_count: 30
  preflight_work_item_count: 30
  static_check_row_count: 246
  static_check_fail_count: 0
  reset_required_count: 6
  concrete_overlay_available_count: 0
  reset_attempted_count: 0
  reset_blocked_missing_concrete_overlay_count: 6
  guardrail/ranking/winner violations: 0

M2459:
  accepted M2458 and classified missing concrete overlays as scenario-spec
  readiness blockers, not driver failures.

M2460:
  designed two concrete overlay families:
    R0_stable_avoidable: speed [8.0, 12.0], distance [34.0, 52.0],
      lateral offset [-0.25, 0.25], half width [0.45, 0.65]
    R1_aeb_infeasible_stable_aes: speed [10.0, 14.0], distance [20.0, 34.0],
      lateral offset [-0.40, 0.40], half width [0.55, 0.80]
  both use track_width 7.5 and soft_offtrack_tolerance_m 0.20

M2461:
  overlay materialization preflight pass
  target_preflight_row_count: 6
  concrete_overlay_row_count: 6
  candidate_rows_with_overlay_count: 6
  adapter_concrete_overlay_available_count: 6
  adapter_static_check_fail_count: 0
  adapter_reset_required_count: 6
  adapter_reset_attempted_count: 0
  adapter_reset_blocked_missing_concrete_overlay_count: 0
  guardrail_violation_count: 0
```

Paper-route axis classification:

```text
engineering driver performance:
  unchanged; no new closed-loop policy action or measured rollout occurred.

mechanism evidence for history dependence:
  unchanged; no wrong-history, reset-hidden, finite-window, GRU, or
  same-current/different-history test occurred.

scenario/task-quality evidence:
  improved. The branch reduced a broad stable/AES task-quality blocker into six
  concrete reset-ready overlay rows while preserving guardrails.

high-fidelity validation readiness:
  not ready. Current-sim reset validation and later measured execution are
  still prerequisites before any high-fidelity validation layer.

workflow or complexity reduction:
  improved. The branch converted a broad 71-row discriminant panel and
  30-row protocol materialization into a bounded six-row reset-validation
  design target.
```

## Supported Claims

Supported:

```text
The scenario-quality discriminant branch has a complete artifact lineage from
M2452 panel through M2461 overlay materialization.

The stable/AES missing-overlay blocker is resolved at preflight level:
concrete_overlay_available_count moved from 0 to 6 and
reset_blocked_missing_concrete_overlay_count moved from 6 to 0.

The actor-input contract and claim boundaries remained clean throughout the
branch: labels did not enter actor input, policy action was not executed,
ranking/winner counts stayed zero, and guardrail violations stayed zero.

The branch is ready for a bounded reset-validation design over exactly the six
M2461 concrete-overlay stable/AES rows.
```

This is scenario/task-quality and workflow-readiness evidence. It is not driver
capability evidence.

## Falsified Claims

Falsified or still blocked:

```text
Stable/AES driving is solved:
  still blocked because M2461 did not execute reset or rollout, and the last
  measured stable/AES evidence from M2452 remains hard-offtrack dominated.

M2461 proves reset success:
  blocked because reset_attempted_count is 0 by design.

M2461 proves measured actual success or driver improvement:
  blocked because no policy action or measured rollout occurred.

Soft-boundary tolerance alone fixes the current-sim task:
  already falsified by the M2445/M2451 route and not repaired by this branch.

Scenario redesign was executed:
  blocked because this branch only designed and materialized protocol/overlay
  artifacts.

Controller/profile/checkpoint/scenario candidate ranking:
  blocked by ranking_admissible_count 0 and winner_selected_count 0.

Current-sim, paper, FW-vs-GRU, training-repair, or level3 self-ID verdict:
  blocked because this branch is scenario-quality infrastructure, not a
  comparative controller or history-necessity study.
```

## Failure Taxonomy Summary

Observed or preserved:

```text
scenario_sampling_failure / task-quality blocker:
  M2452 showed stable/AES rows were hard-offtrack dominated. M2461 only makes a
  reset-validation route possible; it does not prove those rows are solved.

metric_artifact:
  soft-boundary tolerance and old-row relabeling remain diagnostic-only and
  cannot be treated as actual success.

local_search_guard_risk:
  this branch reached cadence after panel, audit, protocol design,
  materialization, audit, preflight design, adapter, audit, overlay design, and
  overlay materialization.
```

Not observed:

```text
contract_violation:
  no actor-input contract change or hidden/oracle actor feature was introduced.

behavior_regression from training:
  no training or repair was run.

private holdout misuse:
  no private holdout was used.
```

## Public Gate Overfit Risk

Risk before synthesis: `high`.

Reason:

```text
The branch spent ten milestones around public-debug/public-gate artifacts from
the M2445/M2449 measured result. Continuing with another ordinary audit or
artifact-only design without synthesis would optimize process state around a
fixed public surface.
```

Risk after synthesis: `medium`.

Mitigation:

```text
The next route is not repair, training, ranking, or measured rollout. It is a
bounded reset-validation design that must test executable environment reset
readiness for exactly the six concrete overlay rows, preserve all guardrail
groups as static-only, and fail closed before policy action.
```

Residual risk:

```text
The six overlay rows are still derived from public branch artifacts. Reset
validation can only establish scenario-spec reset readiness; later measured
execution must use a separately audited workload before any driver-performance
claim.
```

## Actual Progress Versus Process Overhead

Actual progress:

```text
The project now has concrete, statically admissible overlay rows for the six
stable/AES reset-required work items. The previous missing-overlay blocker is
gone at preflight level.
```

Process overhead:

```text
high
```

Reason:

```text
The branch required many process milestones because it avoided treating
diagnostic panels, protocol metadata, or overlay rows as closed-loop success.
The overhead is justified up to M2462 because it prevented direct repair,
training, or ranking from under-specified stable/AES task-quality artifacts.
Further overhead should be capped by moving to reset-validation design and then
reset-only execution evidence, not more artifact relabeling.
```

## Next Branch Decision

Synthesis decision:

```text
continue
```

Branch:

```text
paper_route_current_sim_dual_axis_scenario_quality_discriminant
```

Next milestone:

```text
m2463-paper-route-current-sim-dual-axis-scenario-quality-concrete-overlay-reset-validation-design
```

M2463 should design reset-only validation over exactly the six M2461 concrete
overlay rows. The design must specify target rows, expected observation
contract checks, output artifacts, pass/fail criteria, and fail-closed result
audit routing. It must keep geometry/timing, handling-limit, hidden-dynamics,
and mitigation guardrail rows static-only. It must not execute reset, rollout,
policy actions, scenario redesign, repair, training, replay, PPO, ranking,
winner selection, paper/FW-vs-GRU/self-ID/training-repair verdict, or current-
sim verdict claims.
