# M1703 Paper-Route Controller-Family Task-Quality Calibration Preflight Result Audit

- status: completed
- decision: `calibration_preflight_audit_admit_bounded_smoke_design`
- audited artifact: `runs/m1702_controller_family_task_quality_calibration_preflight/summary.json`
- audited matrix: `runs/m1702_controller_family_task_quality_calibration_preflight/calibration_matrix.csv`
- audited contract checks: `runs/m1702_controller_family_task_quality_calibration_preflight/contract_violations.csv`

## Audit Result

M1702 is a clean no-rollout task-quality calibration preflight.

- result class: `controller_family_task_quality_calibration_preflight_pass`
- base executable specs: `72`
- calibration specs: `864`
- controller-family profiles: `12`
- calibration matrix cells: `10368`
- contract violation count: `0`
- missing profile artifact count: `0`
- guardrail violation count: `0`
- environment rollout started: `false`

## Coverage Checks

The calibration axes are balanced over the generated spec metadata:

| axis | values | counts |
| --- | --- | --- |
| `track_width_scale` | `1.0`, `1.5`, `2.0` | `288` each |
| `finish_variant` | `original`, `relaxed` | `432` each |
| `max_steps_scale` | `1.0`, `1.5` | `432` each |

Every profile appears in `864` matrix rows, and all profile config/checkpoint
paths exist. The matrix schedules no rollout, no training, and no
profile-specific tuning.

## Interpretation

The M1702 matrix is valid as metadata, but it is too large to execute as the
next step. A direct `10368`-cell rollout would mix calibration-axis exploration
with controller-family ranking and would be expensive before we know which
variants reduce the off-track-dominated outcome found in M1698/M1699.

The correct next step is a bounded public calibration smoke design that samples
the matrix across:

```text
track-width scale;
finish variant;
max-step scale;
task family;
source family;
controller controls.
```

The smoke must remain diagnostic-only. It should estimate whether any
calibration setting makes outcome buckets interpretable enough for later
controller-family comparison.

## Supported Claims

- The no-rollout calibration matrix is complete and P0 contract-clean.
- The matrix preserves all twelve controller-family profiles as later controls.
- A bounded calibration smoke design is admitted before any measured execution.

## Unsupported Claims

- controller-family ranking
- calibrated task-quality result
- finite-window history necessity
- recurrent advantage
- private-holdout evidence
- paper-level evidence
- level3 self-identification

## Decision

M1703 passes as a process audit. Route to M1704 bounded calibration smoke design.
Do not run the full matrix, train, replay, run PPO, promote, use private holdout,
change actor inputs, tune profiles, or claim controller-family ranking.
