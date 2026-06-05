# M2813 Engineering Controller Route A Post-Clearance Negative Non-Same-Repair Offtrack-Containment Action-Response Mechanism Panel Materialization Preflight

- status: completed
- result_class: `engineering_controller_route_a_post_clearance_negative_non_same_repair_offtrack_containment_action_response_mechanism_panel_materialization_pass`
- summary: `runs/m2813_engineering_controller_route_a_post_clearance_negative_non_same_repair_offtrack_containment_action_response_mechanism_panel/summary.json`
- action-response mechanism rows: `runs/m2813_engineering_controller_route_a_post_clearance_negative_non_same_repair_offtrack_containment_action_response_mechanism_panel/action_response_mechanism_rows.csv`
- success/offtrack contrast rows: `runs/m2813_engineering_controller_route_a_post_clearance_negative_non_same_repair_offtrack_containment_action_response_mechanism_panel/success_offtrack_contrast_rows.csv`
- guardrail context rows: `runs/m2813_engineering_controller_route_a_post_clearance_negative_non_same_repair_offtrack_containment_action_response_mechanism_panel/guardrail_context_rows.csv`
- actor contract guard rows: `runs/m2813_engineering_controller_route_a_post_clearance_negative_non_same_repair_offtrack_containment_action_response_mechanism_panel/actor_contract_guard_rows.csv`
- claim boundary rows: `runs/m2813_engineering_controller_route_a_post_clearance_negative_non_same_repair_offtrack_containment_action_response_mechanism_panel/claim_boundary_rows.csv`
- gate matrix: `runs/m2813_engineering_controller_route_a_post_clearance_negative_non_same_repair_offtrack_containment_action_response_mechanism_panel/gate_matrix.csv`
- follow-up manifest: `experiments/manifests/m2814-engineering-controller-route-a-post-clearance-negative-non-same-repair-cross-axis-offtrack-containment-action-response-mechanism-panel-materialization-result-audit.json`
- next: `m2814-engineering-controller-route-a-post-clearance-negative-non-same-repair-cross-axis-offtrack-containment-action-response-mechanism-panel-materialization-result-audit`

## Mechanism Rows

- action-response mechanism rows: 12
- offtrack mechanism rows: 10
- success obstacle-pass mechanism rows: 2
- collision mechanism rows: 0
- success/offtrack contrast rows: 2
- action-response metrics available: `true`
- offtrack timing rows: 10
- recoverability available rows: 0

## Guardrails

- guardrail context rows: 44
- guardrails not executed: `true`
- protected rows in success denominator: `false`

## Actor Boundary

- actor contract P0 72/action 3: `true`
- hidden/oracle actor input detected: `false`
- action-response, stress-axis, source-edge, success/progress, and verdict labels actor-visible: `false`

## Claim Boundary

M2813 is no-rollout action-response mechanism materialization from existing artifacts only. It performs no reset, step, policy action, rollout, replay, validation, training, PPO, source build, adapter probe, external simulation, ranking, winner selection, promotion, or success-rate computation.

It does not claim repair success, driver performance, validation readiness, validation result, paper-level evidence, finite-window-vs-GRU, current-sim verdict, high-fidelity validation, full ideal driver completion, or self-ID evidence.
