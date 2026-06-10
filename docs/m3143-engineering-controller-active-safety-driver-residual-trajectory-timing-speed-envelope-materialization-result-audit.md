# M3143 Residual Trajectory-Timing Speed-Envelope Materialization Result Audit

## Summary

- status: completed
- decision: `accept_m3142_materialization_route_to_full_fresh_measurement_preserve_m3105_fallback`
- result class: `accept_m3142_complete_claim_safe_speed_envelope_candidate`
- source summary: `runs/m3142_engineering_controller_active_safety_driver_residual_trajectory_timing_speed_envelope_materialization_preflight/summary.json`
- M3142 status pass: true
- M3142 gate matrix pass: true
- required artifacts present: true
- follow-up route: M3144 full-fresh same-denominator measurement before any repair-success, validation, ranking, promotion, driver-performance, current-sim verdict, robustness, high-fidelity, paper, full-driver, feasibility-proof, or self-ID claim.

## Artifact Audit

M3142 is accepted as complete and claim-safe:

- policy id: `m3142_residual_trajectory_timing_speed_envelope`
- fallback policy id: `m3103_v4_v2_fallback_no_regression_hard_safety_direct_action_repair`
- input contract: actor-visible obs72 current-frame vector
- output contract: direct action3 `[steer, throttle, brake]`
- output semantics: `direct_action_clipped`
- runtime base policy required: false
- checkpoint model required: false
- recurrent hidden state required: false
- hidden/oracle actor input required: false
- TTC actor input required: false
- rule rows: 4
- runtime contract rows: 1
- action probe rows: 6
- fallback probe rows: 2
- overlay probe rows: 4
- residual requirement rows: 7
- claim boundary rows: 14

The action probes preserve the safe/low-speed fallback path exactly and apply only bounded throttle reduction, brake support, and small steer adjustment on overlay probes. All probes are finite, bounded, and delta-limited.

## Residual Requirement Audit

M3142 carries the seven M3139 residual blockers forward as requirements, not solved outcomes:

- collision blockers: 5
- offtrack blockers: 2
- speed-too-low blockers: 0

This preserves the M3105/M3103 incumbent as the current deployable fallback while creating one measurable candidate for the earlier trajectory-timing speed-envelope hypothesis selected in M3141.

## Rejected Claims

- measurement result
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

M3143 accepts M3142 as a complete, bounded, actor-visible obs72-to-action3 materialization artifact. It does not accept any behavior-improvement interpretation because M3142 has not been run on the full fresh denominator.

The next aligned step is one M3144 full-fresh measurement of `residual_trajectory_timing_speed_envelope_action` on the same 64-row denominator used by M3105/M3137, with same-row comparisons against M3105, M3095, M3100, and M3090. M3144 must preserve the M3105 no-regression contract as the comparison baseline and may only become behavior evidence after a result audit.
