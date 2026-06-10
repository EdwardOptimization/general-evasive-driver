# M3149 Speed-Envelope Action-Delta Effectiveness and Saturation Synthesis

## Summary

- status: completed
- decision: `pivot_to_m3150_residual_action_delta_effectiveness_counterfactual_sensitivity_diagnostic`
- result class: `action_delta_effectiveness_synthesis_complete`
- source audit: `docs/m3148-engineering-controller-active-safety-driver-residual-trajectory-timing-speed-envelope-action-delta-coverage-diagnostic-result-audit.md`
- source diagnostic: `runs/m3147_engineering_controller_active_safety_driver_residual_trajectory_timing_speed_envelope_action_delta_coverage_diagnostic_materialization_preflight/summary.json`
- selected next route: M3150 residual action-delta effectiveness counterfactual sensitivity diagnostic.

## Evidence Summary

M3147 is complete and claim-safe:

- residual rows: 7/7
- step trace rows: 256
- trace failures: 0
- terminal collisions: 5
- terminal offtracks: 2
- terminal successes: 0
- overlay-any episodes: 7/7
- overlay-never episodes: 0/7
- zero-delta episodes: 0/7
- mean overlay active fraction: 0.9784557547715442
- max overlay alpha: 0.7935389639658202
- max action delta abs: 0.44438183307647705
- mean candidate saturation fraction: 0.19744602734261155
- mean fallback saturation fraction: 0.20893307830334673

M3147 coverage labels:

- `delta_present_outcome_unresolved`: 4
- `candidate_action_saturation_may_limit_delta_effect`: 2
- `collision_terminal_window_delta_low`: 1

Residual row detail:

- M3147 row 0001: collision, overlay active from step 1, max delta 0.24824605882167816, terminal-window throttle delta -0.1145653635263443, terminal-window brake delta 0.1377965286374092.
- M3147 row 0002: collision, overlay active from step 1, max delta 0.2882860004901886, terminal-window throttle delta -0.011353462934494019, terminal-window brake delta 0.02119312286376953.
- M3147 row 0003: offtrack, overlay active from step 1, max delta 0.20057624578475952, terminal-window throttle delta -0.008130541443824768, terminal-window brake delta 0.015177008509635926.
- M3147 row 0004: offtrack, overlay active from step 1, max delta 0.3141685128211975, terminal-window throttle delta -0.035346169769763944, terminal-window brake delta 0.06597951054573059.
- M3147 row 0005: collision, overlay active from step 1, max delta 0.13074880838394165, candidate saturation fraction 0.3611111111111111.
- M3147 row 0006: collision, overlay active from step 1, max delta 0.44438183307647705, terminal-window throttle delta -0.17272014617919923, terminal-window brake delta 0.18482789099216462.
- M3147 row 0007: collision, overlay active from step 1, max delta 0.30047789216041565, candidate saturation fraction 0.391304347826087.

## Supported Claims

- M3147 falsifies the missing-overlay explanation: all seven residual rows receive nonzero candidate-vs-fallback action deltas.
- M3142/M3147 preserve the obs72 current-frame actor-visible input and direct action3 `[steer, throttle, brake]` output contract.
- The remaining blocker is not coverage but effectiveness: deltas are present while the same residual 5 collision and 2 offtrack outcomes remain.
- The next diagnostic should measure terminal-window authority, action headroom, channel mix, and sensitivity limits before any new repair materialization.

## Falsified Claims

- M3142/M3147 are not repair-success evidence.
- The M3144 plateau is not explained by absent overlay activation.
- The action-delta traces do not justify promotion, ranking, validation, driver-performance, current-sim verdict, robustness-result, high-fidelity, paper, full-driver, feasibility-proof, or self-ID claims.
- Blindly increasing the current speed-envelope gains is not justified because the branch has not yet separated insufficient authority, wrong channel mix, action saturation, and trajectory insensitivity.

## Failure Taxonomy Summary

- `contract_violation`: not observed; obs72/action3 direct-action contract is preserved.
- `lineage_invalid`: not observed; M3149 traces through M3148, M3147, M3146, M3144, M3142, and M3105.
- `metric_artifact`: not observed for M3147 row accounting; residual rows and trace rows are complete.
- `scenario_sampling_failure`: not observed for the seven targeted residual rows; broader robustness remains future work.
- `behavior_regression`: unresolved; M3147 is diagnostic and does not change the measured M3144 plateau.
- `objective_overfit`: high if the next step directly tunes against these seven public residual rows.
- `proof_washout`: high if action-delta coverage is reworded as repair success.
- `seed_fragility`: unresolved until future broader panels.

## Public Gate Overfit Risk

Risk remains high. M3147 uses the known residual rows to understand the plateau, not to optimize a new policy. The next step must therefore be diagnostic and artifact-bounded: quantify whether terminal-window brake/throttle/steer headroom exists and whether the current deltas are near channel bounds before proposing any repair.

## Next Branch Decision

Pivot to M3150 residual action-delta effectiveness counterfactual sensitivity diagnostic:

- do not promote M3142.
- keep M3105/M3103 as the deployable incumbent.
- use M3147 step traces and coverage rows as the source evidence.
- compute residual-row terminal-window action headroom, delta utilization, saturation, and sensitivity labels without new rollout execution.
- preserve actor-visible obs72/action3 contract and no hidden/oracle/TTC/source/route/outcome/verdict actor inputs.
- produce diagnostic artifacts only; no validation, ranking, promotion, driver-performance, current-sim verdict, robustness-result, high-fidelity, paper, full-driver, repair-success, feasibility-proof, or self-ID claim.

## Boundary

M3149 is a synthesis and route-selection artifact only. It performs no reset, step, rollout, replay, fitting, PPO, training, validation, ranking, promotion, high-fidelity simulation, finite-window-vs-GRU comparison, or self-ID test.
