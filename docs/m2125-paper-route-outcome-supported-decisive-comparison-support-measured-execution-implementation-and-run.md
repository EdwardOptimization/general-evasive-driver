# M2125 Paper-Route Outcome-Supported Decisive Comparison-Support Measured Execution Implementation And Run

- status: completed
- decision: `comparison_support_measured_execution_pass_route_to_result_audit`
- measured artifact: `runs/m2125_paper_route_outcome_supported_decisive_comparison_support_measured_execution/summary.json`
- focused tests: `4 passed`
- reset in M2125: `true` as part of rollout execution
- rollout/measured execution in M2125: `true`
- policy actions executed in M2125: `true`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Implementation Summary

M2125 adds a comparison-support-specific measured runner:

```text
src/autodrift/paper_route_outcome_supported_decisive_comparison_support_measured_runner.py
tests/test_paper_route_outcome_supported_decisive_comparison_support_measured_runner.py
```

It reuses the established low-level rollout path, but switches the metadata and
quota contract to the M2118 panel:

```text
comparison_support_intent
target_support_tier
dynamics_band
obstacle_timing_band
road_width_band
initial_speed_band
materialization_semantics=comparison_support_smoke_proxy
```

It writes the M2123 planned measured-execution artifacts:

```text
summary.json
episode_rows.csv
failure_rows.csv
validation_failure_rows.csv
metadata_missing_rows.csv
metric_completeness_failures.csv
profile_aggregate.csv
intent_aggregate.csv
target_support_tier_aggregate.csv
source_kind_aggregate.csv
proxy_template_aggregate.csv
outcome_aggregate.csv
termination_reason_aggregate.csv
claim_boundary.csv
run_state.json
```

## Command

Executed:

```bash
PYTHONPATH=src python -m autodrift.paper_route_outcome_supported_decisive_comparison_support_measured_runner \
  --executable-task-specs runs/m2118_paper_route_outcome_supported_decisive_comparison_support_materialization_preflight/executable_task_specs.json \
  --workload runs/m2118_paper_route_outcome_supported_decisive_comparison_support_materialization_preflight/planned_workload.csv \
  --output-dir runs/m2125_paper_route_outcome_supported_decisive_comparison_support_measured_execution \
  --eval-seed-base 212300 \
  --device cpu \
  --target-episode-count 1200 \
  --target-spec-count 240 \
  --target-profile-count 5 \
  --next-blocker m2126-paper-route-outcome-supported-decisive-comparison-support-measured-execution-result-audit
```

## Result

M2125 passes measured-execution completeness:

```text
result_class: comparison_support_measured_execution_pass
episode_count: 1200
target_episode_count: 1200
failure_count: 0
validation_failure_count: 0
spec_count: 240
target_spec_count: 240
profile_count: 5
target_profile_count: 5
metadata_missing_count: 0
metric_completeness_failure_count: 0
all_selected_metrics_finite: true
intent_quota_pass: true
target_support_tier_quota_pass: true
source_kind_quota_pass: true
proxy_template_quota_pass: true
generated_proxy_quota_pass: true
guardrail_violation_count: 0
```

Outcome counts:

```text
success_obstacle_pass: 188
collision_failure: 144
off_track_noncollision_noncompletion: 868
```

The outcome counts are recorded for audit and localization only. M2125 does not
rank profiles or draw finite-window-vs-GRU conclusions.

## Claim Boundary

Supported:

```text
The comparison-support runner can execute the reset-valid 240-spec / 1200-cell
workload with complete metadata, complete metrics, no failure rows, and no
guardrail violations.
```

Unsupported:

```text
comparison-ready support;
controller-family ranking;
finite-window-vs-GRU conclusion;
paper-level benchmark evidence;
level3 self-identification.
```

## Next

M2126 must audit this measured artifact before localization or any
interpretation:

```text
m2126-paper-route-outcome-supported-decisive-comparison-support-measured-execution-result-audit
```
