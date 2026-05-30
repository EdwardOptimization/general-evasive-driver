# M1715 Paper-Route Controller-Family Calibrated Scale-Up Execution

- status: completed
- result class: `controller_family_calibrated_scale_up_execution_pass`
- artifact: `runs/m1715_controller_family_calibrated_scale_up_execution/summary.json`
- parent design: `docs/m1714-paper-route-controller-family-calibrated-scale-up-execution-design.md`

## Summary

M1715 executed the source-expanded calibrated scale-up over the M1712 subset.

This milestone ran environment rollouts, but did not train, replay, run PPO,
promote, use private holdout, change actor inputs, tune profiles, or claim
controller-family ranking, paper-level evidence, or level3 self-identification.

## Execution Result

- episode count: `864`
- target episode count: `864`
- selected base specs: `18`
- scale-up calibration specs: `72`
- profiles: `12`
- scale-up variants: `4`
- failure count: `0`
- all selected metrics finite: `true`
- guardrail violation count: `0`
- outcome aggregate rows: `3`
- termination reason aggregate rows: `3`
- profile outcome aggregate rows: `23`
- scale-up variant aggregate rows: `4`

Overall outcome buckets:

| outcome bucket | count | share |
| --- | ---: | ---: |
| `success_obstacle_pass` | `98` | `0.1134` |
| `collision_failure` | `45` | `0.0521` |
| `off_track_noncollision_noncompletion` | `721` | `0.8345` |

Termination reasons:

| termination reason | count |
| --- | ---: |
| empty / success | `98` |
| `obstacle_collision` | `45` |
| `off_track` | `721` |

## Scale-Up Variant Data

Raw M1715 scale-up variant rates:

| variant | episodes | success | collision | off-track noncollision noncompletion |
| --- | ---: | ---: | ---: | ---: |
| `original_axis_baseline` | `216` | `0.0324` | `0.0370` | `0.9306` |
| `best_off_track_variant` | `216` | `0.1620` | `0.0370` | `0.8009` |
| `collision_control_wide_relaxed` | `216` | `0.1574` | `0.0833` | `0.7593` |
| `mid_calibration_variant` | `216` | `0.1019` | `0.0509` | `0.8472` |

This raw observation is reserved for M1716 audit under the pre-registered M1714
task-quality rules. M1715 itself only claims clean execution and artifact
availability.

## Artifacts

```text
runs/m1715_controller_family_calibrated_scale_up_execution/summary.json
runs/m1715_controller_family_calibrated_scale_up_execution/episode_rows.csv
runs/m1715_controller_family_calibrated_scale_up_execution/failure_rows.csv
runs/m1715_controller_family_calibrated_scale_up_execution/run_state.json
runs/m1715_controller_family_calibrated_scale_up_execution/profile_aggregate.csv
runs/m1715_controller_family_calibrated_scale_up_execution/scale_up_variant_aggregate.csv
runs/m1715_controller_family_calibrated_scale_up_execution/task_family_aggregate.csv
runs/m1715_controller_family_calibrated_scale_up_execution/source_edge_aggregate.csv
runs/m1715_controller_family_calibrated_scale_up_execution/outcome_aggregate.csv
runs/m1715_controller_family_calibrated_scale_up_execution/termination_reason_aggregate.csv
runs/m1715_controller_family_calibrated_scale_up_execution/profile_outcome_aggregate.csv
```

## Verification

Commands run:

```text
python -m compileall -q src tests
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q tests/test_controller_family_calibrated_scale_up_execution.py tests/test_controller_family_bounded_calibration_smoke_execution.py
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.controller_family_calibrated_scale_up_execution --device cpu --no-resume
```

Focused test result:

```text
4 passed
```

## Supported Claims

- The calibrated scale-up execution path works and is resumable.
- The M1712 `864`-cell scale-up matrix executed with zero runner failures.
- Scale-up variant, outcome, and termination aggregates are available for M1716
  task-quality audit.

## Unsupported Claims

- controller-family ranking
- calibrated task-quality conclusion before M1716 audit
- finite-window history necessity
- recurrent advantage
- private-holdout evidence
- paper-level evidence
- level3 self-identification

## Decision

M1715 passes as measured public diagnostic execution. Route to M1716 result
audit before interpreting calibration quality or deciding whether to scale,
repair, or synthesize the branch.
