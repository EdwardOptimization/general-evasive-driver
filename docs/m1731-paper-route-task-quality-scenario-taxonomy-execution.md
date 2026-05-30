# M1731 Paper-Route Task-Quality Scenario Taxonomy Execution

- status: completed
- result class: `task_quality_scenario_taxonomy_execution_incomplete_or_fail`
- failure taxonomy: `scenario_sampling_failure`
- artifact: `runs/m1731_task_quality_scenario_taxonomy_execution/summary.json`
- parent design: `docs/m1730-paper-route-task-quality-scenario-taxonomy-execution-design.md`

## Summary

M1731 implemented and ran the measured scenario taxonomy runner for the fixed
M1728 matrix. The runner preserved scenario metadata joins and unsupported
feature boundaries, but the execution did not pass because many configured
scenario filters cannot reliably sample a matching obstacle scenario.

This milestone ran environment rollouts. It did not train, replay, run PPO,
promote, use private holdout, change actor inputs, tune profiles, rank
controller families, or claim paper-level evidence or level3 self-identification.

## Execution Result

- episode count: `422`
- target episode count: `864`
- scenario specs with completed rows: `36 / 72`
- scenario families with completed rows: `3 / 6`
- profiles present in completed rows: `12 / 12`
- failure count: `442`
- all selected metrics finite for completed rows: `true`
- guardrail violation count: `0`
- unsupported scenario features: `5`
- silent unsupported approximations: `0`
- unsupported faults treated as covered: `false`

The pass gate fails because:

```text
episode_count != 864
failure_count != 0
scenario_family_aggregate_rows != 6
scenario_spec_count != 72
```

Dominant failure:

```text
RuntimeError: failed to sample an obstacle scenario matching the configured filters
```

Failure distribution:

| scenario family | failed cells |
| --- | ---: |
| `aeb_infeasible_stable_aes` | `144` |
| `off_track_boundary_stress` | `144` |
| `hidden_dynamics_stress` | `144` |
| `drift_required_avoidance` | `10` |

This is a scenario sampling / taxonomy feasibility failure, not a PPO, replay,
checkpoint, or actor-input-contract failure.

## Completed Subset

Completed rows still produced finite diagnostic aggregates. They are not a
complete scenario taxonomy result and must not be used for controller-family
ranking.

Completed scenario-family aggregates:

| scenario family | episodes | success | collision | off-track noncollision |
| --- | ---: | ---: | ---: | ---: |
| `ordinary_stable_avoidance` | `144` | `0.0417` | `0.0347` | `0.9236` |
| `drift_required_avoidance` | `134` | `0.1791` | `0.5299` | `0.2910` |
| `unavoidable_mitigation` | `144` | `0.0625` | `0.9306` | `0.0069` |

Overall completed-row outcome buckets:

| outcome bucket | count |
| --- | ---: |
| `collision_failure` | `210` |
| `off_track_noncollision_noncompletion` | `173` |
| `success_obstacle_pass` | `39` |

These rows confirm that the execution adapter, metadata join, aggregate writer,
and guardrails work for sampleable specs. They do not validate the full M1728
taxonomy.

## Artifacts

```text
runs/m1731_task_quality_scenario_taxonomy_execution/summary.json
runs/m1731_task_quality_scenario_taxonomy_execution/episode_rows.csv
runs/m1731_task_quality_scenario_taxonomy_execution/failure_rows.csv
runs/m1731_task_quality_scenario_taxonomy_execution/run_state.json
runs/m1731_task_quality_scenario_taxonomy_execution/profile_aggregate.csv
runs/m1731_task_quality_scenario_taxonomy_execution/scenario_family_aggregate.csv
runs/m1731_task_quality_scenario_taxonomy_execution/scenario_role_aggregate.csv
runs/m1731_task_quality_scenario_taxonomy_execution/hidden_dynamics_bucket_aggregate.csv
runs/m1731_task_quality_scenario_taxonomy_execution/road_boundary_bucket_aggregate.csv
runs/m1731_task_quality_scenario_taxonomy_execution/obstacle_timing_bucket_aggregate.csv
runs/m1731_task_quality_scenario_taxonomy_execution/obstacle_lateral_bucket_aggregate.csv
runs/m1731_task_quality_scenario_taxonomy_execution/outcome_aggregate.csv
runs/m1731_task_quality_scenario_taxonomy_execution/termination_reason_aggregate.csv
runs/m1731_task_quality_scenario_taxonomy_execution/profile_outcome_aggregate.csv
runs/m1731_task_quality_scenario_taxonomy_execution/scenario_family_outcome_aggregate.csv
runs/m1731_task_quality_scenario_taxonomy_execution/unsupported_scenario_features.csv
```

## Verification

Commands run:

```text
PYTHONPATH=src OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 python -m pytest -q tests/test_task_quality_scenario_taxonomy_execution.py tests/test_task_quality_scenario_taxonomy_preflight.py
python -m compileall -q src tests
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.task_quality_scenario_taxonomy_execution --no-resume --device cpu
```

Focused test result:

```text
7 passed
```

Execution command result:

```text
result_class=task_quality_scenario_taxonomy_execution_incomplete_or_fail
episode_count=422
failure_count=442
guardrail_violation_count=0
```

## Supported Claims

- The M1731 runner can execute sampleable taxonomy specs and preserve scenario
  metadata in episode rows.
- The unsupported fault-like feature boundary is preserved.
- The current M1728 taxonomy is not execution-ready because several
  label/filter combinations are not sampling-feasible under the current
  generator.

## Unsupported Claims

- complete scenario taxonomy result
- controller-family ranking
- scenario-family quality conclusion
- recurrent advantage
- finite-window history necessity
- private-holdout evidence
- paper-level evidence
- level3 self-identification

## Decision

Route to M1732 result audit. M1732 should classify the failure, verify that no
guardrails were violated, and decide whether to repair scenario sampling
parameters, add a reset-stress preflight, or redesign parts of the taxonomy.
