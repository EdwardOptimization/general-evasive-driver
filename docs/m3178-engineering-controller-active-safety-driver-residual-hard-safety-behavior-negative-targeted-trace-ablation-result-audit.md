# M3178 Behavior-Negative Targeted Trace-Ablation Result Audit

## Summary

- status: completed
- decision: `accept_m3177_trace_ablation_route_to_m3179_steer_delta_regression_guard_materialization`
- result class: `accept_m3177_complete_claim_safe_route_to_steer_delta_guard`
- source summary: `runs/m3177_engineering_controller_active_safety_driver_residual_hard_safety_behavior_negative_targeted_trace_ablation_materialization_preflight/summary.json`
- M3177 status pass: true
- M3177 gate matrix pass: true
- required artifacts present: true
- selected next route: `m3179-engineering-controller-active-safety-driver-residual-hard-safety-steer-delta-regression-guard-materialization-preflight`

## Artifact Audit

M3177 is accepted as complete and claim-safe:

- target regression rows: 1
- target source row: `m3084-measurement-episode-0020`
- target fresh panel row: `m3082-fresh-panel-0020`
- targeted trace rows: 443
- ablation variant rows: 5
- contract guard rows: 19
- contract guard rows pass: true
- claim boundary rows: 12
- claim boundary rows pass: true
- gate matrix rows: 22
- gate matrix pass: true
- follow-up manifest registered: true

M3177 preserved the actor-visible obs72 to direct action3 contract. It did not use row labels, baseline outcomes, source labels, route labels, outcome labels, progress labels, verdict labels, TTC oracle values, hidden oracle inputs, a runtime base policy, a checkpoint model, or recurrent hidden state as actor runtime inputs.

## Trace-Ablation Audit

Same-row replay reproduced the negative measurement exactly:

- M3170 candidate replay: collision failure, 79 steps, clearance margin -0.11747365908727159, return 8.552075899939709
- M3105/M3103 incumbent replay: success obstacle pass, 104 steps, clearance margin 0.2678248895862312, return 46.85998586543357

Actor-visible ablations isolate the regression source:

- `m3177_ablate_steer_delta`: success obstacle pass, 104 steps, clearance margin 0.3194207833891467
- `m3177_ablate_throttle_drop`: collision failure, 78 steps, clearance margin -0.029226224919599364
- `m3177_ablate_brake_add`: collision failure, 78 steps, clearance margin -0.019979813204930474

The accepted interpretation is narrow: the M3170 source-localized overlay's steer delta is implicated on the selected regression row. M3178 does not claim that removing or guarding steer delta is a validated repair across the full denominator. It only admits a materialization preflight for a bounded actor-visible steer-delta regression guard.

## Claim Boundary

Rejected claims:

- repair success
- validation result
- driver-performance verdict
- current-sim verdict
- robustness result
- ranking or winner selection
- checkpoint promotion
- public driver default replacement
- high-fidelity validation result
- paper evidence
- finite-window-vs-GRU conclusion
- full ideal driver completion
- feasibility proof
- level3 self-identification

## Decision

M3178 accepts M3177 as a complete targeted trace-ablation artifact and routes to M3179 steer-delta regression guard materialization. M3179 may only materialize a deterministic actor-visible obs72 to action3 candidate that neutralizes or bounds the M3170 steer overlay source identified by M3177. M3179 may not run validation, broad tuning, ranking, promotion, high-fidelity simulation, or claim repair success.

M3105/M3103 remains the deployable incumbent until a later audited same-denominator measurement improves hard-safety counts without contract violations.
