# M1750 Paper-Route Task-Quality Revised Scenario Taxonomy Execution Adapter Implementation

- status: completed
- result class: `revised_scenario_taxonomy_execution_adapter_implementation_pass`
- parent design: `docs/m1749-paper-route-task-quality-revised-scenario-taxonomy-execution-design.md`
- no rollout: true
- training/replay/PPO: false

## Summary

M1750 implements the adapter work required before a revised public diagnostic
scenario-taxonomy execution. The runner can now consume M1743
`semantics_scenario_specs`, preserve semantics fields into episode/failure rows,
write semantics-aware aggregates, and generate applicability-aware metric
completeness reports.

No full `864`-cell rollout was executed. This is infrastructure evidence only.

## Implemented

- `load_scenario_specs` now accepts `scenario_specs`,
  `repaired_scenario_specs`, and `semantics_scenario_specs` payloads.
- `scenario_taxonomy_workload_rows` preserves M1743 semantics fields:
  `evaluation_role`, `primary_metric_family`, `benchmark_row`,
  `ranking_eligible_after_audit`, `diagnostic_only_no_ranking_claim`, and all
  `metric_required_*` flags.
- `_run_scenario_workload_cell` and failure rows pass those semantics fields
  through to downstream artifacts.
- `run_scenario_taxonomy_execution` supports a separate
  `--executable-scenario-specs` path, so a future revised execution can join
  M1743 semantics metadata with M1734 executable repaired specs.
- Revised aggregates now include `evaluation_role_aggregate`,
  `primary_metric_family_aggregate`, `evaluation_role_outcome_aggregate`, and
  `primary_metric_family_outcome_aggregate`.
- `metric_completeness_rows` writes `metric_completeness_summary.csv` and
  `metric_completeness_failures.csv`.

## Metric Completeness Semantics

Always finite:

```text
dt
track_width
max_abs_beta
max_abs_yaw_rate
max_off_track_overshoot
off_track_severity_proxy
collision_mitigation_score
```

Always boolean-like:

```text
recovery_success
drift_used
controlled_drift_recovery_success
collision
obstacle_passed_raw
diagnostic_only_no_ranking_claim
```

Applicability-aware:

- `first_obstacle_pass_step` and `first_obstacle_pass_time_s` must be finite
  when `obstacle_passed_raw == true`.
- `first_recovery_step`, `first_recovery_time_s`, and `recovery_time_proxy`
  must be finite when `recovery_success == true`. They may be missing when the
  vehicle passes the obstacle but does not recover, because that is an outcome,
  not a metric logging failure.
- impact severity fields must be finite when `collision == true` and may be
  missing otherwise.

## Verification

Focused scenario-taxonomy tests:

```text
10 passed
```

Affected execution/metric tests:

```text
21 passed
```

Full test suite:

```text
1707 passed, 4 warnings
```

Compile check:

```text
python -m compileall -q src tests
```

## Guardrails

- full rollout started: `false`
- training started: `false`
- replay started: `false`
- PPO used: `false`
- promoted: `false`
- private holdout used: `false`
- actor input contract changed: `false`
- reward changed: `false`
- termination behavior changed: `false`
- profile-specific tuning: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`
- guardrail violation count: `0`

## Claim Boundary

Supported:

- revised scenario execution adapter implementation;
- semantics payload loading and pass-through;
- applicability-aware metric completeness helpers;
- aggregate artifact hooks.

Unsupported:

- revised rollout result;
- controller-family ranking;
- private-holdout evidence;
- paper-level benchmark evidence;
- level3 self-identification.

## Decision

Route to M1751 adapter result audit before any revised execution design or
rollout.
