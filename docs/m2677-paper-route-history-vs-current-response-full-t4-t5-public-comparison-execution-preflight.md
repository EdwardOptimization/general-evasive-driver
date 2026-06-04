# M2677 Paper Route History Vs Current Response Full T4/T5 Public Comparison Execution Preflight

## Summary

- status: completed
- result_class: `paper_route_history_vs_current_response_full_t4_t5_public_comparison_execution_preflight_pass`
- generated_at_utc: `20260604T142821Z`
- manifest: `experiments/manifests/m2677-paper-route-history-vs-current-response-full-t4-t5-public-comparison-execution-preflight.json`
- summary: `runs/m2677_paper_route_history_vs_current_response_full_t4_t5_public_comparison_execution_preflight/summary.json`
- full rollout runner summary: `runs/m2677_paper_route_history_vs_current_response_full_t4_t5_public_comparison_execution_preflight/full_rollout_execution_summary.json`
- episode rows: `runs/m2677_paper_route_history_vs_current_response_full_t4_t5_public_comparison_execution_preflight/episode_rows.csv`
- profile aggregate: `runs/m2677_paper_route_history_vs_current_response_full_t4_t5_public_comparison_execution_preflight/profile_aggregate.csv`
- spec aggregate: `runs/m2677_paper_route_history_vs_current_response_full_t4_t5_public_comparison_execution_preflight/spec_aggregate.csv`
- stratum aggregate: `runs/m2677_paper_route_history_vs_current_response_full_t4_t5_public_comparison_execution_preflight/stratum_aggregate.csv`
- comparison aggregate: `runs/m2677_paper_route_history_vs_current_response_full_t4_t5_public_comparison_execution_preflight/comparison_aggregate.csv`
- outcome aggregate: `runs/m2677_paper_route_history_vs_current_response_full_t4_t5_public_comparison_execution_preflight/outcome_aggregate.csv`
- termination aggregate: `runs/m2677_paper_route_history_vs_current_response_full_t4_t5_public_comparison_execution_preflight/termination_reason_aggregate.csv`
- profile outcome aggregate: `runs/m2677_paper_route_history_vs_current_response_full_t4_t5_public_comparison_execution_preflight/profile_outcome_aggregate.csv`
- hidden-dynamics aggregate: `runs/m2677_paper_route_history_vs_current_response_full_t4_t5_public_comparison_execution_preflight/hidden_dynamics_aggregate.csv`
- runtime-enforcement join rows: `runs/m2677_paper_route_history_vs_current_response_full_t4_t5_public_comparison_execution_preflight/runtime_enforcement_join_rows.csv`
- claim boundary rows: `runs/m2677_paper_route_history_vs_current_response_full_t4_t5_public_comparison_execution_preflight/claim_boundary_rows.csv`
- gate matrix: `runs/m2677_paper_route_history_vs_current_response_full_t4_t5_public_comparison_execution_preflight/gate_matrix.csv`
- failure rows: `runs/m2677_paper_route_history_vs_current_response_full_t4_t5_public_comparison_execution_preflight/failure_rows.csv`
- run state: `runs/m2677_paper_route_history_vs_current_response_full_t4_t5_public_comparison_execution_preflight/run_state.json`
- follow-up manifest: `experiments/manifests/m2678-paper-route-history-vs-current-response-full-t4-t5-public-comparison-execution-result-audit.json`
- next: `m2678-paper-route-history-vs-current-response-full-t4-t5-public-comparison-execution-result-audit`

## Full Public Execution

- episode rows: 864 / 864
- profiles executed: 12 / 12
- public specs executed: 72 / 72
- failure rows: 0
- profile aggregate rows: 12
- spec aggregate rows: 72
- stratum aggregate rows: 5
- comparison aggregate rows: 11
- outcome aggregate rows: 4
- termination aggregate rows: 4
- hidden-dynamics aggregate rows: 0
- selected metrics finite: True

## Runtime Join

- M2673 status pass: True
- M2675 status pass: True
- M1690 workload status pass: True
- runtime join rows: 12
- runtime join rows pass: True
- protocol controller families mapped: 9 / 9
- current-tiled runtime profile count: 4
- current-tiled runtime observed: True
- reset/truncated runtime profile count: 1
- reset/truncated policy routing ok: True

## Guardrails

- environment rollout run: True
- full public policy rollout run: True
- policy rollout allowed: True
- measured validation run: False
- training run: False
- replay run: False
- ppo run: False
- private holdout used: False
- profile-specific tuning: False
- actor/action boundary: P0 observation multiple action 3 preserved: True
- hidden/oracle actor input detected: False
- diagnostic success-rate metric recorded: True
- diagnostic comparison-delta metric recorded: True
- success-rate verdict claim made: False
- comparison-delta verdict claim made: False

## Claim Boundary

Allowed:

```text
Full public T4/T5 comparison execution preflight data and diagnostic metrics only.
```

Rejected:

```text
controller-family ranking, winner selection, checkpoint promotion, success-rate verdict, driver performance, validation readiness or result, paper-level evidence, finite-window-vs-GRU result, current-response sufficiency result, current-sim verdict, high-fidelity validation, full ideal driver completion, or level3 self-identification
```

M2677 executes the public T4/T5 workload for diagnostic comparison
rows only. The aggregate success-rate columns and comparison delta
columns in the output are diagnostic metrics, not success-rate
verdicts, controller-family rankings, paper evidence,
finite-window-vs-GRU conclusions, current-response sufficiency
results, current-sim verdicts, high-fidelity validation, full
ideal driver completion, or level3 self-ID evidence.
