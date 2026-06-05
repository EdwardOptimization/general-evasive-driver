# M2734 Engineering Controller Route A Post-Negative Diagnostic Source-Diverse Closed-Loop Evidence Surface Materialization Preflight

- status: completed
- result_class: `engineering_controller_route_a_post_negative_diagnostic_source_diverse_closed_loop_evidence_surface_materialization_pass`
- summary: `runs/m2734_engineering_controller_route_a_post_negative_diagnostic_source_diverse_closed_loop_evidence_surface/summary.json`
- input source rows: `runs/m2734_engineering_controller_route_a_post_negative_diagnostic_source_diverse_closed_loop_evidence_surface/input_source_rows.csv`
- evidence surface candidate rows: `runs/m2734_engineering_controller_route_a_post_negative_diagnostic_source_diverse_closed_loop_evidence_surface/evidence_surface_candidate_rows.csv`
- source diversity bucket rows: `runs/m2734_engineering_controller_route_a_post_negative_diagnostic_source_diverse_closed_loop_evidence_surface/source_diversity_bucket_rows.csv`
- blocked surface rows: `runs/m2734_engineering_controller_route_a_post_negative_diagnostic_source_diverse_closed_loop_evidence_surface/blocked_surface_rows.csv`
- negative diagnostic context rows: `runs/m2734_engineering_controller_route_a_post_negative_diagnostic_source_diverse_closed_loop_evidence_surface/negative_diagnostic_context_rows.csv`
- actor contract guard rows: `runs/m2734_engineering_controller_route_a_post_negative_diagnostic_source_diverse_closed_loop_evidence_surface/actor_contract_guard_rows.csv`
- claim boundary rows: `runs/m2734_engineering_controller_route_a_post_negative_diagnostic_source_diverse_closed_loop_evidence_surface/claim_boundary_rows.csv`
- gate matrix: `runs/m2734_engineering_controller_route_a_post_negative_diagnostic_source_diverse_closed_loop_evidence_surface/gate_matrix.csv`
- follow-up manifest: `experiments/manifests/m2735-engineering-controller-route-a-post-negative-diagnostic-source-diverse-closed-loop-evidence-surface-materialization-result-audit.json`
- next: `m2735-engineering-controller-route-a-post-negative-diagnostic-source-diverse-closed-loop-evidence-surface-materialization-result-audit`

## Materialized Surface

- input source rows: 6
- candidate rows: 18
- source-diversity families: 2
- source-diversity bucket rows: 2
- blocked surface rows: 12
- M2693 candidate rows: 9
- M2716 candidate rows: 9

## Negative Diagnostic Context

- M2728 context rows: 31
- M2728 diagnostic success rows: 1
- M2728 collision rows: 3
- M2728 off_track rows: 27
- M2728 negative diagnostic preserved: `true`
- same-surface repair execution admitted: `false`

## Blockers And Actor Boundary

- protected mitigation blocker preserved: `true`
- protected rows in success denominator: `false`
- HF3 source dependency paused: `true`
- actor contract P0 72/action 3: `true`
- hidden/oracle actor input detected: `false`
- taxonomy, target, protected, blocker, route-decision, success/progress, and verdict labels actor-visible: `false`

## Claim Boundary

M2734 is materialization from existing artifacts only. It performs no reset, step, rollout, replay, validation, training, PPO, source build, adapter probe, external simulation, ranking, winner selection, promotion, or success-rate computation.

It does not claim repair success, driver performance, validation readiness, validation result, paper-level evidence, finite-window-vs-GRU, current-sim verdict, high-fidelity validation, full ideal driver completion, or self-ID evidence.
