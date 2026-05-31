# M1969 Executable V2 Task-Quality Calibrated Offtrack Parent-Tier Normalization Implementation

- status: completed
- decision: `task_quality_calibrated_offtrack_parent_tier_normalization_implementation_pass_route_to_audit`
- run dir: `runs/m1969_executable_v2_task_quality_calibrated_materialization_preflight_repaired`
- reset/rollout/measured execution in M1969: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Implementation

M1969 implements the M1968 explicit sentinel normalization:

```text
tier_not_applicable_offtrack_boundary_relief
```

Changed files:

```text
src/autodrift/executable_v2_task_quality_calibrated_materialization_preflight.py
tests/test_executable_v2_task_quality_calibrated_materialization_preflight.py
```

The implementation:

- adds `OFFTRACK_PARENT_TIER_SENTINEL`;
- normalizes blank `parent_feasibility_tier_id` only when
  `repair_source_kind == offtrack_boundary_relief`;
- leaves non-offtrack blank parent tiers fail-closed;
- adds blank/normalized parent-tier counters to the preflight summary;
- keeps runner validation strict.

## Tests

Focused tests:

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q tests/test_executable_v2_task_quality_calibrated_materialization_preflight.py
4 passed
```

The tests cover:

- offtrack blank parent tier normalizes to the explicit sentinel;
- non-offtrack blank parent tier remains blank/fail-closed;
- synthetic 80-spec / 960-workload preflight still passes;
- offtrack planned workload rows inherit the sentinel.

## No-Reset Materialization Result

Command:

```bash
PYTHONPATH=src python -m autodrift.executable_v2_task_quality_calibrated_materialization_preflight \
  --subset-config configs/executable_v2_task_quality_calibrated_materialization_subset_v0.json \
  --repair-accepted-cells runs/m1952_executable_v2_task_quality_offtrack_support_repair_calibrated_source_mining/repair_accepted_cells.csv \
  --profile-run-dir runs/m1674_controller_family_one_seed_public_pilot \
  --output-dir runs/m1969_executable_v2_task_quality_calibrated_materialization_preflight_repaired \
  --next-blocker m1970-executable-v2-task-quality-calibrated-offtrack-parent-tier-normalization-result-audit
```

Result:

```text
result_class: task_quality_calibrated_materialization_preflight_pass
executable_task_spec_count: 80
planned_workload_cell_count: 960
controller_profile_count: 12
selected_accepted_cell_row_count: 3382
parent_feasibility_tier_blank_spec_count: 0
parent_feasibility_tier_blank_workload_count: 0
parent_feasibility_tier_normalized_spec_count: 8
parent_feasibility_tier_normalized_workload_count: 96
contract_violation_count: 0
forbidden_key_violation_count: 0
guardrail_violation_count: 0
environment_reset_started: false
environment_rollout_started: false
measured_rollout_started: false
```

Source-kind and role-surface quotas remain passing.

## Interpretation Boundary

Supported by M1969:

- the blank offtrack parent-tier metadata blocker is repaired at the no-reset
  materialization layer;
- repaired artifacts have no blank `parent_feasibility_tier_id` values;
- the normalization affects exactly the intended `8` offtrack specs and `96`
  workload cells;
- no reset, rollout, measured execution, ranking, training, replay, or PPO was
  run.

Unsupported by M1969:

- reset validity of the repaired artifacts;
- measured rollout success;
- controller-family ranking;
- paper-level benchmark evidence;
- policy improvement;
- finite-window vs GRU conclusion;
- level3 self-identification.

## Next

Next milestone:

```text
m1970-executable-v2-task-quality-calibrated-offtrack-parent-tier-normalization-result-audit
```

M1970 should audit the repaired no-reset artifacts before any reset validation
or measured execution is admitted.
