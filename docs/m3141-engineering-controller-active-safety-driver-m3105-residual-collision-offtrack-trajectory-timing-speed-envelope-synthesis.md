# M3141 M3105 Residual Collision/Offtrack Trajectory-Timing Speed-Envelope Synthesis

## Summary

- status: completed
- decision: `pivot_to_m3142_residual_trajectory_timing_speed_envelope_materialization`
- result class: `m3105_residual_blocker_route_synthesis_complete`
- source deployable interface: `docs/m3140-engineering-controller-active-safety-driver-m3105-incumbent-deployable-reflex-interface-result-audit.md`
- source residual blockers: `runs/m3139_engineering_controller_active_safety_driver_m3105_incumbent_deployable_reflex_interface_materialization_preflight/residual_blocker_rows.csv`
- source counterfactual envelope: `runs/m3125_engineering_controller_active_safety_driver_residual_hard_safety_counterfactual_action_authority_envelope_diagnostic_materialization_preflight/counterfactual_action_authority_envelope_rows.csv`
- selected next route: M3142 residual trajectory-timing speed-envelope materialization.

## Evidence Summary

The accepted deployable incumbent is the M3105/M3103 direct-action reflex:

- public API: `ActiveSafetyReflexDriver.act(obs72) -> [steer, throttle, brake]`
- full-fresh denominator: 64 rows
- success: 57
- collision: 5
- offtrack: 2
- speed-too-low: 0
- runtime base policy required: false
- checkpoint model required: false
- recurrent hidden state required: false

M3139 preserved the seven residual blocker rows:

- 5 collision blockers
- 2 offtrack blockers
- 0 speed-too-low blockers

The residual collision rows are mostly high-speed, late-clearance failures:

- blocker speeds are approximately 14.7-19.1 m/s in M3139 measurement rows.
- M3125 shows terminal obstacle distance is often already near 0.4-1.7 m for collision rows.
- final-window brake/steer authority is near or fully exhausted on most collision rows.

The residual offtrack rows are stability/edge recovery failures:

- both offtrack rows show high edge urgency.
- one offtrack row has high sideslip fraction above 0.5 and lateral RMSE above 2.6 m.
- the other is near steer saturation under boundary pressure.

## Supported Claims

- The public deployable API is now aligned with the M3105/M3103 incumbent.
- M3105 remains the best current deployable incumbent because later direct-rule branches did not improve it:
  - M3112 plateaued exactly against M3105: 57 success, 5 collision, 2 offtrack, 0 speed-too-low.
  - M3120 plateaued exactly against M3105 with the same counts.
  - M3131 regressed badly: 35 success, 7 collision, 14 offtrack, 8 speed-too-low.
  - M3137 still regressed versus M3105: 56 success, 6 collision, 2 offtrack, 0 speed-too-low.
- The next repair hypothesis should act earlier in the episode, before terminal brake/steer saturation, and should be explicitly bounded by speed-floor and offtrack guards.

## Falsified Claims

- M3105 is not the full active-safety goal completion; 5 collision and 2 offtrack blockers remain.
- M3110/M3118-style direct residual gain overlays are not sufficient; measured results plateaued.
- M3129/M3131-style standalone corridor reflex is not acceptable; measured results regressed collision, offtrack, speed floor, and success.
- M3135/M3137 guarded fallback hybrid is not acceptable as a replacement; it added one collision and lost one success versus M3105.
- End-window brake/steer gain increases are not a credible next route for the collision blockers because M3125 shows near-exhausted or exhausted final-window authority.

## Failure Taxonomy Summary

- `contract_violation`: not observed in M3139/M3140; deployable obs72/action3 contract is intact.
- `lineage_invalid`: not observed; evidence traces to M3103, M3105, M3125, M3139, and M3140.
- `metric_artifact`: not observed for the cited artifacts.
- `scenario_sampling_failure`: unresolved for future validation, but the current synthesis uses the complete 64-row fresh denominator evidence.
- `behavior_regression`: observed in M3131 and M3137 relative to M3105; must be guarded against in the next branch.
- `objective_overfit`: high risk if the next branch only targets the seven public blockers without same-row full-denominator measurement.
- `proof_washout`: high risk if deployability is described as repair success.
- `seed_fragility`: unresolved until a future broader fresh/robustness panel is run.

## Public Gate Overfit Risk

Risk is medium-high. The seven residual blockers are known public rows, so the next branch must not be promoted on blocker-only probes. It may materialize a candidate from actor-visible features and blocker diagnostics, but any behavioral interpretation requires the complete 64-row same-denominator measurement against M3105, M3095, M3100, and M3090.

## Next Branch Decision

Pivot to M3142 residual trajectory-timing speed-envelope materialization:

- keep M3105/M3103 as the default fallback action.
- add an actor-visible early speed-envelope overlay that can start braking/throttle suppression before terminal obstacle/edge saturation.
- keep the overlay bounded and conservative:
  - no runtime base policy,
  - no checkpoint,
  - no recurrent hidden state,
  - no hidden/oracle/TTC/source/route/outcome/verdict labels,
  - no row label or M3105 outcome input,
  - no full-brake blanket rule,
  - no speed-floor regression,
  - no standalone corridor replacement.
- require a later full-fresh measurement before any repair-success, validation, ranking, promotion, driver-performance, current-sim verdict, robustness, high-fidelity, paper, full-driver, feasibility-proof, or self-ID claim.

## Boundary

M3141 is a synthesis and route-selection artifact only. It performs no reset, step, rollout, replay, fitting, PPO, training, validation, ranking, promotion, high-fidelity simulation, finite-window-vs-GRU comparison, or self-ID test.
