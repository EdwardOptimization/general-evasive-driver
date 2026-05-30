# M1728 Paper-Route Task-Quality Scenario Taxonomy Preflight

- status: completed
- result class: `task_quality_scenario_taxonomy_preflight_pass`
- artifact: `runs/m1728_task_quality_scenario_taxonomy_preflight/summary.json`
- parent design: `docs/m1727-paper-route-task-quality-scenario-taxonomy-design.md`

## Summary

M1728 materialized the M1727 scenario taxonomy as no-rollout metadata.

This milestone did not execute rollout, train, replay, run PPO, promote, use
private holdout, change actor inputs, tune profiles, rank controller families,
or claim paper-level evidence or level3 self-identification.

## Preflight Result

- scenario families: `6`
- scenario specs: `72`
- scenario specs per family: `12`
- profiles: `12`
- scenario matrix cells: `864`
- missing config count: `0`
- missing checkpoint count: `0`
- contract violation count: `0`
- unsupported scenario feature count: `5`
- silent unsupported approximation count: `0`
- guardrail violation count: `0`
- passes public preflight gates: `true`

Scenario specs per family:

| scenario family | specs |
| --- | ---: |
| `ordinary_stable_avoidance` | `12` |
| `aeb_infeasible_stable_aes` | `12` |
| `drift_required_avoidance` | `12` |
| `unavoidable_mitigation` | `12` |
| `off_track_boundary_stress` | `12` |
| `hidden_dynamics_stress` | `12` |

Hidden dynamics buckets:

| bucket | specs |
| --- | ---: |
| `nominal` | `12` |
| `friction_step` | `16` |
| `low_mu` | `8` |
| `tire_stiffness` | `8` |
| `brake_variation` | `8` |
| `actuator_delay` | `8` |
| `mild_randomization` | `4` |
| `brake_drive_variation` | `4` |
| `mass_cg_shift` | `4` |

## Unsupported Feature Reporting

M1728 explicitly records these fault-like scenarios as unsupported by the
current single-track model:

```text
single_wheel_blowout_or_puncture
wheel_specific_grip_loss
half_shaft_or_single_side_drive_torque_loss
brake_side_imbalance
steering_deadzone_or_partial_actuator_fault
```

All rows have:

```text
silently_approximated: false
covered_by_current_preflight: false
```

This means the taxonomy records those future/extreme scenarios without
pretending the current simulator covers them.

## Artifacts

```text
runs/m1728_task_quality_scenario_taxonomy_preflight/summary.json
runs/m1728_task_quality_scenario_taxonomy_preflight/scenario_taxonomy.json
runs/m1728_task_quality_scenario_taxonomy_preflight/scenario_specs.json
runs/m1728_task_quality_scenario_taxonomy_preflight/scenario_specs.csv
runs/m1728_task_quality_scenario_taxonomy_preflight/scenario_matrix.csv
runs/m1728_task_quality_scenario_taxonomy_preflight/profile_artifacts.csv
runs/m1728_task_quality_scenario_taxonomy_preflight/contract_violations.csv
runs/m1728_task_quality_scenario_taxonomy_preflight/unsupported_scenario_features.csv
```

## Verification

Commands run:

```text
python -m compileall -q src tests
PYTHONPATH=src OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 python -m pytest -q tests/test_task_quality_scenario_taxonomy_preflight.py
PYTHONPATH=src python -m autodrift.task_quality_scenario_taxonomy_preflight
```

Focused test result:

```text
4 passed
```

Preflight command result:

```text
result_class=task_quality_scenario_taxonomy_preflight_pass
scenario_family_count=6
scenario_spec_count=72
scenario_matrix_cell_count=864
contract_violation_count=0
```

## Supported Claims

- The M1727 scenario taxonomy can be materialized as no-rollout metadata.
- The taxonomy has balanced public family coverage: `6 x 12` specs.
- The scenario matrix preserves all `12` controller-family profiles.
- Current unsupported fault-like features are explicitly recorded rather than
  silently approximated.

## Unsupported Claims

- scenario execution result
- controller-family ranking
- recurrent advantage
- finite-window history necessity
- private-holdout evidence
- paper-level evidence
- level3 self-identification

## Decision

M1728 passes as no-rollout preflight. Route to M1729 result audit before any
scenario taxonomy execution design or controller-family comparison.
