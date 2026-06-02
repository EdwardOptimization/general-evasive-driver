# M2327 Paper-Route Current-Sim R4 Mitigation Metric Instrumentation Implementation

- status: completed
- result_class: `r4_mitigation_metric_logging_export_implementation_pass`
- manifest: `experiments/manifests/m2327-paper-route-current-sim-r4-mitigation-metric-instrumentation-implementation.json`
- design doc: `docs/m2326-paper-route-current-sim-r4-mitigation-metric-instrumentation-design.md`
- code:
  - `src/autodrift/outcome_metric_instrumentation.py`
  - `src/autodrift/paper_route_current_sim_scenario_task_family_measured_execution.py`
  - `src/autodrift/paper_route_current_sim_scenario_task_family_feasibility_calibration.py`
- focused tests: `tests/test_paper_route_current_sim_r4_mitigation_metric_instrumentation.py`
- reset/rollout/policy action in M2327: `false`
- measured execution in M2327: `false`
- training/replay/PPO in M2327: `false`
- actor input changed: `false`
- reward/training objective changed: `false`
- collision termination behavior changed: `false`
- controller-family ranking claim made: `false`
- winner selected: `false`
- paper-level claim made: `false`
- finite-window vs GRU conclusion made: `false`
- level3 self-ID claim made: `false`

## Implementation

M2327 adds canonical R4 mitigation metric aliases and availability flags to the
existing logging-only outcome metric instrumentation:

```text
impact_speed_mps
impact_speed_mps_available
delta_v_at_impact_mps
delta_v_at_impact_mps_available
time_to_collision_s
time_to_collision_s_available
collision_angle_or_side
collision_angle_or_side_available
collision_side_proxy
post_event_speed_mps
post_event_speed_mps_available
post_event_yaw_rate_abs
post_event_yaw_rate_abs_available
post_event_offtrack_overshoot
post_event_offtrack_overshoot_available
recoverability_window_success
recoverability_window_success_available
```

Fields that current sim can support now:

```text
impact_speed_mps = impact_speed_proxy
time_to_collision_s = collision step time
collision_side_proxy = body-frame collision side proxy
```

Fields explicitly marked unavailable rather than fabricated:

```text
delta_v_at_impact_mps
collision_angle_or_side
post_event_speed_mps
post_event_yaw_rate_abs
post_event_offtrack_overshoot
recoverability_window_success
```

M2327 also updates the scenario task-family measured execution and support
feasibility calibration CSV fieldnames so existing outcome metrics and the new
aliases are not dropped by `append_csv_row(..., extrasaction="ignore")`.

## Verification

Focused command:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q \
  tests/test_paper_route_current_sim_r4_mitigation_metric_instrumentation.py \
  tests/test_paper_route_current_sim_scenario_task_family_measured_execution.py \
  tests/test_paper_route_current_sim_scenario_task_family_feasibility_calibration.py
```

Result:

```text
9 passed
```

The tests use stub rollout metrics and do not run real env rollouts.

## Claim Boundary

Allowed claim:

```text
M2327 implements logging/export support for R4 mitigation metric aliases and
availability flags.
```

Blocked claims:

```text
mitigation performance measured;
post-collision recovery measured;
R4 mitigation solved;
support-policy/controller ranking;
paper-level evidence;
finite-window vs GRU conclusion;
level3 self-identification evidence.
```

## Follow-Up

Pre-register result audit:

```text
experiments/manifests/m2328-paper-route-current-sim-r4-mitigation-metric-instrumentation-result-audit.json
```
