# M1734 Paper-Route Task-Quality Scenario Taxonomy Sampling Repair Preflight

- status: completed
- result class: `task_quality_scenario_taxonomy_sampling_repair_preflight_pass`
- artifact: `runs/m1734_task_quality_scenario_taxonomy_sampling_repair_preflight/summary.json`
- parent design: `docs/m1733-paper-route-task-quality-scenario-taxonomy-sampling-repair-design.md`

## Summary

M1734 materialized a repaired scenario taxonomy and ran reset-only sampling
feasibility checks over the full planned `72 x 12 = 864` matrix. The repair
does not mutate M1728 artifacts in place. It writes new repaired specs, repair
deltas, reset-stress rows, label distributions, and unsupported-feature
artifacts under the M1734 run directory.

This milestone only reset environments. It did not run policy rollout, train,
replay, run PPO, promote, use private holdout, change actor inputs, tune
profiles, rank controller families, treat unsupported faults as covered, or
claim paper-level evidence or level3 self-identification.

## Preflight Result

- repaired scenario specs: `72 / 72`
- repaired matrix cells: `864 / 864`
- profiles: `12 / 12`
- reset-stress rows: `864 / 864`
- reset successes: `864`
- sampling failures: `0`
- contract violations: `0`
- repair delta rows: `264`
- label-distribution-by-family rows: `9`
- unsupported scenario features: `5`
- silent unsupported approximations: `0`
- guardrail violation count: `0`

Repair variants:

| variant | specs |
| --- | ---: |
| `no_sampling_repair_needed` | `24` |
| `stable_aes_sampling_window_v1` | `12` |
| `drift_required_sampling_window_v1` | `12` |
| `boundary_stress_sampling_window_v1` | `12` |
| `hidden_dynamics_sampling_window_v1` | `12` |

## Label Distribution

Reset-only sampled labels by scenario family:

| scenario family | sampled label | reset count |
| --- | --- | ---: |
| `ordinary_stable_avoidance` | `aeb_feasible` | `144` |
| `aeb_infeasible_stable_aes` | `aes_feasible` | `144` |
| `drift_required_avoidance` | `drift_required` | `144` |
| `unavoidable_mitigation` | `unavoidable` | `144` |
| `off_track_boundary_stress` | `aes_feasible` | `43` |
| `off_track_boundary_stress` | `drift_required` | `101` |
| `hidden_dynamics_stress` | `aes_feasible` | `29` |
| `hidden_dynamics_stress` | `drift_required` | `71` |
| `hidden_dynamics_stress` | `unavoidable` | `44` |

This directly repairs the M1731 reset-time failure mode: every planned cell can
sample a label compatible with its family constraints before policy evaluation.

## Artifacts

```text
runs/m1734_task_quality_scenario_taxonomy_sampling_repair_preflight/summary.json
runs/m1734_task_quality_scenario_taxonomy_sampling_repair_preflight/repaired_scenario_specs.json
runs/m1734_task_quality_scenario_taxonomy_sampling_repair_preflight/repaired_scenario_specs.csv
runs/m1734_task_quality_scenario_taxonomy_sampling_repair_preflight/repaired_scenario_matrix.csv
runs/m1734_task_quality_scenario_taxonomy_sampling_repair_preflight/sampling_repair_delta.csv
runs/m1734_task_quality_scenario_taxonomy_sampling_repair_preflight/reset_stress_rows.csv
runs/m1734_task_quality_scenario_taxonomy_sampling_repair_preflight/sampling_failure_rows.csv
runs/m1734_task_quality_scenario_taxonomy_sampling_repair_preflight/label_distribution_by_spec.csv
runs/m1734_task_quality_scenario_taxonomy_sampling_repair_preflight/label_distribution_by_family.csv
runs/m1734_task_quality_scenario_taxonomy_sampling_repair_preflight/contract_violations.csv
runs/m1734_task_quality_scenario_taxonomy_sampling_repair_preflight/unsupported_scenario_features.csv
```

## Verification

Commands run:

```text
PYTHONPATH=src OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 python -m pytest -q tests/test_task_quality_scenario_taxonomy_sampling_repair_preflight.py tests/test_task_quality_scenario_taxonomy_execution.py tests/test_task_quality_scenario_taxonomy_preflight.py
python -m compileall -q src tests
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.task_quality_scenario_taxonomy_sampling_repair_preflight
```

Focused test result:

```text
11 passed
```

Preflight command result:

```text
result_class=task_quality_scenario_taxonomy_sampling_repair_preflight_pass
reset_stress_row_count=864
reset_success_count=864
sampling_failure_count=0
```

## Supported Claims

- M1731's scenario sampling failure has a repaired taxonomy route.
- The repaired taxonomy can reset all planned `864` public diagnostic cells.
- Unsupported fault-like features remain explicitly not covered.
- The P0 actor input contract remains clean.

## Unsupported Claims

- policy rollout result
- controller-family ranking
- scenario-family task quality conclusion
- recurrent advantage
- finite-window history necessity
- private-holdout evidence
- paper-level evidence
- level3 self-identification

## Decision

M1734 passes the reset-only sampling repair preflight. Route to M1735 result
audit before any repaired scenario taxonomy policy execution design.
