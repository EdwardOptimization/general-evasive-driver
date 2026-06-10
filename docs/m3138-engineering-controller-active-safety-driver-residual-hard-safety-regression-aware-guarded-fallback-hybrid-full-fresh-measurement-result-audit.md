# M3138 Regression-Aware Guarded Fallback Hybrid Full-Fresh Measurement Result Audit

## Summary

- status: completed
- decision: `accept_m3137_artifacts_reject_behavior_regression_stop_guarded_fallback_hybrid_branch_retain_m3105_incumbent`
- result class: `accept_m3137_complete_claim_safe_reject_repair_success`
- source summary: `runs/m3137_engineering_controller_active_safety_driver_residual_hard_safety_regression_aware_guarded_fallback_hybrid_full_fresh_measurement_preflight/summary.json`
- M3137 status pass: true
- M3137 gate matrix pass: true
- required artifacts present: true
- follow-up route: stop this guarded fallback hybrid branch; retain M3105/M3103 no-regression direct-action path as the current incumbent deployable reflex.

## Artifact Audit

M3137 is accepted as complete and claim-safe:

- full-fresh scheduled rows: 64/64
- measurement episode rows: 64
- measurement failure rows: 0
- same-row comparison rows: 256
- exact seed matches: M3105 64, M3095 64, M3100 64, M3090 64
- runtime driver id: `m3135_regression_aware_guarded_fallback_hybrid`
- output contract: obs72 current-frame actor-visible input to direct `[steer, throttle, brake]`
- runtime base policy required: false
- checkpoint model required: false
- recurrent hidden state required: false
- action clip fraction mean: 0.0

The M3137 artifacts are suitable as measurement evidence and audit input only.

## Behavior Audit

M3137 full-fresh measured behavior:

- success: 56/64
- collision: 6/64
- offtrack: 2/64
- speed-too-low: 0/64
- clearance margin mean: 10.975710800230118
- high-sideslip fraction mean: 0.057246427530285714
- lateral RMSE mean: 1.1415766162165462

Same-row deltas:

- vs M3105: success -1, collision +1, offtrack 0, speed-too-low 0
- vs M3095: success -1, collision +1, offtrack 0, speed-too-low 0
- vs M3100: success +1, collision +1, offtrack -1, speed-too-low -1
- vs M3090: success +13, collision +1, offtrack -3, speed-too-low -11

This is not repair-success evidence. Relative to the current M3105/M3095 incumbent denominator, M3137 preserves speed floor and offtrack counts but loses one success and adds one collision. The guarded fallback hybrid recovered most of the standalone corridor regression seen in M3131, but it still fails the incumbent no-regression requirement.

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

M3138 accepts M3137 as a complete full-fresh measurement artifact and rejects promotion or repair-success interpretation. The M3135 guarded fallback hybrid branch should stop here because the full-fresh measurement is behavior-negative against the incumbent M3105/M3095 path.

The current deployable active-safety reflex remains the M3105/M3103 no-regression direct-action fallback. Any later route should start from the residual M3105 blockers rather than continue tuning this guarded corridor hybrid branch.
