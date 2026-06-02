# M2440 Paper-Route Current-Sim Dual-Axis Hard/Soft Offtrack Metric-Selected Measured-Validation Design

- status: completed
- decision: `metric_selected_validation_protocol_route_to_soft_boundary_env_support`
- manifest: `experiments/manifests/m2440-paper-route-current-sim-dual-axis-hard-soft-offtrack-metric-selected-measured-validation-design.json`
- parent audit: `docs/m2439-paper-route-current-sim-dual-axis-hard-soft-offtrack-metric-split-result-audit.md`
- new measured rollout/reset/repair/training/replay/PPO: `false`
- actual success improvement claim: `false`
- candidate/controller ranking and winner selection: `false`
- paper/FW-vs-GRU/level3 self-ID/scenario-redesign/training-repair/current-sim verdict claims: `false`

## Design Summary

M2440 defines how to obtain executed rollout evidence under the hard/soft
offtrack metric without confusing old-row relabeling with actual success.

The protocol cannot route directly to measured validation because the current
environment still terminates offtrack as a hard-coded condition:

```text
if abs(frame.lateral_error) > self.config.track_width:
    return "off_track"
```

There is no separate soft-boundary tolerance in `DriftEnvConfig`. Increasing
`track_width` would change the observed road geometry and reward normalization,
so it is not an acceptable proxy for soft-boundary validation. The next required
step is env-level soft-boundary support that leaves actor observation geometry
and the human-view contract unchanged.

## Metric Policy

Primary measured-validation metric:

```text
soft_offtrack_tolerance_m: 0.20
```

Rationale:

```text
M2435/M2438 evaluated 0.20 m explicitly.
At 0.20 m, diagnostic soft-success gain is large.
M2438 still leaves a nonempty hard-offtrack class, so the metric is not a pure
success relabel.
```

Sensitivity reporting must still include:

```text
0.02 m
0.05 m
0.10 m
0.20 m
```

The primary metric uses 0.20 m for execution, but result artifacts must include
the full threshold grid as diagnostics. The threshold is global for the protocol
and must not be tuned by source, profile, checkpoint, or controller family.

## Actual Success Semantics

Under the selected metric, `actual_success_metric_selected` may be counted only
from a fresh executed rollout where soft-boundary continuation was active.

It requires:

```text
obstacle/role completion is satisfied;
collision == false;
min_clearance_margin > 0;
hard_offtrack_failure == false;
non_finite_state == false;
speed/yaw hard safety limits are not violated;
```

It may include:

```text
soft_offtrack_violation == true
```

but only if the violation remains within the selected tolerance and the rollout
continues to a valid completion/recovery outcome.

Old-row `counterfactual_soft_success` remains diagnostic-only and must never be
merged with `actual_success_metric_selected`.

## Failure Semantics

Hard failure:

```text
collision_or_obstacle_risk_failure:
  collision == true or min_clearance_margin <= 0

hard_offtrack_failure:
  abs(lateral_error) > track_width + soft_offtrack_tolerance_m
  or max_off_track_overshoot > soft_offtrack_tolerance_m

hard_dynamics_failure:
  non_finite_state
  speed_too_low
  speed_too_high
  yaw_rate_limit
```

Soft violation:

```text
soft_offtrack_violation:
  abs(lateral_error) > track_width
  and abs(lateral_error) <= track_width + soft_offtrack_tolerance_m
  and collision == false
  and min_clearance_margin > 0
```

Soft violations must be reported with severity:

```text
max_off_track_overshoot
time_to_first_off_track_s
soft_offtrack_step_count
soft_offtrack_duration_s
post_event_recovery_success
```

## Source Scenarios And Checkpoints

Primary measured-validation denominator:

```text
M2413 source-linked reset target set
350 reset targets x 15 selected checkpoints = 5250 executed episodes
```

Reason:

```text
M2413 is the most recent clean measured panel with source-linked target
metadata, explicit guardrails, and manageable scale.
```

Historical M2362 and M2397 should remain reference artifacts only for comparing
old metric diagnostics. They should not be merged into the primary fresh
measured-validation denominator.

Candidate/family/profile axes stay diagnostic-only:

```text
no candidate-family ranking
no controller-family ranking
no winner selection
```

## Required Env Support Before Rollout

Before measured validation can run, the environment needs a non-oracle config
addition that changes termination semantics without changing actor inputs:

```text
soft_offtrack_tolerance_m: float = 0.0
soft_offtrack_metric_enabled: bool = false
```

Expected behavior:

```text
soft_offtrack_metric_enabled == false:
  preserve current behavior exactly.

soft_offtrack_metric_enabled == true:
  crossing track_width records soft offtrack diagnostics but does not terminate
  until lateral error exceeds track_width + soft_offtrack_tolerance_m.
```

Required diagnostics:

```text
soft_offtrack_violation
soft_offtrack_step_count
soft_offtrack_duration_s
max_off_track_overshoot
hard_offtrack_failure
metric_selected_termination_reason
```

Actor observation must remain unchanged:

```text
road/free-space geometry in ego frame remains based on track_width;
no hidden metric flag enters actor input;
no path/TTC/reference/oracle fields enter actor input.
```

## Measured-Validation Output Contract

Future implementation artifacts should include:

```text
episode_rows.csv
metric_selected_summary.json
threshold_sensitivity_rows.csv
termination_reason_aggregate.csv
guardrail_rows.csv
decision_rows.csv
```

Required episode columns:

```text
raw_success
role_success
actual_success_metric_selected
raw_termination_reason
metric_selected_termination_reason
collision_or_obstacle_risk_failure
hard_offtrack_failure
soft_offtrack_violation
soft_offtrack_step_count
soft_offtrack_duration_s
max_off_track_overshoot
min_clearance_margin
guardrail_violation
```

## Admission Criteria For Measured Validation

Measured validation may start only after:

```text
soft-boundary env support has focused tests;
default config preserves old termination behavior;
soft-boundary config allows continuation inside tolerance;
actor observation shape and human-view contract remain unchanged;
reset/static validation confirms the M2413 target set still loads;
guardrail reporting is registered in a manifest.
```

## Decision

M2440 decision:

```text
metric_selected_validation_protocol_route_to_soft_boundary_env_support
```

Next milestone:

```text
m2441-paper-route-current-sim-dual-axis-soft-boundary-env-support-implementation
```

M2441 should implement and test the env-level soft-boundary support. It must not
run measured validation, repair, training, ranking, or verdict claims.

## Supported Claims

Supported:

```text
M2440 defines a metric-selected measured-validation protocol.

M2440 identifies env-level soft-boundary support as a prerequisite.

M2440 preserves actual success as an executed rollout outcome only.
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
