# M1718 Paper-Route Controller-Family Off-Track Dominance Localization

- status: completed
- result class: `off_track_dominance_localization_pass`
- artifact: `runs/m1718_off_track_dominance_localization/summary.json`
- parent synthesis: `docs/m1717-paper-route-controller-family-task-quality-scale-up-synthesis.md`

## Summary

M1718 materialized no-rollout localization aggregates from the existing M1715
episode rows.

This milestone did not execute rollout, train, replay, run PPO, promote, use
private holdout, change actor inputs, tune profiles, rank controller families,
or claim paper-level evidence or level3 self-identification.

## Localization Result

- episode rows audited: `864`
- all selected metrics finite: `true`
- guardrail violation count: `0`
- variant-source aggregate rows: `60`
- variant-task-family aggregate rows: `8`
- variant-profile aggregate rows: `48`
- source-task-family aggregate rows: `15`
- profile-outcome aggregate rows: `23`
- repair target slices: `48`

Repair target threshold:

```text
episode_count >= 12
off_track_noncollision_noncompletion_rate >= 0.80
collision_failure_rate <= 0.10
```

## Repair Target Distribution

Repair target slice counts:

| slice type | count |
| --- | ---: |
| `variant_source_edge` | `34` |
| `source_task_family` | `10` |
| `variant_task_family` | `4` |

Variant-task-family targets:

| slice | episodes | off-track | collision |
| --- | ---: | ---: | ---: |
| `original_axis_baseline::T4` | `108` | `0.9537` | `0.0093` |
| `original_axis_baseline::T5` | `108` | `0.9074` | `0.0648` |
| `mid_calibration_variant::T4` | `108` | `0.8981` | `0.0370` |
| `best_off_track_variant::T4` | `108` | `0.8241` | `0.0463` |

Top source-task-family targets:

| slice | episodes | off-track | collision |
| --- | ---: | ---: | ---: |
| `t4_staged_warmup_capability|capability_step_up::T4` | `48` | `0.9167` | `0.0208` |
| `actuator_delay_step|capability_step_up::T4` | `96` | `0.8958` | `0.0208` |
| `t4_capability_step_temporal|capability_step_down::T4` | `48` | `0.8750` | `0.0417` |
| `actuator_delay_step|t4_capability_step_temporal::T4` | `96` | `0.8646` | `0.0417` |
| `t4_actuator_delay_response|actuator_delay_step::T4` | `48` | `0.8542` | `0.0625` |

The top individual target is:

```text
slice_type: variant_source_edge
slice_id: mid_calibration_variant::capability_step_down|t5_near_boundary_warmup
episode_count: 12
off_track_noncollision_noncompletion_rate: 1.0000
collision_failure_rate: 0.0000
```

## Interpretation Boundary

The localization is not a profile ranking. `variant_profile_aggregate.csv` is
kept as a control surface to see whether off-track dominance is a profile
artifact, but repair target selection intentionally uses non-profile slices:

```text
variant_source_edge
variant_task_family
source_task_family
```

Supported:

- M1715 off-track dominance is localizable enough to support a repair audit.
- T4 slices are visibly overrepresented among variant-task and source-task
  repair targets.
- T5 remains present in repair targets, so the problem is not T4-only.

Unsupported:

- controller-family ranking
- final task repair design
- recurrent advantage
- finite-window history necessity
- private-holdout evidence
- paper-level evidence
- level3 self-identification

## Artifacts

```text
runs/m1718_off_track_dominance_localization/summary.json
runs/m1718_off_track_dominance_localization/variant_source_edge_aggregate.csv
runs/m1718_off_track_dominance_localization/variant_task_family_aggregate.csv
runs/m1718_off_track_dominance_localization/variant_profile_aggregate.csv
runs/m1718_off_track_dominance_localization/source_task_family_aggregate.csv
runs/m1718_off_track_dominance_localization/profile_outcome_aggregate.csv
runs/m1718_off_track_dominance_localization/repair_target_slices.csv
```

## Verification

Commands run:

```text
python -m compileall -q src tests
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q tests/test_controller_family_off_track_dominance_localization.py tests/test_controller_family_calibrated_scale_up_execution.py
PYTHONPATH=src python -m autodrift.controller_family_off_track_dominance_localization
```

Focused test result:

```text
4 passed
```

## Decision

M1718 passes as a no-rollout localization milestone. Route to M1719 result audit
before designing a repaired task-quality panel.
