# M2703 Engineering Controller Protected Runner Execution Admission Materialization Preflight

## Summary

- status: completed
- result class: `engineering_controller_protected_runner_execution_admission_materialization_pass`
- execution-admission candidate rows: 12
- execution-admission rejection rows: 12
- execution-admission traceability rows: 160
- execution-admitted rows: 0
- blocked no-current-M1690 rows: 12
- protected targets accounted: 10/10
- M1690 exact workload matches preserved from source: 0
- gate matrix pass: True
- next: `m2704-engineering-controller-protected-runner-execution-admission-materialization-result-audit`

M2703 materializes the protected runner execution-admission classification
surface admitted by M2702. It classifies every M2700 adapter candidate while
preserving the M2701 finding that adapter rows are not protected execution
rows, validation rows, or performance evidence.

## Materialization Result

```text
M2700 adapter candidate rows: 12
execution-admission candidates: 12
execution-admitted rows: 0
blocked no-current-M1690 rows: 12
execution-admission rejection rows: 12
M1690 exact workload matches: 0
all candidates classified: True
all non-admitted rows have rejection rows: True
all protected targets accounted: True
```

## Actor Boundary

```text
observation_shape: 72
action_shape: 3
hidden_oracle_actor_input_detected: False
target_labels_actor_visible: False
protected_rows_in_success_denominator: False
```

## Claim Boundary

Allowed claim:

```text
protected runner execution-admission rows were materialized as admitted, rejected, or blocked with explicit reasons
```

Rejected claims:

```text
protected execution result, repair success, driver performance, validation readiness or result, protected mitigation preservation result, controller-family ranking, winner selection, checkpoint promotion, success-rate verdict, paper evidence, finite-window-vs-GRU conclusion, current-response sufficiency, current-sim verdict, high-fidelity validation readiness or result, full ideal driver completion, or level3 self-identification
```

## Artifacts

- summary: `runs/m2703_engineering_controller_protected_runner_execution_admission/summary.json`
- execution_admission_input_source_rows: `runs/m2703_engineering_controller_protected_runner_execution_admission/execution_admission_input_source_rows.csv`
- execution_admission_candidate_rows: `runs/m2703_engineering_controller_protected_runner_execution_admission/execution_admission_candidate_rows.csv`
- execution_admission_rejection_rows: `runs/m2703_engineering_controller_protected_runner_execution_admission/execution_admission_rejection_rows.csv`
- execution_admission_traceability_rows: `runs/m2703_engineering_controller_protected_runner_execution_admission/execution_admission_traceability_rows.csv`
- actor_contract_guard_rows: `runs/m2703_engineering_controller_protected_runner_execution_admission/actor_contract_guard_rows.csv`
- claim_boundary_rows: `runs/m2703_engineering_controller_protected_runner_execution_admission/claim_boundary_rows.csv`
- gate_matrix: `runs/m2703_engineering_controller_protected_runner_execution_admission/gate_matrix.csv`
- doc: `docs/m2703-engineering-controller-protected-runner-execution-admission-materialization-preflight.md`
