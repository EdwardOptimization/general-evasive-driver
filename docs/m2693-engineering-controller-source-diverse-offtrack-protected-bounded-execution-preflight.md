# M2693 Engineering Controller Source Diverse Offtrack Protected Bounded Execution Preflight

## Summary

- status: completed
- result class: `engineering_controller_source_diverse_offtrack_protected_bounded_execution_preflight_pass`
- profile: `L3_online_gru`
- policy subject: `m2655_mitigation_preserving_policy`
- checkpoint: `runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution/checkpoints/m2655_mitigation_preserving_actor_head_repair.pt`
- target panel rows: 19
- off-track executed rows: 9/9
- protected recorded failure rows: 10/10
- accounted target rows: 19/19
- unexpected failure rows: 0
- gate matrix pass: True

## Boundary

M2693 records bounded closed-loop diagnostic data for the current-sim off-track targets and keeps protected mitigation targets outside success denominators. The protected rows are recorded as explicit non-executable target failures when no current runner mapping exists.

Rejected claims:

```text
repair success, driver performance, validation readiness or result, controller-family ranking, winner selection, checkpoint promotion, success-rate verdict, paper evidence, finite-window-vs-GRU conclusion, current-response sufficiency, current-sim verdict, high-fidelity validation readiness or result, full ideal driver completion, or level3 self-identification
```

## Artifacts

- summary: `runs/m2693_engineering_controller_source_diverse_offtrack_protected_bounded_execution_preflight/summary.json`
- target_execution_rows: `runs/m2693_engineering_controller_source_diverse_offtrack_protected_bounded_execution_preflight/target_execution_rows.csv`
- offtrack_target_aggregate: `runs/m2693_engineering_controller_source_diverse_offtrack_protected_bounded_execution_preflight/offtrack_target_aggregate.csv`
- protected_target_aggregate: `runs/m2693_engineering_controller_source_diverse_offtrack_protected_bounded_execution_preflight/protected_target_aggregate.csv`
- source_diversity_aggregate: `runs/m2693_engineering_controller_source_diverse_offtrack_protected_bounded_execution_preflight/source_diversity_aggregate.csv`
- blocker_join_rows: `runs/m2693_engineering_controller_source_diverse_offtrack_protected_bounded_execution_preflight/blocker_join_rows.csv`
- actor_contract_join_rows: `runs/m2693_engineering_controller_source_diverse_offtrack_protected_bounded_execution_preflight/actor_contract_join_rows.csv`
- claim_boundary_rows: `runs/m2693_engineering_controller_source_diverse_offtrack_protected_bounded_execution_preflight/claim_boundary_rows.csv`
- gate_matrix: `runs/m2693_engineering_controller_source_diverse_offtrack_protected_bounded_execution_preflight/gate_matrix.csv`
- failure_rows: `runs/m2693_engineering_controller_source_diverse_offtrack_protected_bounded_execution_preflight/failure_rows.csv`
- run_state: `runs/m2693_engineering_controller_source_diverse_offtrack_protected_bounded_execution_preflight/run_state.json`
- doc: `docs/m2693-engineering-controller-source-diverse-offtrack-protected-bounded-execution-preflight.md`

## Next

- follow-up manifest: `experiments/manifests/m2694-engineering-controller-source-diverse-offtrack-protected-bounded-execution-result-audit.json`
- next: `m2694-engineering-controller-source-diverse-offtrack-protected-bounded-execution-result-audit`
