# M3152 Residual Action-Delta Counterfactual Replay Synthesis

## Summary

- status: completed
- decision: `pivot_to_m3153_bounded_residual_action_delta_counterfactual_replay_diagnostic`
- result class: `counterfactual_replay_route_synthesis_complete`
- source audit: `docs/m3151-engineering-controller-active-safety-driver-residual-action-delta-effectiveness-counterfactual-sensitivity-diagnostic-result-audit.md`
- source diagnostic: `runs/m3150_engineering_controller_active_safety_driver_residual_action_delta_effectiveness_counterfactual_sensitivity_diagnostic_materialization_preflight/summary.json`
- selected next route: M3153 bounded residual action-delta counterfactual replay diagnostic.

## Evidence Summary

M3150/M3151 are complete and claim-safe:

- residual effectiveness rows: 7/7
- source M3147 step rows: 256
- M3150 gate matrix pass: true
- no new environment reset: true
- no new environment step: true
- no policy rollout: true
- headroom available rows: 5
- saturation-limited rows: 2
- terminal-delta-low rows: 1
- delta-present counterfactual-needed rows: 3
- mean brake headroom: 0.5090515977569988
- mean throttle-drop headroom: 0.3318724862166813
- mean steer headroom: 0.12711772492953707
- mean candidate saturation fraction: 0.19744602734261155

M3150 labels:

- `collision_action_saturation_limited`: 2
- `collision_delta_present_counterfactual_needed`: 2
- `collision_terminal_delta_low_headroom_available`: 1
- `offtrack_delta_present_counterfactual_needed`: 1
- `offtrack_steer_delta_low_headroom_available`: 1

## Supported Claims

- The M3144/M3147 plateau is not caused by missing overlay activation.
- The M3150 sensitivity evidence is mixed: some residual rows have terminal-window headroom, while two collision rows are saturation-limited.
- A direct repair is not yet justified because the branch has not measured whether stronger or differently mixed actor-visible action deltas are trajectory-effective in the simulator.
- One bounded counterfactual replay diagnostic is justified if it remains diagnostic-only, row-preserving, contract-safe, and explicitly rejects repair-success and validation claims.

## Falsified Claims

- M3150/M3151 do not show repair success.
- M3150/M3151 do not justify promotion of M3142 or replacement of M3105/M3103.
- The next step should not be blind gain tuning, because the evidence separates at least three causes: saturation-limited collisions, low terminal-window deltas with remaining headroom, and delta-present but outcome-unresolved rows.
- M3152 is not validation, ranking, driver-performance, current-sim verdict, robustness-result, high-fidelity, paper, full-driver, feasibility-proof, or self-ID evidence.

## Failure Taxonomy Summary

- `contract_violation`: not observed; actor contract remains obs72 to direct action3.
- `lineage_invalid`: not observed; M3152 traces through M3151, M3150, M3149, M3147, M3144, M3142, and M3105.
- `metric_artifact`: not observed for M3150 row accounting; diagnostic rows are complete.
- `scenario_sampling_failure`: not observed for the seven targeted residual rows; broader robustness remains future work.
- `behavior_regression`: unresolved; M3150 is no-new-execution reanalysis.
- `objective_overfit`: high if M3153 optimizes the seven rows instead of measuring counterfactual sensitivity.
- `proof_washout`: high if counterfactual replay success is reworded as deployable repair success.
- `seed_fragility`: unresolved until future broader panels.

## Public Gate Overfit Risk

Risk remains high because M3153 will replay known residual rows. M3153 must therefore restrict itself to diagnostic variants that answer whether action channels are sensitive at all. It must not tune a final driver, promote a candidate, or claim repair success.

## Next Branch Decision

Pivot to M3153 bounded residual action-delta counterfactual replay diagnostic:

- keep M3105/M3103 as the deployable incumbent.
- replay only the seven residual rows as a diagnostic panel.
- compare a small fixed set of actor-visible action-delta variants derived from M3147/M3150 labels.
- preserve obs72/action3 direct-action contract for all counterfactual action functions.
- reject hidden/oracle/TTC/source/route/outcome/verdict actor inputs.
- produce diagnostic artifacts only; no validation, ranking, promotion, driver-performance, current-sim verdict, robustness-result, high-fidelity, paper, full-driver, repair-success, feasibility-proof, or self-ID claim.

## Boundary

M3152 is a synthesis and route-selection artifact only. It performs no reset, step, rollout, replay, fitting, PPO, training, validation, ranking, promotion, high-fidelity simulation, finite-window-vs-GRU comparison, or self-ID test.
