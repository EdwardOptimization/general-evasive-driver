# M3122 Residual Trajectory-Authority Stability-Recovery Plateau Synthesis

## Decision

- synthesis decision: `pivot`
- decision: `pivot_to_m3123_residual_hard_safety_action_authority_feasibility_diagnostic_materialization`
- selected next action: `m3123-engineering-controller-active-safety-driver-residual-hard-safety-action-authority-feasibility-diagnostic-materialization-preflight`
- reason: M3120 preserved the deployable direct-action contract and produced complete measurement artifacts, but the M3118 trajectory-authority/stability-recovery rules did not change the residual hard-safety blocker versus M3105/M3095. Another direct-rule gain edit would repeat the same local-search pattern without changing the evidence axis.

## Evidence Summary

M3120 is artifact-complete and claim-safe:

```text
status_pass: True
gate_matrix_pass: True
required_artifacts_present: True
full-fresh rows: 64/64
execution failures: 0
same-row comparison rows: 256
actor contract: obs72 -> direct action3 [steer throttle brake]
runtime_base_policy_required: False
```

The behavior plateau is exact against the strongest current baselines:

```text
M3120 success/collision/offtrack/speed_too_low: 57/5/2/0
delta vs M3105: success 0, collision 0, offtrack 0, speed_too_low 0
delta vs M3095: success 0, collision 0, offtrack 0, speed_too_low 0
clearance_margin_mean: 10.981241004822653
high_sideslip_fraction_mean: 0.05765007026268232
lateral_rmse_mean: 1.141869777927198
```

M3120 improves over older M3090 and M3100 in same-row context, but those deltas do not solve the current branch question because M3105/M3095/M3112 already define the no-speed-low plateau with the same 5 collision and 2 offtrack blockers.

## Supported Claims

- The M3118 rule/config/action function can be executed as a complete obs72/action3 full-fresh measurement source.
- M3120 preserves the runtime contract: no runtime base policy, checkpoint model, recurrent state, hidden oracle, TTC, source, route, outcome, progress, or verdict actor input.
- The M3118 mechanism-specific direct rules do not improve aggregate residual hard-safety counts over M3105/M3095 on the complete 64-row denominator.
- The direct-rule residual repair branch is now behavior-negative enough to require a new evidence axis before any further repair.

## Falsified Claims

- M3120 is not repair-success evidence.
- M3120 does not support promotion, validation, ranking, robustness-result, current-sim verdict, driver-performance, high-fidelity, paper, full-driver, or self-ID claims.
- The M3118 early trajectory authority plus stability recovery additions do not reduce the residual 5 collision and 2 offtrack blockers on the measured denominator.
- A further blind gain edit is not justified by the current evidence.

## Failure Taxonomy Summary

- `contract_violation`: not observed.
- `lineage_invalid`: not observed.
- `metric_artifact`: not observed.
- `scenario_sampling_failure`: not observed.
- `behavior_regression`: not an aggregate regression versus M3105/M3095, but the residual objective remains failed.
- `objective_overfit`: high risk for any direct continuation of same-row rule overlays.
- `proof_washout`: high risk if complete measurements are described as success.
- `seed_fragility`: unresolved; validation/generalization remains unclaimed.

## Public Gate Overfit Risk

Risk is high if the next milestone adjusts the M3118 direct-rule gains against the same seven residual failures. The last two repair materializations already preserved the contract and speed floor, but neither changed the residual hard-safety counts. The next evidence axis should ask whether the current obs72/action3 direct-rule layer has enough action authority and feasible trajectory space for the residual rows, rather than assuming another local overlay can fix them.

## Next Branch Decision

Pivot to:

```text
m3123-engineering-controller-active-safety-driver-residual-hard-safety-action-authority-feasibility-diagnostic-materialization-preflight
```

M3123 should be a diagnostic materialization, not a repair. It should use M3120 full-fresh rows, M3120 same-row comparisons, M3115 residual step/action traces, and M3118 rule artifacts to produce row-preserving action-authority and feasibility diagnostics:

- whether residual collision rows show late visible obstacle geometry, insufficient brake/steer authority, or clearance infeasibility under the direct-action contract
- whether residual offtrack rows show stability/edge recovery demand beyond direct-rule steering authority
- whether speed-floor preservation prevents needed deceleration in collision rows or correctly prevents low-speed regressions
- whether the next route should be an action-authority diagnostic, a trajectory-level controller architecture experiment, or a stop condition for this direct-rule branch

The new branch is:

```text
active_safety_driver_residual_action_authority_feasibility_diagnosis
```

## Boundary

M3122 is a synthesis decision only. It runs no reset, step, rollout, replay, fitting, PPO, training, validation, ranking, promotion, high-fidelity simulation, finite-window-vs-GRU comparison, or self-ID test.
