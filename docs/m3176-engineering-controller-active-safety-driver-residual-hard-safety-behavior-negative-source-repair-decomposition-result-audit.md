# M3176 Behavior-Negative Source Repair Decomposition Result Audit

## Summary

- status: completed
- decision: `accept_m3175_decomposition_route_to_m3177_targeted_actor_visible_trace_ablation_materialization`
- result class: `accept_m3175_complete_claim_safe_route_to_targeted_trace`
- source summary: `runs/m3175_engineering_controller_active_safety_driver_residual_hard_safety_behavior_negative_source_repair_decomposition_materialization_preflight/summary.json`
- M3175 status pass: true
- M3175 gate matrix pass: true
- required artifacts present: true
- selected next route: `m3177-engineering-controller-active-safety-driver-residual-hard-safety-behavior-negative-targeted-trace-ablation-materialization-preflight`

## Artifact Audit

M3175 is accepted as complete and claim-safe:

- regression rows versus M3105: 1
- new collision regression rows: 1
- blocker context rows: 8
- blocker context family counts: collision 6, offtrack 2
- blocker context relation counts: inherited incumbent blockers 7, new collision regression 1
- repair decomposition rows: 4
- contract guard rows: 13
- contract guard rows pass: true
- claim boundary rows: 11
- claim boundary rows pass: true
- follow-up manifest registered: true

M3175 did not run reset, step, rollout, replay, policy action, training, validation, ranking, promotion, or public driver mutation. It preserves M3105/M3103 as incumbent.

## Decomposition Audit

The primary decomposition row is:

- route: `new_collision_regression_actor_visible_ablation_trace`
- source row: `m3082-fresh-panel-0020`
- hard-safety focus: `new_collision_regression_vs_m3105`
- admission decision: `decomposition_admitted_repair_not_admitted`
- next required evidence: per-step actor-visible feature and action-delta ablation trace on the new regression row before implementation
- candidate feature families: speed, obstacle-clearance proxy, edge-urgency proxy, steer damping, throttle drop, brake add
- forbidden runtime inputs: row labels, baseline outcomes, source labels, route labels, outcome labels, progress labels, verdict labels, TTC oracle
- public driver mutation allowed: false

The remaining seven hard-safety blockers are inherited incumbent context, not a justification to mutate the driver before the newly introduced collision regression is isolated and neutralized.

## Claim Boundary

Rejected claims:

- trace-ablation result
- repair implementation
- validation result
- ranking or winner selection
- checkpoint promotion
- driver-performance verdict
- current-sim verdict
- robustness result
- high-fidelity validation result
- paper evidence
- finite-window-vs-GRU conclusion
- full ideal driver completion
- repair success
- feasibility proof
- level3 self-identification

## Decision

M3176 accepts M3175 as a complete behavior-negative decomposition artifact and selects M3177 targeted actor-visible trace-ablation materialization. M3177 may execute only the targeted regression evidence route needed to inspect the M3170 overlay and M3105 incumbent behavior on the new collision regression row, with explicit guard rows preventing row-label, baseline-outcome, route, outcome, progress, verdict, TTC-oracle, or source-label runtime inputs.

M3176 makes no repair-success or performance claim. M3105/M3103 remains the deployable incumbent until a later audited candidate improves same-denominator hard-safety counts without contract violations.
