# M1764 Single-Cell Seed-Repair Completion Execution

- status: completed
- result class: `task_quality_scenario_taxonomy_execution_pass`
- output dir: `runs/m1764_revised_scenario_taxonomy_single_seed_completion`
- training/replay/PPO: false

## Summary

M1764 ran exactly the pre-registered replacement-seed completion command. It
executed the single missing workload cell with replacement seed `175760`, merged
that repaired row with the `863` M1756 completed rows through the M1761
provenance helper, and wrote a fresh completed public diagnostic artifact.

This is a completion-execution result. It is still not a controller-family
ranking or paper-level benchmark result until audited.

## Counts

```text
result_class: task_quality_scenario_taxonomy_execution_pass
episode_count: 864
target_episode_count: 864
failure_count: 0
profile_count: 12
scenario_spec_count: 72
scenario_family_count: 6
all_selected_metrics_finite: true
metric_completeness_passed: true
metric_completeness_failure_count: 0
guardrail_violation_count: 0
```

## Seed-Repair Provenance

```text
seed_repair_applied_row_count: 1
workload_id: m1728-s4-02::L2_window_13_current_tiled
original_eval_seed: 175761
replacement_eval_seed: 175760
replacement_seed_offset: -1
expected_sampled_obstacle_label: unavoidable
seed_repair_rule: nearest_successful_neighbor_tie_lower
seed_repair_source: m1758_single_sampling_failure_reset_only_probe
original_failure_error_type: RuntimeError
original_failure_error_message: failed to sample an obstacle scenario matching the configured filters
```

The final `episode_rows.csv` contains `864` data rows and exactly one
`seed_repair_applied=true` row. `failure_rows.csv` contains only a header, while
`original_failure_rows.csv` preserves the original M1756 failure row.

## Artifacts

Key artifacts:

```text
runs/m1764_revised_scenario_taxonomy_single_seed_completion/summary.json
runs/m1764_revised_scenario_taxonomy_single_seed_completion/episode_rows.csv
runs/m1764_revised_scenario_taxonomy_single_seed_completion/failure_rows.csv
runs/m1764_revised_scenario_taxonomy_single_seed_completion/original_failure_rows.csv
runs/m1764_revised_scenario_taxonomy_single_seed_completion/seed_repair_provenance.csv
runs/m1764_revised_scenario_taxonomy_single_seed_completion/metric_completeness_summary.csv
runs/m1764_revised_scenario_taxonomy_single_seed_completion/metric_completeness_failures.csv
```

Aggregate row counts from the summary:

```text
evaluation_role_aggregate_rows: 3
primary_metric_family_aggregate_rows: 5
scenario_family_aggregate_rows: 6
profile_aggregate_rows: 12
outcome_aggregate_rows: 3
sampled_obstacle_label_aggregate_rows: 4
```

## Guardrails

- environment rollout started: `true`
- replacement workload cells run: `1`
- training started: `false`
- replay started: `false`
- PPO used: `false`
- promoted: `false`
- private holdout used: `false`
- actor input contract changed: `false`
- reward changed: `false`
- dynamics changed: `false`
- termination behavior changed: `false`
- profile configs changed: `false`
- scenario specs changed: `false`
- profile-specific tuning: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`
- unsupported faults treated as covered: `false`
- guardrail violation count: `0`

## Claim Boundary

Supported:

- the M1756 revised scenario taxonomy artifact can be completed with a single
  traceable replacement-seed row;
- the completed artifact has `864` rows, `0` failures, complete metrics, and
  exactly one seed-repair provenance row.

Unsupported until audit:

- controller-family ranking;
- profile comparison;
- paper-level benchmark evidence;
- private-holdout evidence;
- level3 self-identification evidence.

## Decision

Route to M1765 completion result audit before interpreting the completed matrix.
