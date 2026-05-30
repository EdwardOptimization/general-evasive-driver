# M1705 Paper-Route Controller-Family Bounded Calibration Smoke Preflight

- status: completed
- result class: `controller_family_bounded_calibration_smoke_preflight_pass`
- artifact: `runs/m1705_controller_family_bounded_calibration_smoke_preflight/summary.json`
- parent design: `docs/m1704-paper-route-controller-family-bounded-calibration-smoke-design.md`

## Summary

M1705 materialized the no-rollout bounded calibration smoke subset.

This milestone did not execute rollout, train, replay, run PPO, promote, use
private holdout, change actor inputs, tune profiles, or claim controller-family
ranking, paper-level evidence, or level3 self-identification.

## Result

- source matrix cells: `10368`
- source calibration specs: `864`
- source base specs: `72`
- selected base specs: `6`
- rejected base specs: `66`
- selected task family counts: `T4=3`, `T5=3`
- bounded calibration specs: `72`
- bounded smoke matrix cells: `864`
- profiles: `12`
- contract violation count: `0`
- missing config count: `0`
- missing checkpoint count: `0`
- guardrail violation count: `0`
- environment rollout started: `false`

Selected base specs:

| base spec | task | source edge | window | executable source | template |
| --- | --- | --- | --- | --- | --- |
| `m1680-spec-0000` | `T4` | `actuator_delay_step|capability_step_up` | `reveal_plus_4` | `capability_step_up` | `t4_capability_step_temporal` |
| `m1680-spec-0001` | `T4` | `actuator_delay_step|t4_capability_step_temporal` | `mapping_window_unspecified` | `actuator_delay_step` | `t4_actuator_delay_response` |
| `m1680-spec-0006` | `T4` | `t4_staged_warmup_capability|capability_step_up` | `mapping_window_unspecified` | `t4_staged_warmup_capability` | `t4_staged_warmup_capability` |
| `m1680-spec-0036` | `T5` | `actuator_delay_step|t5_near_boundary_warmup` | `reveal_plus_4` | `t5_near_boundary_warmup` | `t5_near_boundary_warmup` |
| `m1680-spec-0039` | `T5` | `curved_boundary_obstacle|drive_loss_proxy` | `mapping_window_unspecified` | `curved_boundary_obstacle` | `t5_boundary_axis_retarget` |
| `m1680-spec-0040` | `T5` | `curved_boundary_obstacle|t5_boundary_axis_retarget` | `decision_minus_32` | `t5_boundary_axis_retarget` | `t5_boundary_axis_retarget` |

## Coverage

- track-width scale counts: `1.0=24`, `1.5=24`, `2.0=24`
- finish variant counts: `original=36`, `relaxed=36`
- max-steps scale counts: `1.0=36`, `1.5=36`
- variants per base spec: min `12`, max `12`
- profiles per calibration spec: min `12`, max `12`
- each profile appears in `72` rows

## Artifacts

```text
runs/m1705_controller_family_bounded_calibration_smoke_preflight/summary.json
runs/m1705_controller_family_bounded_calibration_smoke_preflight/selected_base_specs.csv
runs/m1705_controller_family_bounded_calibration_smoke_preflight/rejected_base_specs.csv
runs/m1705_controller_family_bounded_calibration_smoke_preflight/bounded_calibration_specs.json
runs/m1705_controller_family_bounded_calibration_smoke_preflight/bounded_calibration_specs.csv
runs/m1705_controller_family_bounded_calibration_smoke_preflight/bounded_smoke_matrix.csv
runs/m1705_controller_family_bounded_calibration_smoke_preflight/contract_violations.csv
```

## Verification

Commands run:

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q tests/test_controller_family_bounded_calibration_smoke_preflight.py
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.controller_family_bounded_calibration_smoke_preflight
```

Focused test result:

```text
2 passed
```

## Supported Claims

- The M1704 bounded subset can be materialized as clean no-rollout metadata.
- The subset preserves the planned `3` T4 / `3` T5 split, full calibration
  variants, and all twelve controller-family profiles.
- M1706 can audit whether the subset is ready for bounded execution design.

## Unsupported Claims

- controller-family ranking
- calibrated task-quality result
- finite-window history necessity
- recurrent advantage
- private-holdout evidence
- paper-level evidence
- level3 self-identification

## Decision

M1705 passes as no-rollout preflight. Route to M1706 result audit before any
bounded calibration smoke execution design.
