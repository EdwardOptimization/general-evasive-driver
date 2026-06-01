# M2150 Paper-Route Current-Sim Controlled Comparison Executable Spec Materialization Design

- status: completed
- decision: `current_sim_controlled_comparison_executable_spec_materialization_design_admit_implementation`
- manifest: `experiments/manifests/m2150-paper-route-current-sim-controlled-comparison-executable-spec-materialization-design.json`
- reset/rollout/measured execution in M2150: `false`
- policy actions executed in M2150: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- winner selected: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Design Principle

M2148 created a benchmark contract. M2149 correctly blocked direct reset
validation because the contract rows were not executable env specs. M2150
freezes the missing no-rollout step:

```text
benchmark contract -> executable scenario specs -> reset validation -> measured execution
```

Only the first arrow is designed here.

## Materialization Target

M2151 should materialize a small first-pack current-sim benchmark:

```text
task families: 5
specs per family: 8
total executable specs: 40
profile matrix: 8 profiles
planned workload rows: 40 * 8 = 320
```

This is intentionally smaller than a full paper benchmark. Its job is to make
reset validation possible with concrete current-sim specs while preserving the
paper-route claim boundary.

## Input Artifacts

M2151 must read:

```text
configs/paper_route_current_sim_controlled_comparison_benchmark_v0.json
runs/m2148_paper_route_current_sim_controlled_comparison_benchmark_spec_preflight/profile_matrix.csv
runs/m2148_paper_route_current_sim_controlled_comparison_benchmark_spec_preflight/task_family_specs.csv
runs/m2148_paper_route_current_sim_controlled_comparison_benchmark_spec_preflight/metric_support.csv
runs/m2148_paper_route_current_sim_controlled_comparison_benchmark_spec_preflight/claim_boundary.csv
```

Required inherited invariants:

```text
profile_count: 8
task_family_count: 5
forbidden_profile_violation_count: 0
profile_specific_tuning_count: 0
guardrail_violation_count: 0
unsupported_metric_gap_count: 10, explicit and non-silent
```

## Executable Spec Schema

Each executable spec must include:

```text
task_source_id
benchmark_spec_id
task_family
claim_level_target
scenario_source
source_kind
source_reference
source_index
source_seed
eval_seed_override
materialization_semantics
paper_validity_status
generated_proxy_source
profile_specific_tuning
actor_input_contract
controller_family_ranking_claim_made
finite_window_vs_gru_conclusion_made
paper_level_claim_made
level3_self_id_claim_made
metric_gap_policy
env_config
contract_checks
contract_violation_count
```

The `env_config` must satisfy:

```text
history_length >= 1
action_history_mode == full
include_privileged_params == false
wheel_observation_mode == none
obstacle_relative_velocity_mode == zero
obstacle.enabled == true
obstacle.max_sample_attempts >= 200
```

The executable materializer must not change profile configs and must not choose
scenario parameters based on profile outcomes.

## Task Family Quotas

M2151 should materialize:

```text
T1_reactive_emergency_avoidance: 8 specs
T2_delayed_actuator_response: 8 specs
T3_diagnostic_warmup_obstacle_reveal: 8 specs
T4_same_current_different_older_history: 8 specs
T5_terminal_boundary_near_constraint: 8 specs
```

Deterministic `source_seed` rule:

```text
source_seed = 215100 + 100 * task_family_index + source_index
```

Deterministic `eval_seed_override` rule:

```text
eval_seed_override = 215100 + 1000 * task_family_index + source_index
```

This gives stable reset-validation inputs without private tuning.

## Env Template Semantics

M2151 may start from the existing P0-compatible obstacle env template used by
the paper-route profile configs, then override family-level bands.

Family-level intent:

```text
T1_reactive_emergency_avoidance:
  immediate or short-notice obstacle, moderate hidden dynamics, ordinary-to-near-boundary difficulty.

T2_delayed_actuator_response:
  higher actuator_tau scale, short-to-medium notice, delayed/weak response emphasis.

T3_diagnostic_warmup_obstacle_reveal:
  obstacle reveal after warmup, hidden dynamics randomized before reveal.

T4_same_current_different_older_history:
  pair-group metadata for older-history ambiguity; current/recent alignment remains a future intervention gate.

T5_terminal_boundary_near_constraint:
  low-to-mid friction, short critical decision window, near-boundary obstacle placement.
```

T4/T5 mechanism metrics remain deferred unless later instrumentation and
intervention execution explicitly support them. M2151 should preserve the
metadata hooks, not pretend to solve the mechanism tests.

## Planned Workload Mapping

Each executable spec must be crossed with all 8 profiles:

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

Each planned workload row must include:

```text
workload_id
task_source_id
profile_name
profile_level
task_family
history_representation
history_window_steps
reset_or_truncated_control
environment_reset_scheduled=false
environment_rollout_scheduled=false
training_scheduled=false
profile_specific_tuning=false
controller_family_ranking_claim_made=false
finite_window_vs_gru_conclusion_made=false
paper_level_claim_made=false
level3_self_id_claim_made=false
```

## Planned Outputs

M2151 must write:

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

## Pass Gates

M2151 passes only if:

```text
result_class == current_sim_controlled_comparison_executable_spec_materialization_pass
executable_spec_count == 40
task_family_count == 5
profile_count == 8
planned_workload_row_count == 320
materialization_failure_count == 0
contract_violation_count == 0
forbidden_key_violation_count == 0
profile_specific_tuning_count == 0
guardrail_violation_count == 0
```

No reset-validity, measured-performance, ranking, paper, finite-window-vs-GRU,
or self-ID claim is allowed.

## Next

Immediate next milestone:

```text
m2151-paper-route-current-sim-controlled-comparison-executable-spec-materialization-implementation
```
