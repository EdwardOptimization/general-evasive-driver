# M2151 Paper-Route Current-Sim Controlled Comparison Executable Spec Materialization Implementation

- status: completed
- decision: `current_sim_controlled_comparison_executable_spec_materialization_pass_route_to_audit`
- manifest: `experiments/manifests/m2151-paper-route-current-sim-controlled-comparison-executable-spec-materialization-implementation.json`
- implementation: `src/autodrift/paper_route_current_sim_controlled_comparison_executable_spec_materialization.py`
- tests: `tests/test_paper_route_current_sim_controlled_comparison_executable_spec_materialization.py`
- run artifact: `runs/m2151_paper_route_current_sim_controlled_comparison_executable_spec_materialization/summary.json`
- reset/rollout/measured execution in M2151: `false`
- policy actions executed in M2151: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- winner selected: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Command

```bash
PYTHONPATH=src python -m autodrift.paper_route_current_sim_controlled_comparison_executable_spec_materialization \
  --benchmark-config configs/paper_route_current_sim_controlled_comparison_benchmark_v0.json \
  --output-dir runs/m2151_paper_route_current_sim_controlled_comparison_executable_spec_materialization \
  --next-blocker m2152-paper-route-current-sim-controlled-comparison-executable-spec-materialization-audit
```

## Result

```text
result_class: current_sim_controlled_comparison_executable_spec_materialization_pass
executable_spec_count: 40
expected_executable_spec_count: 40
task_family_count: 5
profile_count: 8
planned_workload_row_count: 320
expected_workload_row_count: 320
materialization_failure_count: 0
contract_violation_count: 0
forbidden_key_violation_count: 0
profile_specific_tuning_count: 0
metric_count: 18
claim_boundary_row_count: 7
guardrail_violation_count: 0
```

No environment reset, environment rollout, policy action, measured execution,
training, replay, PPO, checkpoint promotion, ranking, paper claim,
finite-window-vs-GRU conclusion, or level3 self-ID claim is made.

## Task-Family Coverage

Each task family has exactly `8` executable specs:

```text
T1_reactive_emergency_avoidance: 8
T2_delayed_actuator_response: 8
T3_diagnostic_warmup_obstacle_reveal: 8
T4_same_current_different_older_history: 8
T5_terminal_boundary_near_constraint: 8
```

M2151 uses deterministic source/eval seeds and P0-compatible env templates from
the existing decisive-history hook infrastructure. It writes env configs but
does not instantiate or reset an environment.

## Workload Coverage

The planned workload crosses each executable spec with the full 8-profile matrix:

```text
40 specs * 8 profiles = 320 planned workload rows
```

Profiles:

```text
L0_current_masked
L1_one_step
L2_window_13
L2_window_25
L2_window_50
L2_window_100
L3_online_gru
L3_reset_control
```

The workload rows deliberately leave `checkpoint_path` empty and mark
`checkpoint_required_for_measured_execution=true`. That is acceptable before
reset validation because reset validation only needs executable env specs. It
must be repaired before measured execution.

## Artifacts

M2151 writes:

```text
runs/m2151_paper_route_current_sim_controlled_comparison_executable_spec_materialization/summary.json
runs/m2151_paper_route_current_sim_controlled_comparison_executable_spec_materialization/executable_task_specs.json
runs/m2151_paper_route_current_sim_controlled_comparison_executable_spec_materialization/executable_task_specs.csv
runs/m2151_paper_route_current_sim_controlled_comparison_executable_spec_materialization/planned_workload.csv
runs/m2151_paper_route_current_sim_controlled_comparison_executable_spec_materialization/profile_matrix.csv
runs/m2151_paper_route_current_sim_controlled_comparison_executable_spec_materialization/materialization_failures.csv
runs/m2151_paper_route_current_sim_controlled_comparison_executable_spec_materialization/aggregate_by_task_family.csv
runs/m2151_paper_route_current_sim_controlled_comparison_executable_spec_materialization/metric_support.csv
runs/m2151_paper_route_current_sim_controlled_comparison_executable_spec_materialization/claim_boundary.csv
runs/m2151_paper_route_current_sim_controlled_comparison_executable_spec_materialization/run_state.json
```

## Claim Boundary

Admissible:

```text
current_sim_controlled_comparison_executable_spec_materialized
```

Blocked:

```text
reset_validity
controller_family_ranking
winner_selection
finite_window_vs_gru_conclusion
paper_level_benchmark_result
level3_self_identification
```

## Next

Immediate next milestone:

```text
m2152-paper-route-current-sim-controlled-comparison-executable-spec-materialization-audit
```

M2152 should audit whether the specs are clean enough to admit reset-validation
command design. It should also record that checkpoint compatibility remains a
later measured-execution blocker, not a reset-validation blocker.
