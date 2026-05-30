# M1724 Paper-Route Controller-Family Off-Track Repair Panel Execution

- status: completed
- result class: `controller_family_off_track_repair_panel_execution_pass`
- artifact: `runs/m1724_off_track_repair_panel_execution/summary.json`
- parent design: `docs/m1723-paper-route-controller-family-off-track-repair-panel-execution-design.md`

## Summary

M1724 executed the fixed M1721 off-track repair panel matrix.

This milestone ran environment rollouts, but did not train, replay, run PPO,
promote, use private holdout, change actor inputs, tune profiles, rank
controller families, or claim paper-level evidence or level3 self-identification.

## Execution Result

- episode count: `864`
- target episode count: `864`
- selected base specs: `18`
- repair panel specs: `72`
- profiles: `12`
- repair variants: `4`
- failure count: `0`
- all selected metrics finite: `true`
- guardrail violation count: `0`
- outcome aggregate rows: `4`
- termination reason aggregate rows: `4`
- profile outcome aggregate rows: `26`
- repair variant aggregate rows: `4`

Overall outcome buckets:

| outcome bucket | count | share |
| --- | ---: | ---: |
| `success_obstacle_pass` | `114` | `0.1319` |
| `collision_failure` | `61` | `0.0706` |
| `off_track_noncollision_noncompletion` | `688` | `0.7963` |
| `speed_too_low_noncollision_noncompletion` | `1` | `0.0012` |

Termination reasons:

| termination reason | count |
| --- | ---: |
| empty / success | `114` |
| `obstacle_collision` | `61` |
| `off_track` | `688` |
| `speed_too_low` | `1` |

## Repair Variant Data

Raw M1724 repair variant rates:

| variant | episodes | success | collision | off-track noncollision noncompletion |
| --- | ---: | ---: | ---: | ---: |
| `original_axis_baseline` | `216` | `0.0324` | `0.0324` | `0.9352` |
| `best_off_track_variant` | `216` | `0.1574` | `0.1019` | `0.7361` |
| `collision_control_wide_relaxed` | `216` | `0.1528` | `0.0648` | `0.7824` |
| `wide_relaxed_extended` | `216` | `0.1852` | `0.0833` | `0.7315` |

This raw observation is reserved for M1725 audit under the pre-registered M1723
task-quality repair rules. M1724 itself only claims clean execution and artifact
availability.

## Artifacts

```text
runs/m1724_off_track_repair_panel_execution/summary.json
runs/m1724_off_track_repair_panel_execution/episode_rows.csv
runs/m1724_off_track_repair_panel_execution/failure_rows.csv
runs/m1724_off_track_repair_panel_execution/run_state.json
runs/m1724_off_track_repair_panel_execution/profile_aggregate.csv
runs/m1724_off_track_repair_panel_execution/repair_variant_aggregate.csv
runs/m1724_off_track_repair_panel_execution/task_family_aggregate.csv
runs/m1724_off_track_repair_panel_execution/source_edge_aggregate.csv
runs/m1724_off_track_repair_panel_execution/outcome_aggregate.csv
runs/m1724_off_track_repair_panel_execution/termination_reason_aggregate.csv
runs/m1724_off_track_repair_panel_execution/profile_outcome_aggregate.csv
```

## Verification

Commands run:

```text
python -m compileall -q src tests
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q tests/test_controller_family_off_track_repair_panel_execution.py tests/test_controller_family_calibrated_scale_up_execution.py
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.controller_family_off_track_repair_panel_execution --no-resume --device cpu
```

Focused test result:

```text
4 passed
```

Execution command result:

```text
result_class=controller_family_off_track_repair_panel_execution_pass
episode_count=864
failure_count=0
guardrail_violation_count=0
```

## Supported Claims

- The off-track repair panel execution path works and is resumable.
- The M1721 `864`-cell repair panel matrix executed with zero runner failures.
- Repair variant, outcome, and termination aggregates are available for M1725
  task-quality audit.

## Unsupported Claims

- controller-family ranking
- repair success conclusion before M1725 audit
- finite-window history necessity
- recurrent advantage
- private-holdout evidence
- paper-level evidence
- level3 self-identification

## Decision

M1724 passes as measured public diagnostic execution. Route to M1725 result
audit before interpreting repair quality or deciding whether to redesign,
synthesize, or continue the paper-route task-quality branch.
