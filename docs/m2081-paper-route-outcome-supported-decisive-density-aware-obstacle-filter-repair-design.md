# M2081 Paper-Route Outcome-Supported Decisive Density-Aware Obstacle-Filter Repair Design

- status: completed
- decision: `density_aware_repair_design_admit_no_reset_implementation`
- parent synthesis: `docs/m2080-paper-route-outcome-supported-decisive-seed-robust-repaired-reset-validation-result-audit.md`
- reset/rollout/measured execution in M2081: `false`
- policy actions executed in M2081: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Design Goal

M2080 permits exactly one bounded density-aware continuation. M2081 freezes that
route.

The repair target is narrow:

```text
M2079 reset success: 234/240
M2079 reset failures: 6
failure class: obstacle scenario sampling failure
```

M2081 must not drop specs. The output remains a 240-spec panel, but only the six
M2079 failed specs may have obstacle filters changed.

## Failure Rows

Target task IDs:

```text
m2063-osd-osd_v0_0011_t1
m2063-osd-osd_v0_0023_t1
m2063-osd-osd_v0_0058_t2
m2063-osd-osd_v0_0076_t2
m2063-osd-osd_v0_0170_t4
m2063-osd-osd_v0_0200_t4
```

Shared failure axes:

```text
obstacle_distance_band: late
road_width_band: generous
curvature_band: moderate
initial_speed_band: low
dynamics_band: mixed_mu or nominal_mu
```

## Density Criterion

M2076 required existence of accepted cells. M2081 requires density:

```text
support_seed_offsets = [0, 240, 480, 720, 960]
support_seed_i = M2079 failing eval_seed_for_spec + support_seed_offset_i
target_support_seed_count = 5
required_seed_support = 5
minimum accepted grid cells per support seed = 80
```

The M2079 failing seed itself is included at offset `0`.

The grid is the same global scan used by M2076:

```text
distance grid count: 145
half-width grid count: 43
total grid cells: 6235
minimum accepted fraction: 80 / 6235 = 0.01283
```

## Repair Bounds

Repair is bounded:

```text
max_distance_window_width: 12.0 m
max_half_width_window_width: 0.80 m
global_distance_bounds: [1.0, 80.0]
global_half_width_bounds: [0.20, 1.35]
max_threshold_score_ceiling: 1.0
```

Threshold search order:

```text
0.25 first;
0.50 second;
1.00 only if needed.
```

A no-write probe on the six failed rows shows the route is feasible within
these bounds:

```text
threshold 1.0 minimum accepted cell count across the five support seeds:
m2063-osd-osd_v0_0011_t1: 90
m2063-osd-osd_v0_0023_t1: 120
m2063-osd-osd_v0_0058_t2: 90
m2063-osd-osd_v0_0076_t2: 90
m2063-osd-osd_v0_0170_t4: 90
m2063-osd-osd_v0_0200_t4: 120
```

## Implementation Route

M2082 should implement a focused no-reset adapter that:

```text
1. loads M2076 seed-robust repaired specs;
2. loads M2079 reset failure rows;
3. modifies only the six failed task IDs;
4. searches a density-maximizing support window for each targeted row;
5. requires 5/5 support seeds and minimum accepted grid cells >= 80;
6. preserves all non-target specs unchanged;
7. writes a new 240-spec density-aware repaired artifact.
```

The adapter must write:

```text
density_aware_repaired_executable_task_specs.json
density_aware_repair_rows.csv
density_support_rows.csv
planned_sentinel_workload.csv
claim_boundary.csv
summary.json
```

## Pass Gates

M2082 passes only if:

```text
input_executable_spec_count == 240
repaired_executable_spec_count == 240
targeted_repair_count == 6
non_target_spec_changed_count == 0
planned_sentinel_workload_count == 1200
target_support_seed_count == 5
required_seed_support == 5
minimum_accepted_grid_cell_count_required == 80
density_support_pass_count == 6
density_support_fail_count == 0
density_support_min_accepted_grid_cell_count >= 80
distance_window_width_max <= 12.0
half_width_window_width_max <= 0.80
threshold_score_ceiling_used <= 1.0
family_quota_pass == true
split_quota_pass == true
difficulty_axis_coverage_pass == true
contract_violation_count == 0
metadata_missing_count == 0
forbidden_key_violation_count == 0
guardrail_violation_count == 0
environment_reset_started == false
environment_rollout_started == false
policy_action_executed == false
measured_rollout_started == false
training_started == false
replay_started == false
ppo_used == false
promoted == false
private_holdout_used == false
actor_input_contract_changed == false
profile_specific_tuning == false
controller_family_ranking_claim_made == false
finite_window_vs_gru_conclusion_made == false
paper_level_claim_made == false
level3_self_id_claim_made == false
```

## Command Route

M2082 may run:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q \
  tests/test_paper_route_outcome_supported_decisive_density_aware_obstacle_filter_repair_preflight.py

PYTHONPATH=src python -m autodrift.paper_route_outcome_supported_decisive_density_aware_obstacle_filter_repair_preflight \
  --seed-robust-repaired-executable-task-specs runs/m2076_paper_route_outcome_supported_decisive_seed_robust_obstacle_filter_repair_preflight/seed_robust_repaired_executable_task_specs.json \
  --reset-failure-rows runs/m2079_paper_route_outcome_supported_decisive_seed_robust_repaired_reset_validation_preflight/reset_failure_rows.csv \
  --profile-run-dir runs/m1674_controller_family_one_seed_public_pilot \
  --output-dir runs/m2082_paper_route_outcome_supported_decisive_density_aware_obstacle_filter_repair_preflight \
  --support-seed-count 5 \
  --required-seed-support 5 \
  --minimum-accepted-grid-cell-count 80 \
  --target-spec-count 240 \
  --targeted-repair-count 6 \
  --max-distance-window-width 12.0 \
  --max-half-width-window-width 0.8 \
  --max-threshold-score-ceiling 1.0 \
  --next-blocker m2083-paper-route-outcome-supported-decisive-density-aware-obstacle-filter-repair-result-audit
```

## Claim Boundary

M2081 supports only:

```text
density-aware repair protocol is explicit enough to implement.
```

M2081 does not support:

```text
reset validity;
measured execution readiness;
controller-family ranking;
paper-level benchmark evidence;
finite-window-vs-GRU conclusion;
level3 self-identification.
```

## Next

Next milestone:

```text
m2082-paper-route-outcome-supported-decisive-density-aware-obstacle-filter-repair-preflight-implementation
```
