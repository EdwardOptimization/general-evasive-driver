# M2684 Paper Route History Vs Current Response Task Quality Role Semantics Bounded Subset Execution Preflight

## Summary

- status: completed
- result_class: `paper_route_history_vs_current_response_task_quality_role_semantics_bounded_subset_execution_preflight_pass`
- generated_at_utc: `20260604T155228Z`
- manifest: `experiments/manifests/m2684-paper-route-history-vs-current-response-task-quality-role-semantics-bounded-subset-execution-preflight.json`
- summary: `runs/m2684_paper_route_history_vs_current_response_task_quality_role_semantics_bounded_subset_execution_preflight/summary.json`
- subset rollout runner summary: `runs/m2684_paper_route_history_vs_current_response_task_quality_role_semantics_bounded_subset_execution_preflight/subset_rollout_execution_summary.json`
- episode rows: `runs/m2684_paper_route_history_vs_current_response_task_quality_role_semantics_bounded_subset_execution_preflight/episode_rows.csv`
- profile aggregate: `runs/m2684_paper_route_history_vs_current_response_task_quality_role_semantics_bounded_subset_execution_preflight/profile_aggregate.csv`
- spec aggregate: `runs/m2684_paper_route_history_vs_current_response_task_quality_role_semantics_bounded_subset_execution_preflight/spec_aggregate.csv`
- candidate aggregate: `runs/m2684_paper_route_history_vs_current_response_task_quality_role_semantics_bounded_subset_execution_preflight/candidate_aggregate.csv`
- source-edge aggregate: `runs/m2684_paper_route_history_vs_current_response_task_quality_role_semantics_bounded_subset_execution_preflight/source_edge_aggregate.csv`
- role-semantics aggregate: `runs/m2684_paper_route_history_vs_current_response_task_quality_role_semantics_bounded_subset_execution_preflight/role_semantics_aggregate.csv`
- outcome aggregate: `runs/m2684_paper_route_history_vs_current_response_task_quality_role_semantics_bounded_subset_execution_preflight/outcome_aggregate.csv`
- termination aggregate: `runs/m2684_paper_route_history_vs_current_response_task_quality_role_semantics_bounded_subset_execution_preflight/termination_reason_aggregate.csv`
- runtime-enforcement join rows: `runs/m2684_paper_route_history_vs_current_response_task_quality_role_semantics_bounded_subset_execution_preflight/runtime_enforcement_join_rows.csv`
- claim boundary rows: `runs/m2684_paper_route_history_vs_current_response_task_quality_role_semantics_bounded_subset_execution_preflight/claim_boundary_rows.csv`
- gate matrix: `runs/m2684_paper_route_history_vs_current_response_task_quality_role_semantics_bounded_subset_execution_preflight/gate_matrix.csv`
- failure rows: `runs/m2684_paper_route_history_vs_current_response_task_quality_role_semantics_bounded_subset_execution_preflight/failure_rows.csv`
- run state: `runs/m2684_paper_route_history_vs_current_response_task_quality_role_semantics_bounded_subset_execution_preflight/run_state.json`
- follow-up manifest: `experiments/manifests/m2685-paper-route-history-vs-current-response-task-quality-role-semantics-bounded-subset-execution-result-audit.json`
- next: `m2685-paper-route-history-vs-current-response-task-quality-role-semantics-bounded-subset-execution-result-audit`

## Bounded Execution

- episode rows: 216 / 216
- accounted cells: 216 / 216
- profiles executed: 12 / 12
- subset specs executed: 18 / 18
- candidates executed: 9 / 9
- source-edge aggregate rows: 9
- role-semantics aggregate rows: 2
- failure rows: 0
- selected metrics finite: True
- subset full public matrix expanded: False

## Runtime Join

- M2682 status pass: True
- M2673 status pass: True
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
- bounded subset policy rollout run: True
- policy rollout allowed: True
- measured validation run: False
- training run: False
- replay run: False
- ppo run: False
- private holdout used: False
- profile-specific tuning: False
- actor/action boundary: P0 observation multiple action 3 preserved: True
- hidden/oracle actor input detected: False
- role semantics actor visible: False
- diagnostic success-rate metric recorded: True
- diagnostic role/task-quality metrics recorded: True
- success-rate verdict claim made: False
- comparison-delta verdict claim made: False

## Claim Boundary

Allowed:

```text
M2682 bounded subset execution preflight data and diagnostic role/task-quality metrics only.
```

Rejected:

```text
controller-family ranking, winner selection, checkpoint promotion, success-rate verdict, comparison-delta verdict, driver performance, validation readiness or result, paper-level evidence, finite-window-vs-GRU result, current-response sufficiency result, current-sim verdict, high-fidelity validation, full ideal driver completion, or level3 self-identification
```

M2684 executes only the M2682 proposed subset for diagnostic
closed-loop rows. The success-rate and role/task-quality aggregate
columns are not rankings, controller-family verdicts, paper
evidence, finite-window-vs-GRU conclusions, current-response
sufficiency results, current-sim verdicts, high-fidelity
validation, full ideal driver completion, or level3 self-ID
evidence.
