# M1926 Executable V2 Task-Quality Scenario Redesign Materialization Implementation

- status: completed
- decision: `task_quality_scenario_materialization_selector_pass_route_to_command_design`
- result class: `task_quality_scenario_materialization_selector_pass`
- source: `src/autodrift/executable_v2_task_quality_scenario_redesign_materialization_selector.py`
- tests: `tests/test_executable_v2_task_quality_scenario_redesign_materialization_selector.py`
- focused tests: `2 passed`
- subset config: `configs/executable_v2_task_quality_scenario_redesign_materialization_subset_v0.json`
- summary: `runs/m1926_executable_v2_task_quality_scenario_redesign_materialization_implementation/summary.json`
- selected sources CSV: `runs/m1926_executable_v2_task_quality_scenario_redesign_materialization_implementation/selected_sources.csv`
- reset/rollout/measured execution in M1926: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Commands

Focused tests:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q \
  tests/test_executable_v2_task_quality_scenario_redesign_materialization_selector.py
```

Selector execution:

```bash
PYTHONPATH=src python -m autodrift.executable_v2_task_quality_scenario_redesign_materialization_selector \
  --joined-source-support runs/m1924_executable_v2_task_quality_scenario_redesign_source_mining_result_audit/joined_source_support.csv \
  --output-config configs/executable_v2_task_quality_scenario_redesign_materialization_subset_v0.json \
  --output-dir runs/m1926_executable_v2_task_quality_scenario_redesign_materialization_implementation
```

Return code:

```text
0
```

## Result

M1926 implements the M1925 deterministic selector and emits the first bounded
task-quality source subset.

```text
input_row_count: 640
eligible_source_count: 357
selected_source_count: 80
expected_controller_profile_count: 12
expected_planned_workload_cell_count: 960
selection_failure_count: 0
paper_holdout_selected_count: 0
labels_enter_actor_input_count: 0
ranking_admissible_by_default_count: 0
guardrail_violation_count: 0
```

Selected tier counts:

```text
tier_a_positive_support_sanity: 16
tier_b_feasible_emergency: 16
tier_c_boundary_near_miss: 16
tier_d_handling_limit_drift_required: 16
tier_e_mitigation_only: 16
```

Selected role counts:

```text
drift_required_recovery: 20
stable_aeb: 20
stable_aes_only: 20
unavoidable_mitigation: 20
```

Selected surface counts:

```text
steady_surface: 40
post_friction_step: 40
```

Selected split counts:

```text
public_gate: 67
public_debug: 13
```

Every `feasibility_tier_id x source_role_semantics` cell has exactly four
selected sources, and every cell has exactly two `steady_surface` and two
`post_friction_step` sources.

## Gate Results

```text
tier_role_balance_pass: true
surface_balance_pass: true
result_class: task_quality_scenario_materialization_selector_pass
recommended_next_route: route_to_materialization_command_design
```

No holdout source is selected. No controller-family ranking, measured rollout,
training, replay, PPO, paper-level result, or level3 self-ID claim is made.

## Interpretation Boundary

Supported:

- the M1924 supported pool can produce an exact balanced 80-source public panel;
- the panel preserves tier, role, split, surface, speed, mu, and support
  metadata in a source-only config artifact;
- later no-rollout executable materialization can target 960 planned cells.

Unsupported:

- reset success;
- rollout success;
- measured controller performance;
- controller-family ranking;
- policy improvement;
- paper-level benchmark evidence;
- level3 self-identification evidence.

## Next

Next milestone:

```text
m1927-executable-v2-task-quality-scenario-redesign-materialization-command-design
```

M1927 should design the exact no-rollout command for converting the 80-source
subset into executable task specs and workload rows. It should decide whether
existing materializers can be adapted or a focused new materializer is needed,
and it must still keep reset, rollout, measured execution, ranking, paper-level
claims, and level3 self-ID claims blocked.
