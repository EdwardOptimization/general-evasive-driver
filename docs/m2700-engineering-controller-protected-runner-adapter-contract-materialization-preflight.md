# M2700 Engineering Controller Protected Runner Adapter Contract Materialization Preflight

## Summary

- status: completed
- result class: `engineering_controller_protected_runner_adapter_contract_materialization_pass`
- adapter candidate mapping rows: 12
- adapter rejection rows: 0
- adapter traceability rows: 160
- protected targets accounted: 10/10
- M1690 exact workload matches preserved from source: 0
- gate matrix pass: True
- next: `m2701-engineering-controller-protected-runner-adapter-contract-materialization-result-audit`

M2700 materializes the protected runner adapter contract admitted by M2699. It
maps or explicitly rejects every M2697 protected workload candidate while
preserving the M2698 finding that these rows are adapter-contract materialization
rows, not protected execution admissions or performance evidence.

## Materialization Result

```text
M2697 protected runner specs: 12
M2697 protected workload candidates: 12
adapter contract materialized rows: 12
adapter rejection rows: 0
adapter execution admitted rows: 0
M1690 exact workload matches: 0
all candidates mapped or rejected: True
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
protected runner adapter contract rows were materialized or rejected with explicit reasons
```

Rejected claims:

```text
repair success, driver performance, validation readiness or result, protected mitigation preservation result, controller-family ranking, winner selection, checkpoint promotion, success-rate verdict, paper evidence, finite-window-vs-GRU conclusion, current-response sufficiency, current-sim verdict, high-fidelity validation readiness or result, full ideal driver completion, or level3 self-identification
```

## Artifacts

- summary: `runs/m2700_engineering_controller_protected_runner_adapter_contract/summary.json`
- adapter_input_source_rows: `runs/m2700_engineering_controller_protected_runner_adapter_contract/adapter_input_source_rows.csv`
- adapter_candidate_mapping_rows: `runs/m2700_engineering_controller_protected_runner_adapter_contract/adapter_candidate_mapping_rows.csv`
- adapter_rejection_rows: `runs/m2700_engineering_controller_protected_runner_adapter_contract/adapter_rejection_rows.csv`
- adapter_traceability_rows: `runs/m2700_engineering_controller_protected_runner_adapter_contract/adapter_traceability_rows.csv`
- actor_contract_guard_rows: `runs/m2700_engineering_controller_protected_runner_adapter_contract/actor_contract_guard_rows.csv`
- claim_boundary_rows: `runs/m2700_engineering_controller_protected_runner_adapter_contract/claim_boundary_rows.csv`
- gate_matrix: `runs/m2700_engineering_controller_protected_runner_adapter_contract/gate_matrix.csv`
- doc: `docs/m2700-engineering-controller-protected-runner-adapter-contract-materialization-preflight.md`
