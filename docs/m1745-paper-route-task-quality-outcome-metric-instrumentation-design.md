# M1745 Paper-Route Task-Quality Outcome Metric Instrumentation Design

- status: completed
- decision: `metric_instrumentation_design_admit_logging_only_implementation`
- parent audit: `docs/m1744-paper-route-task-quality-outcome-semantics-materialization-preflight-result-audit.md`
- no rollout: true
- no implementation: true

## Summary

M1745 converts the seven explicit M1743 metric gaps into bounded metric
definitions and data routes. The route is logging-only: no reward, termination,
dynamics, actor input, profile, policy, checkpoint, or training behavior should
change.

Direct revised-semantics execution remains blocked until the logging fields are
implemented and smoke-tested. A supported-only bounded panel is kept as a
fallback, not the main route, because it would avoid the drift-required,
mitigation, boundary, and hidden-dynamics semantics needed for the paper route.

## Instrumentation Principles

- Metrics are computed from deploy/evaluation telemetry, not from actor inputs.
- Logging may include privileged diagnostic metadata already available to the
  evaluator, but it must not enter actor observations.
- Recovery metrics should use time-series evaluator rows, not terminal rows
  alone.
- Mitigation metrics should report severity, not convert unavoidable collision
  cases into ordinary success.
- Hidden-dynamics robustness is an aggregate over hidden-dynamics buckets, not
  a claim that the policy performs level3 self-identification.

## Metric Definitions

| metric | definition | data route | required fields |
| --- | --- | --- | --- |
| `recovery_success` | After obstacle pass or collision/termination candidate, the vehicle enters a stable corridor for `0.5 s` before episode end: no collision, no off-track termination, `abs(beta) <= 0.24`, `abs(yaw_rate) <= 1.5 rad/s`, `speed >= 2.0 m/s`, and `abs(lateral_error) <= 0.8 * track_width`. | evaluator time-series logging | per-step `beta`, `yaw_rate`, `speed`, `lateral_error`, `track_width`, `obstacle_passed_raw`, terminal flags |
| `recovery_time_proxy` | Seconds from first raw obstacle pass to first stable-corridor hold window. `NaN` if obstacle is never passed; capped at episode remaining time for failures. | evaluator time-series logging | first pass step/time, first recovery step/time, `dt`, stable-corridor mask |
| `controlled_drift_recovery_success` | For drift-required benchmark rows, obstacle is passed without collision/off-track/yaw-rate termination and the recovery-success condition is met. High sideslip is allowed, not required. Record `drift_used = max_abs_beta >= 0.35` as a diagnostic. | evaluator time-series logging | `obstacle_passed_raw`, `collision`, `termination_reason`, `max_abs_beta`, `max_abs_yaw_rate`, recovery fields |
| `collision_mitigation_score` | Diagnostic severity score for unavoidable-mitigation rows: lower is better, based on impact speed, negative clearance penetration proxy, and unstable-contact penalty. It is not ordinary success and not ranking-eligible until audited. | evaluator terminal/time-series logging | `collision`, terminal `speed`, terminal `beta`, terminal `yaw_rate`, `min_clearance_margin`, `impact_severity_proxy` |
| `impact_severity_proxy` | Collision-only proxy: terminal speed at first collision plus penalties for high sideslip/yaw at contact and obstacle penetration proxy `max(0, -min_clearance_margin)`. Non-collision rows record `NaN` plus a separate `collision=false` flag. | evaluator terminal logging plus env info `yaw_rate` | terminal `speed`, `beta`, `yaw_rate`, `min_clearance_margin`, `collision` |
| `off_track_severity_proxy` | Boundary-stress severity: maximum positive overshoot `max(abs(lateral_error) - track_width, 0)` and time to first off-track. Non-off-track rows record zero overshoot and `NaN` time-to-off-track. | evaluator time-series logging | per-step `lateral_error`, `track_width`, `termination_reason`, `dt` |
| `hidden_dynamics_robustness` | Aggregate diagnostic over hidden-dynamics buckets: report per-profile worst-bucket benchmark success, worst-bucket recovery success, worst-bucket collision/off-track rates, and max bucket spread. It is diagnostic until promotion gates include fresh hidden-dynamics holdouts. | aggregate over episode rows | scenario metadata `hidden_dynamics_bucket`, profile name, benchmark/diagnostic role, primary metric fields |

## Required Episode Columns

The next implementation should add these logging-only columns to episode rows:

```text
dt
track_width
first_obstacle_pass_step
first_obstacle_pass_time_s
first_recovery_step
first_recovery_time_s
recovery_success
recovery_time_proxy
max_abs_beta
max_abs_yaw_rate
drift_used
controlled_drift_recovery_success
impact_speed_proxy
impact_beta_abs
impact_yaw_rate_abs
impact_severity_proxy
max_off_track_overshoot
time_to_first_off_track_s
off_track_severity_proxy
```

The implementation may compute these fields inside `evaluate.run_episode_with_policy`
from already observed per-step `info` values. It should add `yaw_rate` and
`track_width` to env `info` as logging-only fields, because current episode rows
do not expose them directly.

## Required Aggregates

The next implementation should extend full-rollout aggregates with:

- scenario-family and evaluation-role aggregates for recovery success/time;
- controlled-drift recovery aggregates for drift-required benchmark rows;
- mitigation diagnostic aggregates for impact severity;
- boundary diagnostic aggregates for off-track severity;
- hidden-dynamics bucket aggregates and profile worst-bucket summaries.

These aggregates are still public diagnostic evidence. They are not private
holdout evidence, controller-family ranking, profile promotion, paper-level
evidence, or level3 self-identification evidence until later audited.

## Implementation Route

Admitted next route:

- M1746 logging-only outcome metric instrumentation implementation.

M1746 should:

- add logging-only `yaw_rate` and `track_width` to env `info`;
- add a small metric helper for stable-corridor/recovery/severity computation;
- extend `evaluate.run_episode_with_policy` episode rows with the required
  columns;
- extend full-rollout aggregate outputs with the required aggregate families;
- add focused tests for recovery, drift recovery, mitigation severity,
  off-track severity, and hidden-dynamics aggregate logic;
- avoid any rollout execution beyond unit/smoke tests.

## Claim Boundary

Supported:

- all seven M1743 metric gaps have definitions and data routes;
- the implementation scope is bounded and logging-only;
- direct revised-semantics execution remains blocked until implementation and
  smoke validation.

Unsupported:

- any rollout result under revised semantics;
- profile ranking or promotion;
- private-holdout result;
- paper-level benchmark evidence;
- level3 self-identification.

## Decision

Route to M1746 logging-only outcome metric instrumentation implementation.
