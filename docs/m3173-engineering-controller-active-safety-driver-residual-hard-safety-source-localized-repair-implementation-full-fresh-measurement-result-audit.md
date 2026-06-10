# M3173 Residual Hard-Safety Source-Localized Repair Implementation Full-Fresh Measurement Result Audit

## Summary

- status: completed
- decision: `accept_m3172_complete_claim_safe_reject_behavior_improvement_route_to_m3174_negative_measurement_synthesis`
- result class: `accept_m3172_complete_claim_safe_behavior_negative_vs_m3105`
- source summary: `runs/m3172_engineering_controller_active_safety_driver_residual_hard_safety_source_localized_repair_implementation_full_fresh_measurement_preflight/summary.json`
- M3172 status pass: true
- M3172 gate matrix pass: true
- required artifacts present: true
- follow-up route: M3174 negative-measurement synthesis before any new repair implementation or validation route.

## Artifact Audit

M3172 is accepted as complete and claim-safe:

- scheduled full-fresh rows: 64/64
- measurement episode rows: 64
- measurement failure rows: 0
- same-row comparison rows: 256
- exact seed matches: M3105 64, M3095 64, M3100 64, M3090 64
- runtime driver id: `m3170_source_localized_repair_overlay`
- output contract: obs72 current-frame actor-visible input to direct `[steer, throttle, brake]`
- runtime base policy required: false
- checkpoint model required: false
- recurrent hidden state required: false
- action clip fraction mean: 0.0
- contract guard rows: 22
- contract guard rows pass: true
- claim boundary rows: 21
- claim boundary rows pass: true

The M3172 artifacts are suitable as full-fresh measurement evidence and audit input only.

## Behavior Audit

M3172 full-fresh measured behavior:

- success: 56/64
- collision: 6/64
- offtrack: 2/64
- speed-too-low: 0/64
- clearance margin mean: 11.002313807121931
- high-sideslip fraction mean: 0.059417655889315024
- lateral RMSE mean: 1.1559879144579355

Same-row deltas:

- vs M3105: success -1, collision +1, offtrack 0, speed-too-low 0
- vs M3095: success -1, collision +1, offtrack 0, speed-too-low 0
- vs M3100: success +1, collision +1, offtrack -1, speed-too-low -1
- vs M3090: success +13, collision +1, offtrack -3, speed-too-low -11

This is behavior-negative against the current M3105/M3095 incumbent. The M3170 source-localized overlay improves speed-low and offtrack counts relative to older weaker baselines, but it adds one collision and loses one success against the incumbent same-denominator rows. That blocks promotion, validation interpretation, and repair-success language.

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

M3173 accepts M3172 as a complete full-fresh measurement artifact and rejects behavior-improvement interpretation. The M3170 source-localized candidate is not a deployable incumbent replacement.

The next step is M3174 synthesis: classify the negative measurement, preserve M3105/M3103 as the deployable incumbent, and select exactly one next route or stop state before any new repair implementation, validation, ranking, promotion, or performance verdict.
