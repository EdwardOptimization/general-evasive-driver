# M3151 Residual Action-Delta Effectiveness Sensitivity Diagnostic Result Audit

## Summary

- status: completed
- decision: `accept_m3150_artifacts_route_to_m3152_counterfactual_replay_synthesis`
- result class: `accept_m3150_complete_claim_safe_sensitivity_diagnostic`
- source summary: `runs/m3150_engineering_controller_active_safety_driver_residual_action_delta_effectiveness_counterfactual_sensitivity_diagnostic_materialization_preflight/summary.json`
- M3150 status pass: true
- M3150 gate matrix pass: true
- required artifacts present: true
- follow-up route: M3152 counterfactual replay synthesis before any repair implementation.

## Artifact Audit

M3150 is accepted as complete and claim-safe:

- residual effectiveness rows: 7/7
- source M3147 step rows: 256
- sensitivity summary rows: 1
- gate matrix rows: 17
- claim boundary rows: 21
- environment reset run: false
- environment step run: false
- policy rollout run: false
- runtime base policy required: false
- hidden/oracle actor input required: false
- TTC actor input required: false

The artifacts are suitable as no-new-execution diagnostic reanalysis only. They do not provide validation, repair-success, driver-performance, current-sim verdict, robustness, feasibility-proof, high-fidelity, paper, full-driver, or self-ID evidence.

## Sensitivity Audit

M3150 labels:

- `collision_action_saturation_limited`: 2
- `collision_delta_present_counterfactual_needed`: 2
- `collision_terminal_delta_low_headroom_available`: 1
- `offtrack_delta_present_counterfactual_needed`: 1
- `offtrack_steer_delta_low_headroom_available`: 1

Aggregate diagnostic values:

- headroom available rows: 5
- saturation-limited rows: 2
- terminal-delta-low rows: 1
- delta-present counterfactual-needed rows: 3
- mean brake headroom: 0.5090515977569988
- mean throttle-drop headroom: 0.3318724862166813
- mean steer headroom: 0.12711772492953707
- mean candidate saturation fraction: 0.19744602734261155

This accepts the M3150 finding that residual failures are mixed: some rows retain terminal-window headroom, some rows are saturation-limited, and several rows need a controlled counterfactual replay to determine whether stronger or differently mixed action deltas are trajectory-effective. This is not enough to implement a repair directly, because direct gain changes would still target known public residual rows without showing whether the environment is sensitive to those action variants.

## Claim Boundary

Rejected claims:

- new repair implementation
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

M3151 accepts M3150 as a complete no-new-execution sensitivity diagnostic and rejects direct repair continuation. The next aligned step is M3152 synthesis: decide whether to run one bounded counterfactual replay diagnostic that tests a small set of actor-visible action-delta variants on the seven residual rows, or stop the branch if that would overfit or require hidden inputs.
