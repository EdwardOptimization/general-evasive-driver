# M3146 Residual Trajectory-Timing Speed-Envelope Plateau Synthesis

## Summary

- status: completed
- decision: `pivot_to_m3147_speed_envelope_action_delta_coverage_diagnostic`
- result class: `speed_envelope_plateau_synthesis_complete`
- source audit: `docs/m3145-engineering-controller-active-safety-driver-residual-trajectory-timing-speed-envelope-full-fresh-measurement-result-audit.md`
- source measurement: `runs/m3144_engineering_controller_active_safety_driver_residual_trajectory_timing_speed_envelope_full_fresh_measurement_preflight/summary.json`
- selected next route: M3147 speed-envelope action-delta coverage diagnostic.

## Evidence Summary

The M3105/M3103 incumbent remains the current deployable fallback:

- full-fresh denominator: 64 rows
- success: 57
- collision: 5
- offtrack: 2
- speed-too-low: 0
- runtime base policy required: false
- checkpoint model required: false
- recurrent hidden state required: false

M3142 materialized a bounded actor-visible speed-envelope overlay and M3144 measured it on the same full-fresh denominator:

- scheduled full-fresh rows: 64/64
- measurement episode rows: 64
- measurement failure rows: 0
- same-row comparison rows: 256
- M3144 success: 57
- M3144 collision: 5
- M3144 offtrack: 2
- M3144 speed-too-low: 0
- M3144 vs M3105: success 0, collision 0, offtrack 0, speed-too-low 0
- M3144 clearance mean delta vs M3105: +0.006064695049001482
- M3144 return mean delta vs M3105: -0.06574071251776653

## Supported Claims

- M3142/M3144 preserve the obs72/action3 direct `[steer, throttle, brake]` contract.
- The speed-envelope candidate is complete enough to measure and audit.
- The speed-envelope candidate does not regress M3105 hard-safety counts on the 64-row fresh denominator.

## Falsified Claims

- M3142 is not repair-success evidence.
- The current bounded speed-envelope overlay does not reduce the 5 residual collision blockers or 2 residual offtrack blockers.
- Continuing by simply increasing terminal direct-action gains is not justified because M3125 already showed late authority exhaustion and M3144 showed no outcome improvement from the earlier bounded overlay.

## Failure Taxonomy Summary

- `contract_violation`: not observed in M3142/M3144.
- `lineage_invalid`: not observed; M3144 traces through M3143, M3142, M3141, M3139, and M3105.
- `metric_artifact`: not observed; full-fresh row count, comparison count, and seed alignment gates pass.
- `scenario_sampling_failure`: not observed for the 64-row current-sim denominator; broader robustness remains future work.
- `behavior_regression`: not observed versus M3105, but no hard-safety improvement is observed either.
- `objective_overfit`: still high if the next step only targets known residual rows without understanding whether the overlay activated and changed actions.
- `proof_washout`: high if plateau is reworded as deployment success.
- `seed_fragility`: unresolved until future broader panels.

## Public Gate Overfit Risk

Risk remains medium-high. The seven residual blockers are known public rows, and M3144 did not improve them. Any next repair branch must first establish whether the speed-envelope overlay actually changed candidate actions on the residual rows, whether changes were too small or too late, and whether unchanged hard-safety outcomes are due to action saturation, trajectory timing, or environment insensitivity.

## Next Branch Decision

Pivot to M3147 speed-envelope action-delta coverage diagnostic:

- do not promote M3142 or replace M3105/M3103 as incumbent.
- use M3144 measurement rows and same-row comparisons as the starting evidence.
- inspect candidate-vs-fallback action deltas, overlay activation coverage, action saturation, and residual-failure row coverage.
- preserve actor-visible obs72/action3 contract and no hidden/oracle/TTC/source/route/outcome/verdict actor inputs.
- produce diagnostic artifacts only; no new validation, ranking, promotion, driver-performance, current-sim verdict, robustness, high-fidelity, paper, full-driver, repair-success, feasibility-proof, or self-ID claim.

## Boundary

M3146 is a synthesis and route-selection artifact only. It performs no reset, step, rollout, replay, fitting, PPO, training, validation, ranking, promotion, high-fidelity simulation, finite-window-vs-GRU comparison, or self-ID test.
