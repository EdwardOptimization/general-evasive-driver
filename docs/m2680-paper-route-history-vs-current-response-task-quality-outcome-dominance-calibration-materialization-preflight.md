# M2680 Paper Route History Vs Current Response Task Quality Outcome Dominance Calibration Materialization Preflight

## Summary

- status: completed
- result_class: `paper_route_history_vs_current_response_task_quality_outcome_dominance_calibration_pass`
- generated_at_utc: `20260604T150252Z`
- manifest: `experiments/manifests/m2680-paper-route-history-vs-current-response-task-quality-outcome-dominance-calibration-materialization-preflight.json`
- source M2677 status pass: True
- summary: `runs/m2680_paper_route_history_vs_current_response_task_quality_outcome_dominance_calibration/summary.json`
- spec rows: `runs/m2680_paper_route_history_vs_current_response_task_quality_outcome_dominance_calibration/spec_outcome_dominance_rows.csv`
- profile rows: `runs/m2680_paper_route_history_vs_current_response_task_quality_outcome_dominance_calibration/profile_outcome_dominance_rows.csv`
- task-family rows: `runs/m2680_paper_route_history_vs_current_response_task_quality_outcome_dominance_calibration/task_family_outcome_dominance_rows.csv`
- comparison interpretability rows: `runs/m2680_paper_route_history_vs_current_response_task_quality_outcome_dominance_calibration/comparison_interpretability_rows.csv`
- calibration gap rows: `runs/m2680_paper_route_history_vs_current_response_task_quality_outcome_dominance_calibration/calibration_gap_rows.csv`
- claim boundary rows: `runs/m2680_paper_route_history_vs_current_response_task_quality_outcome_dominance_calibration/claim_boundary_rows.csv`
- gate matrix: `runs/m2680_paper_route_history_vs_current_response_task_quality_outcome_dominance_calibration/gate_matrix.csv`
- run state: `runs/m2680_paper_route_history_vs_current_response_task_quality_outcome_dominance_calibration/run_state.json`
- follow-up manifest: `experiments/manifests/m2681-paper-route-history-vs-current-response-task-quality-outcome-dominance-calibration-result-audit.json`
- next: `m2681-paper-route-history-vs-current-response-task-quality-outcome-dominance-calibration-result-audit`

## Materialized Calibration Surface

- episode rows consumed: 864 / 864
- profiles covered: 12 / 12
- specs covered: 72 / 72
- task families covered: 2
- comparison rows covered: 11 / 11
- spec outcome-dominance rows: 72
- profile outcome-dominance rows: 12
- task-family outcome-dominance rows: 2
- calibration gap rows: 9
- selected metrics finite: True

## Blockers Recorded

- success count: 35
- collision count: 35
- offtrack outcome count: 793
- offtrack termination count: 794
- global outcome dominance blocked: True
- hidden-dynamics bucket missing: True
- spec dominance blocked rows: 68
- profile dominance blocked rows: 9
- task-family dominance blocked rows: 2
- comparison rows interpretable for ranking: 0
- comparison rows allowed for synthesis only: 11

## Guardrails

- environment reset started: False
- environment rollout started: False
- policy action executed: False
- measured validation started: False
- training started: False
- replay started: False
- PPO used: False
- private holdout used: False
- profile-specific tuning: False
- actor input contract changed: False
- hidden/oracle actor input detected: False
- controller-family ranking claim made: False
- success-rate verdict claim made: False
- paper-level claim made: False

## Claim Boundary

Allowed:

```text
No-rollout calibration materialization and diagnostic blocker localization from existing M2677 rows.
```

Rejected:

```text
controller-family ranking, winner selection, checkpoint promotion, success-rate verdict, comparison-delta verdict, driver performance, validation readiness or result, paper-level evidence, finite-window-vs-GRU result, current-response sufficiency result, current-sim verdict, high-fidelity validation, full ideal driver completion, or level3 self-identification
```

M2680 passes only if the calibration artifacts are complete and the
claim boundary remains clean. It does not make M2677 interpretable
as controller-family ranking, paper evidence, current-sim verdict,
finite-window-vs-GRU evidence, current-response sufficiency, high-
fidelity validation, full ideal driver completion, or self-ID.
