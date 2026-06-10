# M3163 Route A Public Deployable Validation Result Synthesis

## Summary

- status: completed
- decision: `pivot_to_m3164_residual_hard_safety_failure_source_branch_materialization`
- result class: `route_a_public_deployable_validation_result_synthesis_complete`
- source audit: `docs/m3162-engineering-controller-active-safety-driver-route-a-public-deployable-validation-execution-result-audit.md`
- source validation execution: `runs/m3161_engineering_controller_active_safety_driver_route_a_public_deployable_validation_execution_preflight/validation_execution_summary.json`
- selected next route: M3164 residual hard-safety failure-source branch materialization preflight.

## Evidence Summary

M3161/M3162 are complete and claim-safe:

- public runtime API: `ActiveSafetyReflexDriver.act(obs72)`
- output contract: direct `[steer, throttle, brake]`
- runtime base policy required: false
- checkpoint model required: false
- recurrent hidden state required: false
- validation execution rows: 64/64
- validation execution failures: 0
- gate matrix pass: true
- runtime contract probe rows: 5
- claim boundary rows: 22

The validation execution result remains the M3105 incumbent behavior:

- success: 57
- collision: 5
- offtrack: 2
- speed-too-low: 0
- success rate: 0.890625
- clearance margin mean: 10.981307227309182
- same-case comparison rows: 64
- same-case outcome matches against M3105: 64/64
- hard-safety deltas against M3105: success 0, collision 0, offtrack 0, speed-too-low 0

Known residual blockers remain unresolved:

- known residual blocker rows: 7
- known failures preserved: 7
- known failures resolved: 0
- residual blocker families: 5 collision, 2 offtrack

Prior branch evidence limits the next search space. M3153/M3155 showed 0/21 action-channel-sensitive comparisons on the seven residual rows under fixed throttle, brake, and lateral variants. The next route should not widen or retune the same local action-delta loop without a new evidence axis.

## Supported Claims

- Route A now has a deployable and verifiable public runtime surface: `obs72 -> [steer, throttle, brake]`.
- M3161 proves the public API faithfully executes the accepted M3105/M3103 incumbent on the 64-row same-case validation denominator.
- M3161/M3162 provide complete row-level accounting for residual hard-safety blockers.
- The current public deployable driver is useful as an incumbent baseline and validation denominator.
- Further progress toward the full objective requires a residual hard-safety branch that changes the evidence axis beyond local action-delta tuning.

## Falsified Claims

- M3161 does not prove repair success.
- M3161 does not prove a driver-performance verdict, current-sim verdict, robustness result, high-fidelity result, paper-level result, full ideal-driver completion, feasibility proof, finite-window-vs-GRU result, or self-ID evidence.
- Exact same-case M3105 match is not improvement evidence.
- The public deployable validation result does not justify promotion or winner selection.
- Continuing the same fixed-row action-delta gain/mix loop is not justified by M3153/M3155.

## Failure Taxonomy Summary

- `contract_violation`: not observed in M3161; obs72/action3 and no-runtime-base-policy contract probes pass.
- `lineage_invalid`: not observed; M3161 traces through M3160, M3159, M3156, and M3105.
- `metric_artifact`: not observed for row accounting; 64 validation rows and 0 execution failure rows are present.
- `scenario_sampling_failure`: unresolved for broader claims; M3161 is same-case current-sim validation execution, not private holdout or high-fidelity validation.
- `behavior_regression`: not observed versus M3105 because all 64 same-case outcomes match.
- `objective_overfit`: high if the next work keeps optimizing only the seven public residual rows or the same action-delta variants.
- `proof_washout`: high if M3161 is reworded as repair success or current-sim verdict.
- `seed_fragility`: unresolved outside the accepted 64-row denominator.

## Public Gate Overfit Risk

Risk is high if the next branch treats the seven residual rows as a tuning target. M3164 must materialize a branch pack that separates:

- residual row disclosure;
- exact same-case M3105 equivalence;
- negative action-delta counterfactual evidence;
- actor-visible contract constraints;
- allowed next evidence axes.

It must not mutate the driver, rank candidates, or claim repair. The point is to prevent the next repair from repeating a local search loop that has already returned terminal-invariant diagnostics.

## Next Branch Decision

Pivot to M3164 residual hard-safety failure-source branch materialization:

- close the Route A deployable benchmark pack validation branch as a packaging and execution branch.
- keep M3105/M3103 as the deployable incumbent baseline.
- open a new residual hard-safety branch focused on failure-source localization and actor-visible repair admission.
- materialize a machine-readable branch pack from M3161, M3162, M3156, and M3153 evidence.
- require the next repair path to name a new evidence axis before any driver mutation.

The M3164 branch must preserve the public runtime contract:

```text
ActiveSafetyReflexDriver.act(obs72) -> [steer, throttle, brake]
```

It must reject hidden dynamics, oracle labels, TTC actor inputs, reference trajectories, target/source/route/outcome/progress/verdict labels, runtime base policies, recurrent hidden state, checkpoint mutation, ranking, promotion, repair-success claims, validation-result claims, and self-ID/GRU/paper claims.

## Boundary

M3163 is a synthesis and route-selection artifact only. It performs no reset, step, rollout, replay, fitting, PPO, training, validation rerun, ranking, promotion, high-fidelity simulation, finite-window-vs-GRU comparison, or self-ID test.

Rejected claims:

```text
repair implementation, validation result, driver-performance verdict, current-sim verdict, robustness-result, repair success, feasibility proof, checkpoint ranking, winner selection, checkpoint promotion, high-fidelity validation readiness or result, paper evidence, finite-window-vs-GRU conclusion, full ideal driver completion, or level3 self-identification
```

## Next

- next blocker: `m3164-engineering-controller-active-safety-driver-residual-hard-safety-failure-source-branch-materialization-preflight`
- follow-up manifest: `experiments/manifests/m3164-engineering-controller-active-safety-driver-residual-hard-safety-failure-source-branch-materialization-preflight.json`
