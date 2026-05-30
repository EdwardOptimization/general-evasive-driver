# M1746 Paper-Route Task-Quality Outcome Metric Instrumentation Implementation

- status: completed
- result class: `outcome_metric_instrumentation_implementation_pass`
- parent design: `docs/m1745-paper-route-task-quality-outcome-metric-instrumentation-design.md`
- no full rollout: true
- training/replay/PPO: false

## Summary

M1746 implements the M1745 logging-only outcome metric instrumentation. The
implementation adds metric helpers, evaluator episode-row fields, and aggregate
fields for recovery, controlled drift recovery, mitigation severity, off-track
severity, and hidden-dynamics robustness.

The change is logging-only. It does not change actor observations, reward,
dynamics, termination behavior, policy checkpoints, profile masks, training, or
promotion logic.

## Implementation

Code changes:

- `src/autodrift/outcome_metric_instrumentation.py`
  - defines recovery, controlled-drift recovery, impact severity, off-track
    severity, and hidden-dynamics aggregate helpers;
- `src/autodrift/env.py`
  - adds logging-only `yaw_rate`, `dt`, and `track_width` to `info`;
- `src/autodrift/evaluate.py`
  - computes episode-row outcome metric fields from per-step `info`;
- `src/autodrift/controller_family_full_rollout_execution.py`
  - adds metric aggregate fields and hidden-dynamics robustness artifacts;
- `src/autodrift/controller_family_bounded_calibration_smoke_execution.py`
  - adds metric aggregate fields to outcome aggregates;
- `src/autodrift/task_quality_scenario_taxonomy_execution.py`
  - writes profile hidden-dynamics worst-bucket aggregate rows.

New episode-row fields:

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
collision_mitigation_score
max_off_track_overshoot
time_to_first_off_track_s
off_track_severity_proxy
```

## Verification

Focused tests:

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest \
  tests/test_outcome_metric_instrumentation.py \
  tests/test_evaluate.py \
  tests/test_controller_family_full_rollout_execution.py -q
```

Result: `22 passed`.

Additional affected aggregate tests:

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest \
  tests/test_controller_family_bounded_calibration_smoke_execution.py \
  tests/test_controller_family_off_track_repair_panel_execution.py \
  tests/test_controller_family_calibrated_scale_up_execution.py \
  tests/test_task_quality_scenario_taxonomy_execution.py -q
```

Result: `11 passed`.

## Claim Boundary

Supported:

- all M1745 metric families have logging-only implementation hooks;
- focused tests cover recovery, controlled drift recovery, mitigation severity,
  off-track severity, and hidden-dynamics aggregate logic;
- the actor input contract remains unchanged.

Unsupported:

- revised-semantics rollout result;
- controller-family ranking;
- profile promotion;
- private-holdout evidence;
- paper-level benchmark result;
- level3 self-identification.

## Decision

Route to M1747 instrumentation implementation result audit before any revised
scenario execution design or rollout.
