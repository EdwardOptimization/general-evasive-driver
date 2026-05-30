# M1749 Paper-Route Task-Quality Revised Scenario Taxonomy Execution Design

- status: completed
- decision: `revised_execution_design_admit_adapter_implementation`
- parent synthesis: `docs/m1748-paper-route-task-quality-scenario-taxonomy-branch-synthesis.md`
- no rollout: true
- training/replay/PPO: false

## Summary

M1749 designs the revised public diagnostic execution over the fixed
semantics-aware scenario taxonomy. The design does not admit immediate rollout:
the current runner can compute M1746 episode metrics, but it must first be
adapted to preserve M1743 semantics fields and to validate applicability-aware
metric completeness.

The next step is a logging/adapter implementation milestone, not an execution
milestone.

## Workload

Use the fixed M1743 materialization:

```text
scenario specs:
  runs/m1743_task_quality_outcome_semantics_materialization_preflight/semantics_scenario_specs.json

scenario matrix:
  runs/m1743_task_quality_outcome_semantics_materialization_preflight/semantics_scenario_matrix.csv

target cells:
  72 specs x 12 profiles = 864 public diagnostic episodes
```

The runner must preserve these semantics fields into every episode row:

```text
evaluation_role
primary_metric_family
ranking_eligible_after_audit
diagnostic_only_no_ranking_claim
benchmark_row
metric_required_*
```

## Required Adapter Work

M1750 should implement:

- loader support for `semantics_scenario_specs.json`;
- pass-through of M1743 semantics fields from workload/spec rows into episode
  rows;
- revised aggregate outputs grouped by `evaluation_role`,
  `primary_metric_family`, `scenario_family`, `profile_name`,
  `hidden_dynamics_bucket`, and outcome bucket;
- applicability-aware metric completeness checks;
- focused tests proving no reward, termination, actor input, profile, training,
  replay, or PPO behavior changed.

## Metric Completeness Gates

Always-required finite fields:

```text
dt
track_width
max_abs_beta
max_abs_yaw_rate
max_off_track_overshoot
off_track_severity_proxy
collision_mitigation_score
```

Always-required boolean fields:

```text
recovery_success
drift_used
controlled_drift_recovery_success
collision
obstacle_passed_raw
diagnostic_only_no_ranking_claim
```

Applicability-aware fields:

- `first_obstacle_pass_step`, `first_obstacle_pass_time_s`,
  `first_recovery_step`, `first_recovery_time_s`, and `recovery_time_proxy`
  must be finite when `obstacle_passed_raw == true` and may be `NaN` otherwise;
- `impact_speed_proxy`, `impact_beta_abs`, `impact_yaw_rate_abs`, and
  `impact_severity_proxy` must be finite when `collision == true` and may be
  `NaN` otherwise;
- hidden-dynamics robustness aggregates must exist when
  `hidden_dynamics_bucket` is present.

## Execution Pass Criteria

The later execution milestone should pass only if:

- episode count is `864`;
- failure count is `0`;
- profile count is `12`;
- scenario spec count is `72`;
- scenario family count is `6`;
- guardrail violation count is `0`;
- selected legacy metrics are finite;
- semantics fields are present in every row;
- metric completeness gates pass;
- required aggregate artifacts exist;
- no ranking, promotion, private holdout, paper-level, or level3 self-ID claim
  is made.

## Required Artifacts

The later execution should write:

```text
summary.json
episode_rows.csv
failure_rows.csv
run_state.json
profile_aggregate.csv
scenario_family_aggregate.csv
evaluation_role_aggregate.csv
primary_metric_family_aggregate.csv
scenario_family_outcome_aggregate.csv
profile_outcome_aggregate.csv
hidden_dynamics_bucket_aggregate.csv
profile_hidden_dynamics_worst_bucket.csv
metric_completeness_summary.csv
metric_completeness_failures.csv
unsupported_scenario_features.csv
```

All artifacts are public diagnostic artifacts until audited. They are not
controller-family ranking or paper-level evidence.

## Claim Boundary

Supported:

- revised execution design;
- adapter implementation route;
- metric completeness and aggregate requirements.

Unsupported:

- rollout result;
- profile ranking or promotion;
- private-holdout evidence;
- paper-level benchmark result;
- level3 self-identification.

## Decision

Route to M1750 revised scenario taxonomy execution adapter implementation.
