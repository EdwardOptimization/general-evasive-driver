# M3109 Residual Collision/Offtrack Decomposition Result Audit

## Audit Decision

- decision: `accept_m3108_decomposition_route_to_m3110_residual_collision_offtrack_actor_visible_repair_materialization`
- audit status: `accepted_with_residual_hard_safety_repair_requirement`
- M3108 status_pass: `True`
- M3108 gate_matrix_pass: `True`
- required artifacts present: `True`
- source measurement rows: `64`
- residual failure rows: `7`
- residual collision rows: `5`
- residual offtrack rows: `2`
- residual speed-too-low rows: `0`
- residual axes: `collision_lateral_intrusion`, `offtrack_boundary_recovery`
- residual comparison rows: `21`
- residual repair requirement rows: `7`
- selected next action: `m3110-engineering-controller-active-safety-driver-residual-collision-offtrack-actor-visible-repair-materialization-preflight`

## Evidence Summary

M3108 is a complete no-new-execution decomposition artifact set derived from the M3105 full-fresh v4 measurement and the M3107 pivot decision. It preserves the complete 64-row source denominator and materializes exactly the 7 residual non-success rows that block hard-safety progress.

The residual rows are:

```text
obstacle_collision: 5
off_track: 2
speed_too_low: 0
collision_lateral_intrusion: 3
offtrack_boundary_recovery: 4
same-row residual comparison rows: 21
same-row baselines: M3095, M3100, M3090
```

The decomposition keeps the deployable actor boundary intact:

```text
input: actor-visible obs72 only
output: direct action3 [steer, throttle, brake]
runtime_base_policy_required: false
checkpoint_model_required: false
recurrent_hidden_state_required: false
hidden/oracle/TTC/target/source/route/outcome/progress/verdict actor input: forbidden
```

The repair requirements are sufficiently explicit to admit one materialization route:

```text
collision_lateral_intrusion_guard: p0
offtrack_boundary_recovery_guard: p0
speed_floor_preservation: p0
residual_collision_reduction: p0
residual_offtrack_recovery: p0
deployable_actor_boundary: p0
claim_boundary_audit: p0
```

## Supported Claims

- M3108 is complete and claim-safe as a residual failure decomposition artifact set.
- The remaining blocker is residual collision/offtrack hard safety and not speed-floor recovery.
- The next route may materialize an actor-visible direct-action repair that targets the two residual axes while preserving the zero speed-too-low constraint.
- The next route must keep the obs72 to action3 direct `[steer, throttle, brake]` deployment boundary and must not require hidden actor inputs or a runtime base policy.

## Rejected Claims

- M3108 is not a validation result.
- M3108 is not a ranking, winner-selection, checkpoint-mutation, or promotion result.
- M3108 is not a driver-performance, current-sim verdict, robustness-result, repair-success, full-driver, high-fidelity, paper, finite-window-vs-GRU, or self-ID claim.
- M3108 does not prove that a residual repair works because it performs no new environment execution.

## Failure Taxonomy

- `contract_violation`: not observed; the actor-visible obs72/action3 direct-action boundary is preserved.
- `lineage_invalid`: not observed; M3108 derives from M3107/M3106/M3105 and uses row-preserving residual artifacts.
- `metric_artifact`: not observed; summary, residual rows, axis summaries, comparisons, repair requirements, claims, gates, and doc are present.
- `scenario_sampling_failure`: not observed for decomposition; all 64 source rows and 7 residual rows are accounted.
- `behavior_regression`: not measured in M3108 because M3108 does not execute the environment.
- `objective_overfit`: active risk if the next route tunes only known rows without preserving speed-floor and contract guards.
- `proof_washout`: active risk if decomposition is described as repair success.
- `seed_fragility`: unresolved; no broader validation should start before residual collision/offtrack repair is measured.

## Public Gate Overfit Risk

Risk remains medium. M3108 improves the evidence structure by decomposing the residual hard-safety blocker but does not add new closed-loop behavior. A materialization route is justified only as an actor-visible repair artifact preflight followed by audit and same-denominator measurement.

## Next Branch Decision

Route exactly one follow-up to:

```text
m3110-engineering-controller-active-safety-driver-residual-collision-offtrack-actor-visible-repair-materialization-preflight
```

M3110 should materialize a deployable direct-action repair package that:

- starts from the M3103/M3105 no-regression fallback boundary
- targets `collision_lateral_intrusion` and `offtrack_boundary_recovery`
- preserves the M3105 zero speed-too-low result as a hard guard
- emits direct `[steer, throttle, brake]` from actor-visible obs72 only
- registers M3111 result audit before any measurement route

## Boundary

M3109 is a result audit only. It runs no reset, step, rollout, replay, fitting, PPO, training, validation, ranking, promotion, high-fidelity simulation, finite-window-vs-GRU comparison, or self-ID test.
