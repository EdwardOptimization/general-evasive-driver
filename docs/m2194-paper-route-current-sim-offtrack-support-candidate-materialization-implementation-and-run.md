# M2194 Paper-Route Current-Sim Offtrack-Support Candidate Materialization Implementation And Run

- status: completed
- decision: `current_sim_offtrack_support_candidate_materialization_pass_route_to_result_audit`
- manifest: `experiments/manifests/m2194-paper-route-current-sim-offtrack-support-candidate-materialization-implementation-and-run.json`
- implementation: `src/autodrift/paper_route_current_sim_offtrack_support_candidate_materialization.py`
- focused tests: `2 passed`
- summary: `runs/m2194_paper_route_current_sim_offtrack_support_candidate_materialization/summary.json`
- reset in M2194: `false`
- measured execution in M2194: `false`
- policy action executed: `false`
- controller-family ranking claim made: `false`
- winner selected: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Command

```bash
PYTHONPATH=src python -m autodrift.paper_route_current_sim_offtrack_support_candidate_materialization \
  --candidate-config configs/paper_route_current_sim_task_quality_offtrack_support_repair_candidates_v0.json \
  --executable-task-specs runs/m2151_paper_route_current_sim_controlled_comparison_executable_spec_materialization/executable_task_specs.json \
  --output-dir runs/m2194_paper_route_current_sim_offtrack_support_candidate_materialization
```

## Result

```text
result_class: current_sim_offtrack_support_candidate_materialization_pass
candidate_count: 288
repaired_executable_spec_count: 288
expected_repaired_executable_spec_count: 288
planned_workload_row_count: 2304
expected_planned_workload_row_count: 2304
profile_count: 8
materialization_failure_count: 0
contract_violation_count: 0
forbidden_key_violation_count: 0
guardrail_violation_count: 0
profile_specific_tuning_count: 0
actor_input_contract_change_count: 0
```

Axis counts:

```text
diagnostic_warmup_support_ladder: 32
offtrack_saturation_relief: 96
older_history_ambiguity_support_ladder: 64
positive_support_preservation: 32
terminal_boundary_support_ladder: 64
```

Split counts:

```text
public_debug: 176
public_gate: 112
```

Task family counts:

```text
T1_reactive_emergency_avoidance: 24
T2_delayed_actuator_response: 30
T3_diagnostic_warmup_obstacle_reveal: 66
T4_same_current_different_older_history: 70
T5_terminal_boundary_near_constraint: 98
```

## Artifacts

```text
runs/m2194_paper_route_current_sim_offtrack_support_candidate_materialization/summary.json
runs/m2194_paper_route_current_sim_offtrack_support_candidate_materialization/repaired_executable_task_specs.json
runs/m2194_paper_route_current_sim_offtrack_support_candidate_materialization/repaired_executable_task_specs.csv
runs/m2194_paper_route_current_sim_offtrack_support_candidate_materialization/planned_workload.csv
runs/m2194_paper_route_current_sim_offtrack_support_candidate_materialization/materialization_rows.csv
runs/m2194_paper_route_current_sim_offtrack_support_candidate_materialization/materialization_failures.csv
runs/m2194_paper_route_current_sim_offtrack_support_candidate_materialization/claim_boundary.csv
runs/m2194_paper_route_current_sim_offtrack_support_candidate_materialization/run_state.json
```

## Interpretation

M2194 creates an executable repaired task panel from the audited M2190 candidate
artifact. It is a no-rollout materialization pass: no environment reset, no
policy action, no measured execution, and no controller comparison occurred.

Allowed claim:

```text
The project now has 288 repaired executable current-sim support tasks and 2304
planned profile workload rows ready for result audit.
```

Still blocked:

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

M2195 must audit this materialization result before any reset-validation command
design. If M2195 passes, the next route is reset-validation command design over
the repaired executable task specs.
