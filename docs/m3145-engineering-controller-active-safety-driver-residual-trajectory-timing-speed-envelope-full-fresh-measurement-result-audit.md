# M3145 Residual Trajectory-Timing Speed-Envelope Full-Fresh Measurement Result Audit

## Summary

- status: completed
- decision: `accept_m3144_artifacts_reject_repair_success_classify_speed_envelope_plateau_route_to_m3146_synthesis`
- result class: `accept_m3144_complete_claim_safe_reject_behavior_improvement`
- source summary: `runs/m3144_engineering_controller_active_safety_driver_residual_trajectory_timing_speed_envelope_full_fresh_measurement_preflight/summary.json`
- M3144 status pass: true
- M3144 gate matrix pass: true
- required artifacts present: true
- follow-up route: M3146 plateau synthesis before any new repair branch.

## Artifact Audit

M3144 is accepted as complete and claim-safe:

- scheduled full-fresh rows: 64/64
- measurement episode rows: 64
- measurement failure rows: 0
- same-row comparison rows: 256
- exact seed matches: M3105 64, M3095 64, M3100 64, M3090 64
- runtime driver id: `m3142_residual_trajectory_timing_speed_envelope`
- output contract: obs72 current-frame actor-visible input to direct `[steer, throttle, brake]`
- runtime base policy required: false
- checkpoint model required: false
- recurrent hidden state required: false
- action clip fraction mean: 0.0

The M3144 artifacts are suitable as measurement evidence and audit input only.

## Behavior Audit

M3144 full-fresh measured behavior:

- success: 57/64
- collision: 5/64
- offtrack: 2/64
- speed-too-low: 0/64
- clearance margin mean: 10.987371922358182
- high-sideslip fraction mean: 0.0597859724685691
- lateral RMSE mean: 1.1419228091670726

Same-row deltas:

- vs M3105: success 0, collision 0, offtrack 0, speed-too-low 0
- vs M3095: success 0, collision 0, offtrack 0, speed-too-low 0
- vs M3100: success +2, collision 0, offtrack -1, speed-too-low -1
- vs M3090: success +14, collision 0, offtrack -3, speed-too-low -11

This is a plateau against the current M3105/M3095 incumbent. The speed-envelope candidate preserves the incumbent no-regression counts, but it does not reduce the residual 5 collision and 2 offtrack blockers. The small clearance mean delta versus M3105 is not enough to claim behavior improvement because hard-safety outcome counts remain unchanged and return is slightly lower.

## Claim Boundary

Rejected claims:

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

M3145 accepts M3144 as a complete full-fresh measurement artifact and rejects promotion or repair-success interpretation. The residual trajectory-timing speed-envelope branch has produced no same-denominator hard-safety improvement over M3105.

The next step is M3146 synthesis: classify the speed-envelope plateau, preserve M3105/M3103 as the deployable incumbent, and select exactly one next route or stop state before any new implementation.
