# M3155 Residual Action-Delta Negative Counterfactual Replay Synthesis

## Summary

- status: completed
- decision: `pivot_to_m3156_route_a_deployable_benchmark_pack_materialization`
- result class: `negative_counterfactual_replay_route_synthesis_complete`
- source audit: `docs/m3154-engineering-controller-active-safety-driver-residual-action-delta-counterfactual-replay-diagnostic-result-audit.md`
- source diagnostic: `runs/m3153_engineering_controller_active_safety_driver_residual_action_delta_counterfactual_replay_diagnostic_materialization_preflight/summary.json`
- selected next route: M3156 Route A deployable benchmark pack and known-failure taxonomy materialization.

## Evidence Summary

M3153/M3154 are complete and claim-safe:

- residual replay plan rows: 7/7
- fixed variant rows: 4
- counterfactual replay episode rows: 28
- counterfactual replay failure rows: 0
- comparison rows: 21
- M3153 gate matrix pass: true
- M3153 action-channel-sensitive diagnostic comparisons: 0
- M3153 diagnostic labels: `counterfactual_terminal_outcome_unchanged_diagnostic`: 21

Terminal counts are unchanged across the fixed replay panel:

- `m3142_reference`: 5 collision, 2 offtrack, 0 speed-too-low, 0 success
- `decel_headroom_probe`: 5 collision, 2 offtrack, 0 speed-too-low, 0 success
- `brake_saturation_probe`: 5 collision, 2 offtrack, 0 speed-too-low, 0 success
- `lateral_headroom_probe`: 5 collision, 2 offtrack, 0 speed-too-low, 0 success

The deployable incumbent remains M3105/M3103 through M3139/M3140:

- public runtime API: `ActiveSafetyReflexDriver.act(obs72)`
- output contract: direct `[steer, throttle, brake]`
- M3105 full-fresh rows: 64/64
- M3105 success/collision/offtrack/speed-too-low: 57/5/2/0
- M3105 measurement failures: 0
- M3105 runtime base policy required: false

## Supported Claims

- The local residual action-delta branch has a negative diagnostic result on the seven known residual rows.
- The tested bounded actor-visible throttle/brake/steer variants did not change terminal outcome on any comparison row.
- Continuing the same local action-channel gain/mix loop is not justified without a new evidence axis.
- The current deployable artifact should remain the M3105/M3103 incumbent until a stronger measured candidate improves hard-safety metrics without violating the obs72/action3 contract.
- The next aligned engineering step is to materialize a Route A deployable verification pack: driver contract, benchmark metric rows, known residual failure taxonomy, claim boundaries, and audit route.

## Falsified Claims

- M3153 does not show repair success.
- M3153 does not show validation, robustness, driver-performance, current-sim verdict, high-fidelity validation, paper evidence, feasibility proof, or self-ID evidence.
- M3150 headroom labels alone do not justify a local action-delta repair route.
- M3142/M3153 variants do not improve the seven residual terminal outcomes under the fixed counterfactual panel.
- The branch should not continue by widening or tuning the same residual action-delta variants on the same rows.

## Failure Taxonomy Summary

- `contract_violation`: not observed; all M3153 variants remain actor-visible obs72 to direct action3.
- `lineage_invalid`: not observed; evidence traces through M3154, M3153, M3152, M3150, M3147, M3144, and M3105.
- `metric_artifact`: not observed for M3153 row accounting; 28/28 episodes and 21/21 comparisons are present.
- `scenario_sampling_failure`: unresolved outside the seven residual rows; M3153 is not broad validation.
- `behavior_regression`: local variants are terminal-outcome invariant on the residual panel, so no candidate earns broader behavior testing.
- `objective_overfit`: high if the branch keeps generating fixed-row action-delta variants.
- `proof_washout`: high if negative diagnostics are reworded as repair impossibility or performance evidence.
- `seed_fragility`: unresolved for broader verification; M3156 should package existing evidence rather than claim robustness.

## Public Gate Overfit Risk

Risk is high if the project keeps using the seven residual rows as a local repair target. M3156 must not tune a driver against those rows. It should freeze the deployable incumbent evidence and produce a verification pack that makes the current strengths and blockers explicit: M3105/M3103 is deployable and traceable, but incomplete against the hard-safety objective.

## Next Branch Decision

Pivot to M3156 Route A deployable benchmark pack materialization:

- stop the local residual action-delta repair branch.
- keep M3105/M3103 as the deployable incumbent.
- materialize a compact benchmark/verification pack from existing evidence, without new environment reset, rollout, validation, ranking, or promotion.
- include the public obs72/action3 runtime contract, M3105 denominator metrics, residual collision/offtrack taxonomy, M3153 negative replay labels, and claim boundaries.
- route M3156 to M3157 result audit before any further repair or validation step.

This follows the post-M2470 Route A direction: freeze a usable actuator-level active-safety controller baseline, make its failure taxonomy explicit, and keep self-ID/GRU/paper evidence auxiliary.

## Boundary

M3155 is a synthesis and route-selection artifact only. It performs no reset, step, rollout, replay, fitting, PPO, training, validation, ranking, promotion, high-fidelity simulation, finite-window-vs-GRU comparison, or self-ID test.

Rejected claims:

```text
repair implementation, validation result, driver-performance verdict, current-sim verdict, robustness-result, repair success, feasibility proof, checkpoint ranking, winner selection, checkpoint promotion, high-fidelity validation readiness or result, paper evidence, finite-window-vs-GRU conclusion, full ideal driver completion, or level3 self-identification
```
