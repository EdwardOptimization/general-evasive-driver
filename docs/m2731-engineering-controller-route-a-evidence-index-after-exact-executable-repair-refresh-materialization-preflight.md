# M2731 Engineering Controller Route A Evidence Index After Exact-Executable Repair Refresh Materialization Preflight

- status: completed
- result_class: `engineering_controller_route_a_evidence_index_after_exact_executable_repair_refresh_pass`
- summary: `runs/m2731_engineering_controller_route_a_evidence_index_after_exact_executable_repair_refresh/summary.json`
- evidence index: `runs/m2731_engineering_controller_route_a_evidence_index_after_exact_executable_repair_refresh/evidence_index.csv`
- blocker matrix: `runs/m2731_engineering_controller_route_a_evidence_index_after_exact_executable_repair_refresh/blocker_matrix.csv`
- next-action admission rows: `runs/m2731_engineering_controller_route_a_evidence_index_after_exact_executable_repair_refresh/next_action_admission_rows.csv`
- claim boundary rows: `runs/m2731_engineering_controller_route_a_evidence_index_after_exact_executable_repair_refresh/claim_boundary_rows.csv`
- gate matrix: `runs/m2731_engineering_controller_route_a_evidence_index_after_exact_executable_repair_refresh/gate_matrix.csv`
- follow-up manifest: `experiments/manifests/m2732-engineering-controller-route-a-evidence-index-after-exact-executable-repair-refresh-materialization-result-audit.json`
- next: `m2732-engineering-controller-route-a-evidence-index-after-exact-executable-repair-refresh-materialization-result-audit`

## Evidence Index

- evidence rows: 10
- blocker rows: 5
- selected next action: `m2732_route_a_evidence_index_after_exact_executable_repair_result_audit`
- source artifacts reanalyzed only: `true`

## M2728 Diagnostic Boundary

- repair execution rows: 31
- diagnostic success rows: 1
- collision rows: 3
- off_track rows: 27
- negative diagnostic preserved: `true`
- same-surface repair closed by M2730: `true`

## Blockers

- protected mitigation blocker preserved: `true`
- protected rows in success denominator: `false`
- HF3 source dependency paused: `true`

## Actor Boundary

- actor contract P0 72/action 3: `true`
- hidden/oracle actor input detected: `false`
- taxonomy, repair-target, objective-gate, route-decision, and verdict labels actor-visible: `false`

## Claim Boundary

M2731 is an evidence/readiness index over existing artifacts only. It performs no reset, step, rollout, replay, validation, training, PPO, source build, adapter probe, external simulation, ranking, winner selection, promotion, or success-rate computation.

It does not claim repair success, driver performance, validation readiness, validation result, paper-level evidence, finite-window-vs-GRU, current-sim verdict, high-fidelity validation, full ideal driver completion, or self-ID evidence.
