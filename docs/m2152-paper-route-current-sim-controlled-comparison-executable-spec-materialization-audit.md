# M2152 Paper-Route Current-Sim Controlled Comparison Executable Spec Materialization Audit

- status: completed
- decision: `current_sim_executable_spec_materialization_audit_admit_reset_validation_command_design`
- manifest: `experiments/manifests/m2152-paper-route-current-sim-controlled-comparison-executable-spec-materialization-audit.json`
- audited summary: `runs/m2151_paper_route_current_sim_controlled_comparison_executable_spec_materialization/summary.json`
- reset/rollout/measured execution in M2152: `false`
- policy actions executed in M2152: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- winner selected: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Audit Result

M2151 is a clean no-rollout executable-spec materialization:

```text
result_class: current_sim_controlled_comparison_executable_spec_materialization_pass
executable_spec_count: 40 / 40
task_family_count: 5
profile_count: 8
planned_workload_row_count: 320 / 320
materialization_failure_count: 0
contract_violation_count: 0
forbidden_key_violation_count: 0
profile_specific_tuning_count: 0
guardrail_violation_count: 0
```

Task-family coverage is balanced:

```text
T1_reactive_emergency_avoidance: 8
T2_delayed_actuator_response: 8
T3_diagnostic_warmup_obstacle_reveal: 8
T4_same_current_different_older_history: 8
T5_terminal_boundary_near_constraint: 8
```

The executable env configs satisfy the pre-reset contract checks:

```text
history_length >= 1
action_history_mode == full
include_privileged_params == false
wheel_observation_mode == none
obstacle_relative_velocity_mode == zero
obstacle.enabled == true
obstacle.max_sample_attempts >= 200
```

## Checkpoint Gap

The planned workload rows have empty `checkpoint_path` values and
`checkpoint_required_for_measured_execution=true`.

This is not a reset-validation blocker:

```text
reset validation uses executable env specs only;
measured execution requires checkpoint/profile compatibility later.
```

M2152 therefore records the checkpoint gap as a measured-execution blocker to
handle after reset validation, not as a reason to block reset-validation command
design.

## Claim Boundary

Supported:

```text
M2151 produced a concrete current-sim executable-spec panel and planned workload
artifact suitable for reset-validation command design.
```

Unsupported:

```text
reset validity;
measured execution;
controller-family ranking;
finite-window-vs-GRU verdict;
paper-level benchmark result;
level3 self-identification.
```

## Next Route

M2153 should design a current-sim-specific reset validator command. Existing
validators are close, but the new artifact uses:

```text
materialization_semantics: current_sim_executable_spec_v0
target_executable_spec_count: 40
expected_observation_dim: 72
```

The reset validator should reuse the low-level reset helper where possible, but
must preserve M2151 metadata and claim boundaries.

Immediate next milestone:

```text
m2153-paper-route-current-sim-controlled-comparison-reset-validation-command-design
```
