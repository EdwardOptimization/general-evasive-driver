# M2675 Paper Route History Vs Current Response Bounded Comparison Execution Preflight

## Summary

- status: completed
- result_class: `paper_route_history_vs_current_response_bounded_comparison_execution_preflight_pass`
- generated_at_utc: `20260604T135737Z`
- manifest: `experiments/manifests/m2675-paper-route-history-vs-current-response-bounded-comparison-execution-preflight.json`
- summary: `runs/m2675_paper_route_history_vs_current_response_bounded_comparison_execution_preflight/summary.json`
- measured runner summary: `runs/m2675_paper_route_history_vs_current_response_bounded_comparison_execution_preflight/measured_routing_smoke_summary.json`
- episode rows: `runs/m2675_paper_route_history_vs_current_response_bounded_comparison_execution_preflight/episode_rows.csv`
- profile aggregate: `runs/m2675_paper_route_history_vs_current_response_bounded_comparison_execution_preflight/profile_aggregate.csv`
- spec aggregate: `runs/m2675_paper_route_history_vs_current_response_bounded_comparison_execution_preflight/spec_aggregate.csv`
- runtime-enforcement join rows: `runs/m2675_paper_route_history_vs_current_response_bounded_comparison_execution_preflight/runtime_enforcement_join_rows.csv`
- claim boundary rows: `runs/m2675_paper_route_history_vs_current_response_bounded_comparison_execution_preflight/claim_boundary_rows.csv`
- gate matrix: `runs/m2675_paper_route_history_vs_current_response_bounded_comparison_execution_preflight/gate_matrix.csv`
- follow-up manifest: `experiments/manifests/m2676-paper-route-history-vs-current-response-bounded-comparison-execution-result-audit.json`
- next: `m2676-paper-route-history-vs-current-response-bounded-comparison-execution-result-audit`

## Bounded Execution

- episode rows: 48 / 48
- profiles executed: 12 / 12
- selected specs executed: 4 / 4
- profile aggregate rows: 12
- spec aggregate rows: 4
- selected source families: t4_staged_warmup_capability, t4_actuator_delay_response, t5_near_boundary_warmup, t5_boundary_axis_retarget
- all selected metrics finite: True

## Runtime Join

- M2673 status pass: True
- runtime join rows: 12
- runtime join rows pass: True
- protocol controller families mapped: 9 / 9
- current-tiled runtime profile count: 4
- current-tiled runtime observed: True
- reset/truncated runtime profile count: 1
- reset/truncated policy routing ok: True

## Guardrails

- environment rollout run: True
- bounded policy rollout run: True
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
- success-rate verdict claim made: False

## Claim Boundary

Allowed:

```text
Bounded public comparison execution preflight data and diagnostic metrics only.
```

Rejected:

```text
controller-family ranking, winner selection, checkpoint promotion, success-rate verdict, driver performance, validation readiness or result, paper-level evidence, finite-window-vs-GRU result, current-sim verdict, high-fidelity validation, full ideal driver completion, or level3 self-identification
```

M2675 executes a small public T4/T5 panel for diagnostic comparison
rows only. The aggregate success-rate columns in the output are
diagnostic metrics, not success-rate verdicts, controller-family
rankings, paper evidence, finite-window-vs-GRU conclusions,
current-sim verdicts, high-fidelity validation, full ideal driver
completion, or level3 self-ID evidence.
