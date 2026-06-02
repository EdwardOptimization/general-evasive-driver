# M2442 Paper-Route Current-Sim Dual-Axis Task-Boundary Metric Redesign Branch Synthesis

- status: completed
- synthesis decision: `continue`
- route decision: `continue_to_metric_selected_validation_preflight_implementation`
- manifest: `experiments/manifests/m2442-paper-route-current-sim-dual-axis-task-boundary-metric-redesign-branch-synthesis.json`
- synthesized branch: M2437-M2441 task-boundary metric redesign
- rerun/reset/new measured rollout/repair/training/replay/PPO: `false`
- actual success improvement claim: `false`
- candidate/controller ranking and winner selection: `false`
- paper/FW-vs-GRU/level3 self-ID/scenario-redesign/training-repair/current-sim verdict claims: `false`

## Evidence Summary

M2437-M2441 converted the offtrack-dominated current-sim blocker into a
guardrailed metric path:

```text
M2437:
  defined actual_success, collision_or_obstacle_risk_failure,
  hard_offtrack_failure, soft_offtrack_violation, and
  boundary_tolerated_diagnostic semantics.

M2438:
  implemented the hard/soft offtrack metric split panel over existing M2362,
  M2397, and M2413 episode rows.
  actual_success_preserved: true
  guardrail_violation_count: 0
  min_soft_success_gain_at_0_20m: 0.7175925925925926

M2439:
  accepted M2438 as a metric-split implementation and kept old-row soft success
  diagnostic-only.

M2440:
  designed metric-selected measured validation with primary tolerance 0.20 m,
  sensitivity reporting at 0.02/0.05/0.10/0.20 m, and M2413 350 x 15 as the
  primary denominator.

M2441:
  implemented opt-in soft-boundary env support.
  focused tests: 4 passed
  default offtrack behavior preserved.
  actor observation shape preserved.
```

The branch also found a real infrastructure blocker: the original environment
hard-terminated offtrack at `abs(lateral_error) > track_width`. M2441 resolved
that as opt-in infrastructure rather than widening `track_width`, which would
have changed actor-visible road geometry.

## Supported Claims

Supported:

```text
The task-boundary metric split is now specified and implemented.

Counterfactual soft success remains diagnostic-only.

The environment now has opt-in soft-boundary continuation support needed for
fresh measured validation.

The route can continue to a metric-selected validation preflight that produces
fresh workload/reset evidence.
```

This advances scenario/task-quality evidence and infrastructure readiness. It
does not advance driver performance or self-identification evidence.

## Falsified Claims

Falsified or blocked:

```text
Treat old-row soft success as actual success:
  blocked by M2437-M2439 claim boundaries.

Run measured validation by simply widening track_width:
  blocked because that would alter actor-visible road geometry and reward
  normalization.

Claim current-sim verdict from metric split:
  blocked because no fresh metric-selected rollout has run.

Continue with another ordinary same-data relabel/audit:
  blocked by local-search guard and public-overfit risk.

Claim paper/FW-vs-GRU/self-ID result:
  blocked because this branch is task-boundary infrastructure only.
```

## Failure Taxonomy Summary

Observed:

```text
local_search_guard_triggered:
  the branch reached the non-evidence milestone limit and required synthesis.

task_boundary_metric_blocker:
  current-sim offtrack semantics needed a hard/soft split before measured
  validation.
```

Not observed:

```text
contract_violation:
  actual_success was preserved and actor observation shape was unchanged.

metric_artifact in M2441:
  soft-boundary behavior is opt-in and default behavior is preserved.

scenario_sampling_failure:
  no measured-validation sampling was attempted in this branch.

behavior_regression:
  no driver behavior was trained or promoted.
```

## Public Gate Overfit Risk

Risk level before synthesis: `high`.

Reason:

```text
M2438 reused old episode rows; M2439 and M2440 were process decisions; M2441 was
infrastructure. Continuing with another ordinary audit would be local search.
```

Risk mitigation:

```text
Synthesize now.

Continue only to a fresh metric-selected validation preflight that materializes
workload/reset evidence under the opt-in soft-boundary config.

Do not claim actual success until a fresh executed rollout runs under the
selected metric.
```

## Actual Progress Versus Process Overhead

Actual capability changed:

```text
Before M2437, the project had only counterfactual evidence that many offtrack
failures were low-overshoot positive-clearance boundary events.

After M2441, the project has a specified metric split, a classifier panel, a
measured-validation protocol, and tested opt-in env support that can execute
soft-boundary continuation without changing actor inputs.
```

Process overhead:

```text
high but justified
```

Reason:

```text
The branch had several design/audit milestones, but it ended with a concrete env
capability and a clear preflight route. The next milestone must produce fresh
validation-preflight evidence, not another same-data relabel.
```

## Next Branch Decision

Synthesis decision:

```text
continue
```

Next milestone:

```text
m2443-paper-route-current-sim-dual-axis-metric-selected-validation-preflight-implementation
```

M2443 should implement a preflight panel for the M2440 protocol:

```text
materialize M2413-derived workload rows under soft_offtrack_metric_enabled true;
set soft_offtrack_tolerance_m to 0.20;
preserve sensitivity thresholds as diagnostic metadata;
validate config load/build/reset without policy action;
verify actor observation shape compatibility;
write summary/workload/decision artifacts;
route to result audit before any full measured rollout.
```

M2443 must not execute policy rollout, repair, training, ranking, winner
selection, or current-sim/paper/self-ID verdict claims.
