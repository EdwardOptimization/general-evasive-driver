# M3140 M3105-Incumbent Deployable Reflex Interface Result Audit

## Summary

- status: completed
- decision: `accept_m3139_deployable_interface_retain_m3105_incumbent_preserve_residual_blockers`
- result class: `accept_m3139_complete_claim_safe_deployable_interface_artifact`
- source summary: `runs/m3139_engineering_controller_active_safety_driver_m3105_incumbent_deployable_reflex_interface_materialization_preflight/summary.json`
- M3139 status pass: true
- M3139 gate matrix pass: true
- required artifacts present: true
- follow-up route: no automatic promotion or validation; later work should start from the explicit M3105 residual collision/offtrack blockers.

## Artifact Audit

M3139 is accepted as complete and claim-safe:

- public API: `autodrift.active_safety_reflex_driver.ActiveSafetyReflexDriver.act(obs72)`
- driver id: `active_safety_reflex_driver_m3105_incumbent_v4_no_regression`
- incumbent policy id: `m3103_v4_v2_fallback_no_regression_hard_safety_direct_action_repair`
- incumbent measurement id: `m3105-engineering-controller-active-safety-driver-v4-v2-fallback-no-regression-hard-safety-direct-action-repair-full-fresh-measurement-preflight`
- input contract: actor-visible obs72 current-frame vector
- output contract: direct action3 `[steer, throttle, brake]`
- output semantics: `direct_action_clipped`
- runtime base policy required: false
- checkpoint model required: false
- recurrent hidden state required: false
- action probe rows: 5
- action probes finite: true
- action probes bounded: true
- action probes equivalent to M3103 incumbent action: true

The deployable interface now reflects the M3138-selected incumbent instead of the older M3078 binding.

## Incumbent Evidence

M3139 preserves the M3105 full-fresh measurement evidence:

- measurement rows: 64/64
- measurement failures: 0
- success: 57
- collision: 5
- offtrack: 2
- speed-too-low: 0

Residual blocker rows are explicitly materialized:

- collision blockers: 5
- offtrack blockers: 2
- speed-too-low blockers: 0

This means M3139 improves deployability and traceability, not closed-loop safety performance. The public API is now aligned with the current incumbent, but the active safety driver is still incomplete against the full hard-safety objective.

## Rejected Claims

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

M3140 accepts M3139 as the current deployable interface artifact. It is suitable as the public obs72-to-action3 active-safety reflex API for subsequent engineering and validation work, with the explicit limitation that M3105 still has 5 collision and 2 offtrack blockers on the 64-row fresh current-sim denominator.

The next aligned engineering work should target those residual blockers directly and preserve the M3105 no-regression deployment contract until a stronger measured candidate improves hard-safety metrics without regressing same-row success, collision, offtrack, speed floor, clearance, stability, recovery, or robustness evidence.
