# M3148 Speed-Envelope Action-Delta Coverage Diagnostic Result Audit

## Summary

- status: completed
- decision: `accept_m3147_artifacts_reject_missing_overlay_hypothesis_route_to_m3149_delta_effectiveness_synthesis`
- result class: `accept_m3147_complete_claim_safe_action_delta_coverage_diagnostic`
- source summary: `runs/m3147_engineering_controller_active_safety_driver_residual_trajectory_timing_speed_envelope_action_delta_coverage_diagnostic_materialization_preflight/summary.json`
- M3147 status pass: true
- M3147 gate matrix pass: true
- required artifacts present: true
- follow-up route: M3149 delta-effectiveness and saturation synthesis before any new repair implementation.

## Artifact Audit

M3147 is accepted as complete and claim-safe:

- residual action-delta plan rows: 7/7
- action-delta step trace rows: 256
- action-delta coverage rows: 7
- action-delta trace failure rows: 0
- terminal collisions: 5
- terminal offtracks: 2
- terminal successes: 0
- gate matrix rows: 33
- claim boundary rows: 23
- runtime driver id: `m3142_residual_trajectory_timing_speed_envelope`
- fallback policy id: `m3103_v4_v2_fallback_no_regression_hard_safety_direct_action_repair`
- output contract: obs72 current-frame actor-visible input to direct `[steer, throttle, brake]`
- runtime base policy required: false
- checkpoint model required: false
- recurrent hidden state required: false

The artifacts are suitable as diagnostic input only. They do not provide validation, repair-success, driver-performance, current-sim verdict, robustness, feasibility-proof, high-fidelity, paper, full-driver, or self-ID evidence.

## Coverage Audit

M3147 falsifies the missing-overlay explanation:

- overlay-any episode count: 7/7
- overlay-never episode count: 0/7
- zero-delta episode count: 0/7
- mean overlay active fraction: 0.9784557547715442
- max overlay alpha: 0.7935389639658202
- max action delta abs: 0.44438183307647705

Coverage labels:

- `delta_present_outcome_unresolved`: 4
- `candidate_action_saturation_may_limit_delta_effect`: 2
- `collision_terminal_window_delta_low`: 1

This means M3142 was not plateauing because the overlay failed to activate. The candidate differs from the M3105/M3103 fallback early on all residual rows, yet the same 5 collision and 2 offtrack outcomes remain. The remaining question is therefore delta effectiveness: whether the bounded deltas are too small, are neutralized by action saturation, arrive in the wrong channel mix, or cannot change the residual trajectories under the current direct-action architecture.

## Claim Boundary

Rejected claims:

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

M3148 accepts M3147 as a complete action-delta coverage diagnostic. It rejects both promotion and direct gain continuation. The next aligned step is M3149 synthesis: classify the action-delta effectiveness and saturation evidence, preserve M3105/M3103 as incumbent, and select exactly one claim-safe route before any new implementation or measurement.
