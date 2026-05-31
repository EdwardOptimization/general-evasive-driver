# M2076 Paper-Route Outcome-Supported Decisive Seed-Robust Obstacle-Filter Repair Preflight Implementation

- status: completed
- decision: `seed_robust_obstacle_filter_repair_preflight_pass_route_to_result_audit`
- run artifact: `runs/m2076_paper_route_outcome_supported_decisive_seed_robust_obstacle_filter_repair_preflight/summary.json`
- focused tests: `2 passed`
- reset/rollout/measured execution in M2076: `false`
- policy actions executed in M2076: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Implementation

M2076 adds a focused no-reset preflight tool:

```text
src/autodrift/paper_route_outcome_supported_decisive_seed_robust_obstacle_filter_repair_preflight.py
tests/test_paper_route_outcome_supported_decisive_seed_robust_obstacle_filter_repair_preflight.py
```

The tool repairs obstacle filters by scanning `classify_obstacle_scenario` over
a deterministic support-seed panel. It does not call environment reset, rollout,
policy action, measured execution, training, replay, or PPO.

## Run Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q \
  tests/test_paper_route_outcome_supported_decisive_seed_robust_obstacle_filter_repair_preflight.py

PYTHONPATH=src python -m autodrift.paper_route_outcome_supported_decisive_seed_robust_obstacle_filter_repair_preflight \
  --repaired-executable-task-specs runs/m2070_paper_route_outcome_supported_decisive_reset_materialization_repair_preflight/repaired_executable_task_specs.json \
  --reset-rows runs/m2073_paper_route_outcome_supported_decisive_repaired_reset_validation_preflight/reset_rows.csv \
  --profile-run-dir runs/m1674_controller_family_one_seed_public_pilot \
  --output-dir runs/m2076_paper_route_outcome_supported_decisive_seed_robust_obstacle_filter_repair_preflight \
  --support-seed-count 5 \
  --required-seed-support 5 \
  --target-spec-count 240 \
  --max-distance-window-width 12.0 \
  --max-half-width-window-width 0.8 \
  --max-threshold-score-ceiling 1.0 \
  --next-blocker m2077-paper-route-outcome-supported-decisive-seed-robust-obstacle-filter-repair-result-audit
```

## Result

```text
result_class: outcome_supported_decisive_seed_robust_obstacle_filter_repair_preflight_pass
input_executable_spec_count: 240
repaired_executable_spec_count: 240
planned_sentinel_workload_count: 1200
target_support_seed_count: 5
required_seed_support: 5
seed_robust_support_pass_count: 240
seed_robust_support_fail_count: 0
distance_window_width_max: 12.0
half_width_window_width_max: 0.8
threshold_score_ceiling_used: 1.0
family_quota_pass: true
split_quota_pass: true
difficulty_axis_coverage_pass: true
contract_violation_count: 0
metadata_missing_count: 0
forbidden_key_violation_count: 0
profile_missing_count: 0
guardrail_violation_count: 0
```

Threshold usage:

```text
0.25: 203 specs
0.50: 21 specs
1.00: 16 specs
threshold_score_escalated: 22 specs
```

All specs reached `5/5` support:

```text
seed_support_count=5: 240 specs
repair_reason=seed_robust_window_found: 240 specs
```

## Interpretation

M2076 directly addresses the M2074 diagnosis. It turns the M2070
single-seed/exact-point repair into a multi-seed support-window artifact:

```text
M2073 failed reset validation at 164/240.
M2076 no-reset support scan finds 240/240 specs with 5/5 seed support.
```

This is still not reset-validity evidence. It is only stronger materialization
evidence that the next reset rerun is justified.

## Supported Claims

Supported:

```text
The outcome-supported decisive panel now has a no-reset seed-robust obstacle-filter repair artifact.
The artifact preserves family, split, and difficulty-axis quotas.
The repair keeps contract, metadata, forbidden-key, profile, and guardrail counts clean.
The next route can audit whether to admit reset-validation command design.
```

Unsupported:

```text
reset validity;
measured execution readiness;
controller-family ranking;
paper-level benchmark evidence;
finite-window-vs-GRU conclusion;
level3 self-identification.
```

## Artifacts

```text
runs/m2076_paper_route_outcome_supported_decisive_seed_robust_obstacle_filter_repair_preflight/summary.json
runs/m2076_paper_route_outcome_supported_decisive_seed_robust_obstacle_filter_repair_preflight/seed_robust_repaired_executable_task_specs.json
runs/m2076_paper_route_outcome_supported_decisive_seed_robust_obstacle_filter_repair_preflight/seed_robust_repair_rows.csv
runs/m2076_paper_route_outcome_supported_decisive_seed_robust_obstacle_filter_repair_preflight/seed_support_rows.csv
runs/m2076_paper_route_outcome_supported_decisive_seed_robust_obstacle_filter_repair_preflight/planned_sentinel_workload.csv
runs/m2076_paper_route_outcome_supported_decisive_seed_robust_obstacle_filter_repair_preflight/claim_boundary.csv
```

## Next

Next milestone:

```text
m2077-paper-route-outcome-supported-decisive-seed-robust-obstacle-filter-repair-result-audit
```
