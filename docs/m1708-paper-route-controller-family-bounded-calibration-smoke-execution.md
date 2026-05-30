# M1708 Paper-Route Controller-Family Bounded Calibration Smoke Execution

- status: completed
- result class: `controller_family_bounded_calibration_smoke_execution_pass`
- artifact: `runs/m1708_controller_family_bounded_calibration_smoke_execution/summary.json`
- parent design: `docs/m1707-paper-route-controller-family-bounded-calibration-smoke-execution-design.md`

## Summary

M1708 executed the bounded public calibration smoke over the M1705 subset.

This milestone ran environment rollouts, but did not train, replay, run PPO,
promote, use private holdout, change actor inputs, tune profiles, or claim
controller-family ranking, paper-level evidence, or level3 self-identification.

## Execution Result

- episode count: `864`
- target episode count: `864`
- selected base specs: `6`
- calibration specs: `72`
- profiles: `12`
- failure count: `0`
- all selected metrics finite: `true`
- guardrail violation count: `0`
- outcome aggregate rows: `3`
- termination reason aggregate rows: `3`
- profile outcome aggregate rows: `24`
- calibration variant aggregate rows: `12`

Overall outcome buckets:

| outcome bucket | count | share |
| --- | ---: | ---: |
| `success_obstacle_pass` | `91` | `0.1053` |
| `collision_failure` | `57` | `0.0660` |
| `off_track_noncollision_noncompletion` | `716` | `0.8287` |

Termination reasons:

| termination reason | count |
| --- | ---: |
| empty / success | `91` |
| `obstacle_collision` | `57` |
| `off_track` | `716` |

## Calibration Variant Data

The pre-registered original-axis baseline variant:

```text
track_width_scale=1.0
finish_variant=original
max_steps_scale=1.0
off_track_noncollision_noncompletion_rate=0.9028
success_obstacle_pass_rate=0.0417
collision_failure_rate=0.0556
```

The best off-track variant in the raw execution data:

```text
track_width_scale=2.0
finish_variant=original
max_steps_scale=1.5
off_track_noncollision_noncompletion_rate=0.6944
success_obstacle_pass_rate=0.2083
collision_failure_rate=0.0972
```

This raw observation is reserved for M1709 audit under the pre-registered
M1707 task-quality rules. M1708 itself only claims clean execution and artifact
availability.

## Artifacts

```text
runs/m1708_controller_family_bounded_calibration_smoke_execution/summary.json
runs/m1708_controller_family_bounded_calibration_smoke_execution/episode_rows.csv
runs/m1708_controller_family_bounded_calibration_smoke_execution/failure_rows.csv
runs/m1708_controller_family_bounded_calibration_smoke_execution/run_state.json
runs/m1708_controller_family_bounded_calibration_smoke_execution/profile_aggregate.csv
runs/m1708_controller_family_bounded_calibration_smoke_execution/calibration_variant_aggregate.csv
runs/m1708_controller_family_bounded_calibration_smoke_execution/task_family_aggregate.csv
runs/m1708_controller_family_bounded_calibration_smoke_execution/source_edge_aggregate.csv
runs/m1708_controller_family_bounded_calibration_smoke_execution/outcome_aggregate.csv
runs/m1708_controller_family_bounded_calibration_smoke_execution/termination_reason_aggregate.csv
runs/m1708_controller_family_bounded_calibration_smoke_execution/profile_outcome_aggregate.csv
```

## Verification

Commands run:

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q tests/test_controller_family_bounded_calibration_smoke_execution.py
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.controller_family_bounded_calibration_smoke_execution
```

Focused test result:

```text
2 passed
```

## Supported Claims

- The bounded calibration smoke execution path works and is resumable.
- The M1705 `864`-cell bounded matrix executed with zero runner failures.
- Outcome and termination aggregates are available for M1709 task-quality audit.

## Unsupported Claims

- controller-family ranking
- calibrated task-quality conclusion before M1709 audit
- finite-window history necessity
- recurrent advantage
- private-holdout evidence
- paper-level evidence
- level3 self-identification

## Decision

M1708 passes as measured public diagnostic execution. Route to M1709 result
audit before interpreting calibration quality or deciding whether to scale,
repair, or synthesize the branch.
