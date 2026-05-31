# M2075 Paper-Route Outcome-Supported Decisive Seed-Robust Obstacle-Filter Repair Design

- status: completed
- decision: `seed_robust_obstacle_filter_repair_design_admit_no_reset_implementation`
- parent audit: `docs/m2074-paper-route-outcome-supported-decisive-repaired-reset-validation-result-audit.md`
- reset/rollout/measured execution in M2075: `false`
- policy actions executed in M2075: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Design Goal

M2074 showed that M2070 repaired obstacle filters were seed-fragile:

```text
M2070 no-reset repair feasibility: 240/240
M2073 fresh-seed reset validation: 164/240
M2073 remaining failures: 76 obstacle scenario sampling failures
```

M2075 freezes a bounded no-reset repair route that must avoid the M2070 failure
mode. The next implementation should repair toward seed-robust obstacle support,
not toward one exact accepted point.

## Core Rule

For each spec, the repaired obstacle filter must be supported across a
deterministic seed panel:

```text
support_seed_offsets = [0, 240, 480, 720, 960]
support_seed_i = m2073_eval_seed_for_spec + support_seed_offset_i
required_seed_support = 5 / 5
```

The M2073 seed itself is included as offset `0`. A repair that cannot make the
failed M2073 seed feasible is not a repair.

## Repair Search

The implementation should load:

```text
runs/m2070_paper_route_outcome_supported_decisive_reset_materialization_repair_preflight/repaired_executable_task_specs.json
runs/m2073_paper_route_outcome_supported_decisive_repaired_reset_validation_preflight/reset_rows.csv
```

For each spec:

```text
1. Reconstruct the reset sampler state for each support seed.
2. Classify obstacle candidates with classify_obstacle_scenario.
3. Accept only candidates satisfying:
   - allowed_labels;
   - require_aeb_infeasible;
   - min_time_after_friction_step;
   - max_threshold_score.
4. First search the current repaired window.
5. If unsupported, search a bounded local window around the current repaired point.
6. If still unsupported, search a source-band window derived from the source metadata.
7. If still unsupported, escalate max_threshold_score in bounded stages.
8. If still unsupported, fail closed and route to result audit.
```

The repaired output must preserve the original task metadata and add repair
audit fields. It must not treat generated smoke-proxy rows as paper-valid tasks.

## Window Bounds

The repair may widen a point obstacle filter into a support window, but only
within explicit bounds:

```text
max_distance_window_width: 12.0 m
max_half_width_window_width: 0.80 m
global_distance_bounds: [1.0, 80.0]
global_half_width_bounds: [0.20, 1.35]
max_threshold_score_ceiling: 1.0
```

Search order:

```text
threshold score 0.25 first;
then 0.50 if needed;
then 1.00 only if still needed.
```

Any threshold-score escalation must be recorded. M2074 observed that all rows
previously escalated to `1.0` reset successfully, but this is a repair knob, not
paper-level task evidence.

## Support Metrics

M2076 should write one row per spec and support seed:

```text
task_source_id
eval_seed
support_seed
support_seed_offset
candidate_label
candidate_threshold_score
accepted_grid_cell_count
accepted_grid_cell_fraction
candidate_distance_min
candidate_distance_max
candidate_half_width_min
candidate_half_width_max
threshold_score_used
seed_supported
```

Spec-level summary fields:

```text
seed_support_count
required_seed_support
seed_support_pass
distance_window_width
half_width_window_width
threshold_score_escalated
scenario_filter_seed_robust_after
```

Panel-level pass fields:

```text
seed_robust_support_pass_count
seed_robust_support_fail_count
family_quota_pass
split_quota_pass
difficulty_axis_coverage_pass
contract_violation_count
metadata_missing_count
forbidden_key_violation_count
guardrail_violation_count
```

## Pass Gates

M2076 passes only if:

```text
input_executable_spec_count == 240
repaired_executable_spec_count == 240
planned_sentinel_workload_count == 1200
target_support_seed_count == 5
required_seed_support == 5
seed_robust_support_pass_count == 240
seed_robust_support_fail_count == 0
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

If any spec cannot meet `5/5` seed support inside the bounded repair policy,
M2076 must fail closed and M2077 must audit whether to reduce the panel or
synthesize the branch.

## Command Route

M2076 may implement a focused no-reset adapter:

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

Expected artifacts:

```text
runs/m2076_paper_route_outcome_supported_decisive_seed_robust_obstacle_filter_repair_preflight/summary.json
runs/m2076_paper_route_outcome_supported_decisive_seed_robust_obstacle_filter_repair_preflight/seed_robust_repaired_executable_task_specs.json
runs/m2076_paper_route_outcome_supported_decisive_seed_robust_obstacle_filter_repair_preflight/seed_support_rows.csv
runs/m2076_paper_route_outcome_supported_decisive_seed_robust_obstacle_filter_repair_preflight/seed_robust_repair_rows.csv
runs/m2076_paper_route_outcome_supported_decisive_seed_robust_obstacle_filter_repair_preflight/planned_sentinel_workload.csv
runs/m2076_paper_route_outcome_supported_decisive_seed_robust_obstacle_filter_repair_preflight/claim_boundary.csv
```

## Claim Boundary

M2075 supports only:

```text
seed-robust obstacle-filter repair design is explicit enough to implement.
```

M2075 does not support:

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
m2076-paper-route-outcome-supported-decisive-seed-robust-obstacle-filter-repair-preflight-implementation
```
