# M1712 Paper-Route Controller-Family Calibrated Scale-Up Preflight

- status: completed
- result class: `controller_family_calibrated_scale_up_preflight_pass`
- artifact: `runs/m1712_controller_family_calibrated_scale_up_preflight/summary.json`
- parent design: `docs/m1711-paper-route-controller-family-calibrated-scale-up-design.md`

## Summary

M1712 materialized the no-rollout source-expanded calibrated scale-up subset.

This milestone did not execute rollout, train, replay, run PPO, promote, use
private holdout, change actor inputs, tune profiles, or claim controller-family
ranking, paper-level evidence, or level3 self-identification.

## Result

- source matrix cells: `10368`
- source calibration specs: `864`
- source base specs: `72`
- anchor base specs: `6`
- selected base specs: `18`
- rejected base specs: `54`
- selected task family counts: `T4=9`, `T5=9`
- scale-up calibration specs: `72`
- scale-up matrix cells: `864`
- profiles: `12`
- contract violation count: `0`
- missing config / checkpoint count: `0` / `0`
- guardrail violation count: `0`
- environment rollout started: `false`

## Variant Coverage

Each selected base spec keeps exactly four variants:

| variant label | spec count |
| --- | ---: |
| `original_axis_baseline` | `18` |
| `best_off_track_variant` | `18` |
| `collision_control_wide_relaxed` | `18` |
| `mid_calibration_variant` | `18` |

Coverage checks:

- variants per base spec: min `4`, max `4`
- profiles per calibration spec: min `12`, max `12`
- each profile appears in `72` matrix rows

## Selected Base Specs

The first six are M1705 anchors, followed by source-diverse additions:

```text
m1680-spec-0000
m1680-spec-0001
m1680-spec-0006
m1680-spec-0036
m1680-spec-0039
m1680-spec-0040
m1680-spec-0002
m1680-spec-0003
m1680-spec-0005
m1680-spec-0004
m1680-spec-0007
m1680-spec-0008
m1680-spec-0037
m1680-spec-0041
m1680-spec-0038
m1680-spec-0042
m1680-spec-0043
m1680-spec-0044
```

## Artifacts

```text
runs/m1712_controller_family_calibrated_scale_up_preflight/summary.json
runs/m1712_controller_family_calibrated_scale_up_preflight/selected_base_specs.csv
runs/m1712_controller_family_calibrated_scale_up_preflight/rejected_base_specs.csv
runs/m1712_controller_family_calibrated_scale_up_preflight/scale_up_calibration_specs.json
runs/m1712_controller_family_calibrated_scale_up_preflight/scale_up_calibration_specs.csv
runs/m1712_controller_family_calibrated_scale_up_preflight/scale_up_matrix.csv
runs/m1712_controller_family_calibrated_scale_up_preflight/contract_violations.csv
```

## Verification

Commands run:

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q tests/test_controller_family_calibrated_scale_up_preflight.py
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.controller_family_calibrated_scale_up_preflight
```

Focused test result:

```text
3 passed
```

## Supported Claims

- The source-expanded scale-up subset can be materialized within the fixed
  `864`-cell budget.
- The subset preserves baseline, best off-track, collision-control, and mid
  calibration variants.
- The subset preserves all twelve controller-family controls.

## Unsupported Claims

- controller-family ranking
- scale-up task-quality result
- finite-window history necessity
- recurrent advantage
- private-holdout evidence
- paper-level evidence
- level3 self-identification

## Decision

M1712 passes as no-rollout preflight. Route to M1713 result audit before any
scale-up execution design.
