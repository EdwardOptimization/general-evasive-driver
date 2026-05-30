# M1752 Paper-Route Task-Quality Revised Scenario Taxonomy Measured Execution Design

- status: completed
- decision: `revised_measured_execution_design_admit_m1753_execution`
- parent audit: `docs/m1751-paper-route-task-quality-revised-scenario-taxonomy-execution-adapter-result-audit.md`
- no rollout: true
- training/replay/PPO: false

## Summary

M1752 pre-registers the adapter-aware revised public diagnostic execution. The
execution will use M1743 semantics metadata and M1734 executable repaired specs
as separate inputs, write to a new M1753 run directory, and defer all
interpretation to a later result audit.

This design admits M1753 measured execution, not controller-family ranking or
paper-level evidence.

## Fixed Inputs

Metadata scenario specs:

```text
runs/m1743_task_quality_outcome_semantics_materialization_preflight/semantics_scenario_specs.json
```

Workload matrix:

```text
runs/m1743_task_quality_outcome_semantics_materialization_preflight/semantics_scenario_matrix.csv
```

Executable scenario specs:

```text
runs/m1734_task_quality_scenario_taxonomy_sampling_repair_preflight/repaired_scenario_specs.json
```

Unsupported-feature boundary:

```text
runs/m1734_task_quality_scenario_taxonomy_sampling_repair_preflight/unsupported_scenario_features.csv
```

Preflight facts checked before this design:

```text
semantics specs: 72
executable specs: 72
workload rows: 864
profiles: 12
scenario families: 6
evaluation roles: benchmark, diagnostic_stress, mitigation_diagnostic
scenario id sets equal: true
```

## Execution Command

M1753 should run:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.task_quality_scenario_taxonomy_execution \
  --output-dir runs/m1753_revised_scenario_taxonomy_execution \
  --scenario-specs runs/m1743_task_quality_outcome_semantics_materialization_preflight/semantics_scenario_specs.json \
  --executable-scenario-specs runs/m1734_task_quality_scenario_taxonomy_sampling_repair_preflight/repaired_scenario_specs.json \
  --workload runs/m1743_task_quality_outcome_semantics_materialization_preflight/semantics_scenario_matrix.csv \
  --unsupported-features runs/m1734_task_quality_scenario_taxonomy_sampling_repair_preflight/unsupported_scenario_features.csv \
  --eval-seed-base 175300 \
  --device cpu \
  --no-resume \
  --next-blocker m1754-paper-route-task-quality-revised-scenario-taxonomy-result-audit
```

## Required Pass Criteria

M1753 passes execution only if:

- `episode_count == 864`;
- `failure_count == 0`;
- `profile_count == 12`;
- `scenario_spec_count == 72`;
- `scenario_family_count == 6`;
- `guardrail_violation_count == 0`;
- selected legacy metrics are finite;
- M1743 semantics fields are present in every episode row;
- `metric_completeness_passed == true`;
- `metric_completeness_failure_count == 0`;
- unsupported fault-like features remain explicitly uncovered;
- no training, replay, PPO, promotion, private holdout, actor-input change,
  reward change, termination change, profile-specific tuning, ranking claim,
  paper-level claim, or level3 self-ID claim occurs.

## Required Artifacts

M1753 must write:

```text
summary.json
episode_rows.csv
failure_rows.csv
run_state.json
profile_aggregate.csv
scenario_family_aggregate.csv
scenario_role_aggregate.csv
evaluation_role_aggregate.csv
primary_metric_family_aggregate.csv
sampling_repair_variant_aggregate.csv
hidden_dynamics_bucket_aggregate.csv
road_boundary_bucket_aggregate.csv
obstacle_timing_bucket_aggregate.csv
obstacle_lateral_bucket_aggregate.csv
sampled_obstacle_label_aggregate.csv
outcome_aggregate.csv
termination_reason_aggregate.csv
profile_outcome_aggregate.csv
scenario_family_outcome_aggregate.csv
evaluation_role_outcome_aggregate.csv
primary_metric_family_outcome_aggregate.csv
scenario_family_sampled_label_aggregate.csv
profile_hidden_dynamics_worst_bucket.csv
unsupported_scenario_features.csv
metric_completeness_summary.csv
metric_completeness_failures.csv
```

## Interpretation Boundary

M1753 may claim only that the revised public diagnostic execution completed or
failed under the pre-registered gates. It must not interpret controller-family
rank, recurrent advantage, paper-level benchmark quality, private-holdout
evidence, or level3 self-identification.

If M1753 passes, route to M1754 result audit. If it fails, route to execution
failure audit or runner repair depending on whether the failure is sampling,
metric completeness, artifact completeness, or guardrail related.

## Decision

Admit M1753 measured execution over the fixed `864`-cell revised public
diagnostic workload.
