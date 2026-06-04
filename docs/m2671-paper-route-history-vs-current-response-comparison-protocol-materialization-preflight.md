# M2671 Paper Route History Vs Current Response Comparison Protocol Materialization Preflight

## Summary

- status: completed
- result_class: `paper_route_history_vs_current_response_comparison_protocol_materialization_pass`
- generated_at_utc: `20260604T131216Z`
- summary: `runs/m2671_paper_route_history_vs_current_response_comparison_protocol_materialization/summary.json`
- controller family rows: `runs/m2671_paper_route_history_vs_current_response_comparison_protocol_materialization/controller_family_rows.csv`
- task family rows: `runs/m2671_paper_route_history_vs_current_response_comparison_protocol_materialization/task_family_rows.csv`
- fairness gate rows: `runs/m2671_paper_route_history_vs_current_response_comparison_protocol_materialization/fairness_gate_rows.csv`
- claim boundary rows: `runs/m2671_paper_route_history_vs_current_response_comparison_protocol_materialization/claim_boundary_rows.csv`
- gate matrix: `runs/m2671_paper_route_history_vs_current_response_comparison_protocol_materialization/gate_matrix.csv`
- follow-up manifest: `experiments/manifests/m2672-paper-route-history-vs-current-response-comparison-protocol-materialization-result-audit.json`
- next: `m2672-paper-route-history-vs-current-response-comparison-protocol-materialization-result-audit`

## Materialized Protocol

- controller family rows: 9 / 9
- task family rows: 5 / 5
- fairness gate rows: 15
- claim boundary rows: 21
- gate matrix rows: 15
- gate matrix pass: True

## Guardrails

- actor/action boundary: P0 observation 72 action 3
- hidden/oracle actor input detected: False
- private holdout used: False
- current-tiled L2 control present: True
- reset/truncated L3 control present: True

## Claim Boundary

Allowed:

```text
Route B comparison protocol materialization readiness only.
```

Rejected:

```text
driver performance, controller-family ranking, finite-window superiority, GRU superiority, recurrent-belief advantage, level3 self-identification, paper verdict, current-sim verdict, high-fidelity validation result, full ideal driver completion, or promotion evidence
```

M2671 did not execute reset, rollout, replay, validation, training, PPO,
source build, adapter probe, external simulation, ranking, winner
selection, promotion, success-rate verdict computation, driver-performance
measurement, paper verdict, current-sim verdict, high-fidelity validation,
full ideal driver gate, or self-ID verdict.
