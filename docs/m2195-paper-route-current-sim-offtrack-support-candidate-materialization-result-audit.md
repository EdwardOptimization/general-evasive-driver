# M2195 Paper-Route Current-Sim Offtrack-Support Candidate Materialization Result Audit

- status: completed
- decision: `current_sim_offtrack_support_candidate_materialization_audit_admit_reset_validation_command_design`
- manifest: `experiments/manifests/m2195-paper-route-current-sim-offtrack-support-candidate-materialization-result-audit.json`
- audited summary: `runs/m2194_paper_route_current_sim_offtrack_support_candidate_materialization/summary.json`
- audited specs: `runs/m2194_paper_route_current_sim_offtrack_support_candidate_materialization/repaired_executable_task_specs.json`
- audited workload: `runs/m2194_paper_route_current_sim_offtrack_support_candidate_materialization/planned_workload.csv`
- next manifest: `experiments/manifests/m2196-paper-route-current-sim-offtrack-support-reset-validation-command-design.json`
- reset in M2195: `false`
- measured execution in M2195: `false`
- policy action executed: `false`
- controller-family ranking claim made: `false`
- winner selected: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Audit Checks

M2195 recalculated the main materialization counts from the generated specs and
workload files.

```text
summary_result_class: current_sim_offtrack_support_candidate_materialization_pass
spec_count: 288
workload_count: 2304
contract_violation_count: 0
guardrail_violation_count: 0
materialization_failure_count: 0
```

Task family counts:

```text
T1_reactive_emergency_avoidance: 24
T2_delayed_actuator_response: 30
T3_diagnostic_warmup_obstacle_reveal: 66
T4_same_current_different_older_history: 70
T5_terminal_boundary_near_constraint: 98
```

Profile workload counts:

```text
L0_current_masked: 288
L1_one_step: 288
L2_window_13: 288
L2_window_25: 288
L2_window_50: 288
L2_window_100: 288
L3_online_gru: 288
L3_reset_control: 288
```

Candidate split counts:

```text
public_debug: 176
public_gate: 112
```

The materialized artifact is clean enough to design reset validation.

## Runner Compatibility Note

The existing current-sim reset validator was written for the original M2151
materialization semantics:

```text
materialization_semantics = current_sim_executable_spec_v0
paper_validity_status = current_sim_executable_candidate_not_reset_validated
```

M2194 repaired specs intentionally use a new materialization semantics:

```text
materialization_semantics = current_sim_offtrack_support_repair_materialization_v0
paper_validity_status = current_sim_offtrack_support_candidate_not_reset_validated
```

Therefore M2196 should not blindly run the old command. It must first design a
reset-validation command or runner extension that accepts the M2194 semantics
without weakening the human-view actor-input contract.

## Interpretation

Allowed claim:

```text
The project has a clean no-rollout repaired executable task panel ready for
reset-validation command design.
```

Blocked claims:

```text
reset validity
measured execution
controller-family ranking
winner selection
finite-window vs GRU verdict
paper-level benchmark evidence
level3 self-identification
```

## Next Step

M2196 must design reset-validation over:

```text
runs/m2194_paper_route_current_sim_offtrack_support_candidate_materialization/repaired_executable_task_specs.json
```

The design must include:

```text
target_spec_count = 288
expected_observation_dim = 72
seed_source_mode = prefer_spec_eval_seed_override
accepted materialization_semantics for M2194
accepted paper_validity_status for M2194
no rollout / no policy-action guardrails
```

If M2196 passes, M2197 can implement or run the compatible reset validation.
