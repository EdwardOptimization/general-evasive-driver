# M1713 Paper-Route Controller-Family Calibrated Scale-Up Preflight Result Audit

- status: completed
- decision: `calibrated_scale_up_preflight_audit_admit_execution_design`
- audited artifact: `runs/m1712_controller_family_calibrated_scale_up_preflight/summary.json`
- audited matrix: `runs/m1712_controller_family_calibrated_scale_up_preflight/scale_up_matrix.csv`

## Audit Result

M1712 is a clean no-rollout source-expanded calibrated scale-up preflight.

- result class: `controller_family_calibrated_scale_up_preflight_pass`
- selected base specs: `18`
- selected task family counts: `T4=9`, `T5=9`
- scale-up calibration specs: `72`
- scale-up matrix cells: `864`
- profiles: `12`
- contract violation count: `0`
- missing config / checkpoint count: `0` / `0`
- guardrail violation count: `0`
- environment rollout started: `false`

## Coverage Interpretation

The subset preserves the intended fixed-budget scale-up shape:

| check | result |
| --- | --- |
| selected base specs | `18` |
| task-family split | `T4=9`, `T5=9` |
| variants per base spec | min `4`, max `4` |
| profiles per calibration spec | min `12`, max `12` |
| `original_axis_baseline` specs | `18` |
| `best_off_track_variant` specs | `18` |
| `collision_control_wide_relaxed` specs | `18` |
| `mid_calibration_variant` specs | `18` |

The preflight expands source coverage from the M1705 six-base-spec smoke while
keeping the same `864`-episode execution budget.

## Required Next Route

The next milestone should be execution design, not direct execution.

M1714 should specify:

```text
runner input: M1712 scale_up_matrix.csv
calibration spec input: M1712 scale_up_calibration_specs.json
episode count: 864
required scale-up variant aggregates
required outcome and termination aggregates
collision/off-track tradeoff audit thresholds
resume/failure behavior
claim boundary: task-quality scale-up only
```

Execution should happen only after M1714 commits the protocol.

## Supported Claims

- The source-expanded scale-up subset is complete and P0 contract-clean.
- The fixed-budget source expansion preserves all planned variants and all
  controller-family controls.
- Calibrated scale-up execution design is admitted.

## Unsupported Claims

- controller-family ranking
- calibrated scale-up result
- finite-window history necessity
- recurrent advantage
- private-holdout evidence
- paper-level evidence
- level3 self-identification

## Decision

M1713 passes as a process audit. Route to M1714 calibrated scale-up execution
design. Keep rollout execution, training, replay, PPO, promotion, private
holdout, actor-input changes, profile-specific tuning, and controller-family
ranking blocked until explicitly admitted.
