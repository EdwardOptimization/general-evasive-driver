# M2816 Engineering Controller Route A Post-Action-Response Recoverability-Window Instrumented Bounded Execution Preflight

- status: completed
- result_class: `engineering_controller_route_a_post_action_response_recoverability_window_instrumented_bounded_execution_preflight_pass`
- summary: `runs/m2816_engineering_controller_route_a_post_action_response_recoverability_window_instrumented_bounded_execution_preflight/summary.json`
- recoverability rows: `runs/m2816_engineering_controller_route_a_post_action_response_recoverability_window_instrumented_bounded_execution_preflight/recoverability_window_rows.csv`
- post-offtrack action-response rows: `runs/m2816_engineering_controller_route_a_post_action_response_recoverability_window_instrumented_bounded_execution_preflight/post_offtrack_action_response_rows.csv`
- success/offtrack contrast rows: `runs/m2816_engineering_controller_route_a_post_action_response_recoverability_window_instrumented_bounded_execution_preflight/success_offtrack_contrast_rows.csv`
- guardrail context rows: `runs/m2816_engineering_controller_route_a_post_action_response_recoverability_window_instrumented_bounded_execution_preflight/guardrail_context_rows.csv`
- actor contract guard rows: `runs/m2816_engineering_controller_route_a_post_action_response_recoverability_window_instrumented_bounded_execution_preflight/actor_contract_guard_rows.csv`
- claim boundary rows: `runs/m2816_engineering_controller_route_a_post_action_response_recoverability_window_instrumented_bounded_execution_preflight/claim_boundary_rows.csv`
- gate matrix: `runs/m2816_engineering_controller_route_a_post_action_response_recoverability_window_instrumented_bounded_execution_preflight/gate_matrix.csv`
- follow-up manifest: `experiments/manifests/m2817-engineering-controller-route-a-post-action-response-recoverability-window-instrumented-bounded-execution-result-audit.json`
- next: `m2817-engineering-controller-route-a-post-action-response-recoverability-window-instrumented-bounded-execution-result-audit`

## Fixed Row Accounting

- fixed mechanism rows: 12
- source offtrack rows: 10
- source success rows: 2
- source collision rows: 0
- instrumented execution rows: 12
- execution failures: 0
- diagnostic terminations: {'': 6, 'obstacle_collision': 1, 'off_track': 5}

## Recoverability Diagnostics

- horizon steps: 180
- recoverability window steps: 40
- soft-offtrack metric enabled: `true`
- soft-offtrack tolerance m: 1.0
- post-event available rows: 7
- recoverability available rows: 0
- recoverability success rows: 0

## Guardrails

- guardrail context rows: 44
- guardrails not executed: `true`
- protected rows in success denominator: `false`

## Actor Boundary

- actor contract P0 72/action 3: `true`
- hidden/oracle actor input detected: `false`
- action-response, recoverability, stress-axis, source-edge, success/progress, and verdict labels actor-visible: `false`

## Claim Boundary

M2816 Route A post-action-response recoverability-window instrumented bounded execution preflight only; fixed M2813/M2807 rows may be rerun with evaluator-only soft-offtrack metric instrumentation to materialize recoverability-window and post-offtrack action-response diagnostics. No replay, validation, training, PPO, repair, source build, adapter probe, external simulation, ranking, winner selection, promotion, success-rate verdict, repair-success, driver-performance, paper, finite-window-vs-GRU, current-sim, high-fidelity validation, full ideal driver, or self-ID claim is made

Forbidden interpretation:

repair success, driver performance, validation readiness or result, controller ranking, action-response ranking, recoverability ranking, source-family ranking, task-family ranking, stress-axis ranking, profile ranking, winner selection, checkpoint promotion, success-rate verdict, paper evidence, finite-window-vs-GRU conclusion, current-sim verdict, high-fidelity validation readiness or result, full ideal driver completion, or level3 self-identification
