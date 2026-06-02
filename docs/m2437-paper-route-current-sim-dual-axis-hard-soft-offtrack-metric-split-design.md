# M2437 Paper-Route Current-Sim Dual-Axis Hard/Soft Offtrack Metric Split Design

- status: completed
- decision: `hard_soft_offtrack_metric_split_design_route_to_implementation`
- manifest: `experiments/manifests/m2437-paper-route-current-sim-dual-axis-hard-soft-offtrack-metric-split-design.json`
- source synthesis: `docs/m2436-paper-route-current-sim-dual-axis-boundary-threshold-sensitivity-panel-result-audit.md`
- new measured rollout/reset/repair/training/replay/PPO: `false`
- actual success improvement claim: `false`
- candidate/controller ranking and winner selection: `false`
- paper/FW-vs-GRU/level3 self-ID/scenario-redesign/training-repair/current-sim verdict claims: `false`

## Purpose

M2437 converts the M2431-M2436 task-quality branch into an explicit
task-boundary metric contract before any implementation, scenario redesign,
measured rollout, repair, training, or controller-family comparison.

M2435 showed that positive-clearance, low-overshoot road-boundary termination is
highly threshold-sensitive:

```text
thresholds_m: [0.02, 0.05, 0.10, 0.20]
min_soft_success_gain_at_0_20m: 0.7175925925925926
min_counterfactual_soft_success_rate_at_0_20m: 0.7827777777777778
max_counterfactual_soft_success_rate_at_0_20m: 0.8752562225475842
max_actual_success_rate: 0.06685714285714285
```

That is strong task-boundary evidence, but not driver-performance evidence.
M2437 therefore defines the hard/soft offtrack split and the claim boundary
needed for the next implementation milestone.

## Metric Semantics

### Actual Success

`actual_success` means an executed rollout outcome under the selected metric.

It must never be created by counterfactual relabeling of an old episode row. If
an old offtrack row is reclassified for analysis, the original measured
`actual_success` value remains unchanged.

### Collision Or Obstacle-Risk Failure

`collision_or_obstacle_risk_failure` is a hard failure when any obstacle safety
condition is violated:

```text
collision == true
or min_clearance_margin <= 0
or the selected future implementation marks obstacle low-clearance risk as hard
```

This class has priority over offtrack softness. A boundary-tolerated row cannot
be treated as soft if it also has collision or nonpositive clearance.

### Hard Offtrack Failure

`hard_offtrack_failure` is a severe road-boundary violation and remains a hard
failure even if obstacle clearance is positive.

The initial implementation should treat it as true when:

```text
episode is offtrack or road-boundary terminated
and no higher-priority collision/risk failure was already assigned
and max_off_track_overshoot > hard_offtrack_threshold_m
```

The initial hard threshold should be configurable, with `0.20 m` as the
starting analysis threshold because M2435 evaluated it explicitly. The threshold
is not a per-profile tuning knob and must be reported in every artifact.

Future measured-rollout configs may add stricter nonrecoverable/out-of-corridor
conditions, but M2438 should remain a classification panel over existing rows.

### Soft Offtrack Violation

`soft_offtrack_violation` is a positive-clearance, low-road-boundary-overshoot
event:

```text
episode is offtrack or road-boundary terminated
and collision == false
and min_clearance_margin > 0
and 0 <= max_off_track_overshoot <= soft_offtrack_threshold_m
```

Soft offtrack is a diagnostic severity class. It may support task redesign and
future metric selection, but it is not actual success in old artifacts.

The initial implementation should compute all M2435 thresholds:

```text
0.02 m
0.05 m
0.10 m
0.20 m
```

### Boundary-Tolerated Diagnostic

`boundary_tolerated_diagnostic` is an analysis-only label for rows that would be
accepted under a given soft boundary threshold.

It exists to quantify task-boundary sensitivity. It must not be reported as
`actual_success`, a driver improvement, a controller-family ranking signal, or a
paper/current-sim verdict.

## Priority Order

Future implementations should use this classification order:

```text
1. Preserve measured actual_success unchanged.
2. Assign collision_or_obstacle_risk_failure for collision or nonpositive
   clearance.
3. Assign hard_offtrack_failure for severe road-boundary violation.
4. Assign soft_offtrack_violation for positive-clearance low-overshoot
   road-boundary events.
5. Assign boundary_tolerated_diagnostic for threshold-specific diagnostic
   relabeling.
```

This order keeps obstacle safety ahead of road-boundary tolerance and prevents
soft-success leakage into actual success.

## Required Implementation Columns

M2438 should add explicit columns rather than changing the simulator
termination contract immediately:

```text
source_id
episode_key or row key
threshold_m
actual_success_preserved
collision_or_obstacle_risk_failure
hard_offtrack_failure
soft_offtrack_violation
boundary_tolerated_diagnostic
counterfactual_soft_success
min_clearance_margin
max_off_track_overshoot
claim_boundary_guardrail_violation
```

`counterfactual_soft_success` must be diagnostic-only and should be true only
when the row is actual-success preserved or boundary-tolerated under the
explicit threshold. The artifact must include guardrails proving this field did
not overwrite actual success.

## Threshold Policy

M2438 should use a fixed threshold grid:

```text
[0.02, 0.05, 0.10, 0.20]
```

The grid exists for sensitivity analysis. It must be shared across sources and
must not be tuned separately for M2362, M2397, M2413, candidate families,
controller families, or profiles.

The threshold selected for later measured rollout, if any, must be chosen by a
separate audit or design milestone. M2437 does not select a final deployed road
boundary tolerance.

## Admission Criteria For M2438

M2438 may pass only if it:

```text
reads existing M2362, M2397, and M2413 primary episode rows;
does not run measured rollout, reset rerun, repair, training, replay, or PPO;
preserves measured actual_success exactly;
computes hard/soft/diagnostic columns for all required thresholds;
keeps candidate/profile/controller axes non-ranking;
reports guardrail violations, if any;
produces summary, panel rows, decision rows, tests, docs, and review artifact;
chooses a bounded result-audit route or stops.
```

M2438 must fail if it:

```text
treats counterfactual soft success as actual success;
claims driver improvement;
claims scenario redesign was executed;
ranks candidate families or controller families;
selects a winner;
changes actor input/output contract;
routes directly to training/PPO before the metric implementation is audited.
```

## Supported Claims

Supported:

```text
M2437 defines a hard/soft offtrack metric and termination split.

M2437 preserves that actual success is an executed rollout outcome only.

M2437 admits a bounded implementation/relabel panel over existing rows.
```

Blocked:

```text
driver improvement
actual success improvement
new measured rollout result
repair execution
training repair success
candidate/controller ranking
winner selection
paper-level benchmark result
finite-window-vs-GRU conclusion
level3 self-identification
scenario redesign executed
current-sim verdict
```

## Next Route

Next milestone:

```text
m2438-paper-route-current-sim-dual-axis-hard-soft-offtrack-metric-split-implementation
```

M2438 should implement the classification/relabel panel described above. It is
not an environment termination change, measured rollout, repair route, training
route, or controller comparison.
