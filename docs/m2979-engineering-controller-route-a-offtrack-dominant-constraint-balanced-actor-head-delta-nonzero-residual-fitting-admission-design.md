# M2979 Engineering Controller Route A Actor-Head Delta Nonzero Residual Fitting Admission Design

## Metadata

- status: completed
- decision: `reject_direct_nonzero_residual_fitting_route_to_m2980_residual_target_materialization_design`
- manifest: `experiments/manifests/m2979-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-nonzero-residual-fitting-admission-design.json`
- parent audit: `docs/m2978-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-deployable-trace-capture-result-audit.md`
- parent trace capture: `runs/m2977_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_deployable_trace_capture_preflight/summary.json`
- parent training admission: `runs/m2970_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_nonzero_residual_training_admission_materialization_preflight/summary.json`
- parent objective materialization: `runs/m2966_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_nonzero_residual_objective_materialization_preflight/summary.json`
- follow-up manifest: `experiments/manifests/m2980-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-nonzero-residual-target-materialization-design.json`
- next: `m2980-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-nonzero-residual-target-materialization-design`

## Design Decision

M2979 rejects direct nonzero residual fitting after M2977 and admits one
target-materialization design route.

Formal decision:

```text
reject_direct_nonzero_residual_fitting_route_to_m2980_residual_target_materialization_design
```

The M2977 raw actor-view traces clear the previous raw-trace availability
blocker, but they do not define numeric residual deltas, teacher actions,
per-step target labels, target masks, loss weights, or a fitting denominator.
The M2966/M2970 artifacts define objective families and guarded admission
rows, but their target signals are still trainer-side context names and are not
actor-visible labels or fitted targets.

Therefore M2979 does not admit fitting. It routes to M2980 to design a bounded
target-materialization step before any residual fitting, training, validation,
ranking, promotion, repair-success, performance, paper, current-sim,
high-fidelity, full-driver, finite-window-vs-GRU, or self-ID claim.

## Evidence Review

M2978 accepts M2977 raw trace capture as complete and claim-safe:

```text
raw trace index rows: 56
future training candidate raw traces: 43
success identity raw traces: 13
stale guardrails protected: 11
stale guardrails executed: 0
actor observation/action: 72/action 3
raw trace tensors finite: true
residual delta abs max: 0.0
zero residual identity mode: true
```

M2966 and M2970 preserve the objective/admission accounting:

```text
objective families: 4
objective components: 4
row assignments: 56
training candidates: 43
success identity guards: 13
stale guardrails: 11
collision candidates: 7
offtrack candidates: 35
speed-floor candidates: 1
```

The accepted candidate families are:

```text
collision_clearance_residual_objective
offtrack_recovery_residual_objective
speed_floor_context_guard_objective
```

The success rows remain:

```text
success_identity_guard
```

## Direct Fitting Readiness Audit

M2979 rejects direct fitting because the current artifacts do not yet provide:

```text
per-step residual delta targets: absent
teacher action targets: absent
target validity masks: absent
target loss weights: absent
target generation provenance: absent
candidate-to-target denominator: absent
success-identity zero-target contract: not materialized as target rows
stale-guardrail exclusion contract: not materialized as target rows
```

The M2970 `target_signal` values are trainer-side context descriptors:

```text
trainer_side_clearance_context_not_actor_input
trainer_side_offtrack_recovery_context_not_actor_input
trainer_side_speed_floor_context_not_actor_input
trainer_side_success_identity_context_not_actor_input
```

Those descriptors can inform a later target-materialization design, but they
are not numeric action-delta labels and cannot be used as direct fit targets.

## Actor And Guard Boundaries

M2979 preserves the existing actor and guard boundaries:

```text
actor observation/action: 72/action 3
hidden/oracle actor input: rejected
future-target actor input: rejected
objective/admission/trace-readiness/verdict labels actor-visible: rejected
success identity guards as positive residual targets: rejected
stale fixed-source guardrail execution: rejected
stale fixed-source guardrails as training/validation/paper denominators: rejected
```

M2980 may design trainer-side target materialization, but any generated targets
must remain outside actor inputs and must carry row-level provenance, masks,
and claim boundaries.

## Supported Claims

M2979 supports only:

```text
M2977 raw actor-view trace capture is available for 43 future training
candidates and 13 success identity guards.

M2966/M2970 objective and admission artifacts identify candidate families and
guard families, but do not yet define numeric residual fitting targets.

Direct nonzero residual fitting remains blocked until target materialization
semantics are designed and audited.

The next admissible route is M2980 target-materialization design.
```

These are design and blocker claims only.

## Rejected Claims

M2979 rejects:

```text
direct nonzero residual fitting after M2977: false
nonzero residual target labels already materialized: false
residual fitting executed: false
residual training executed: false
validation/ranking/promotion executed: false
repair success proved: false
driver performance improved: false
paper/current-sim/high-fidelity/full-driver/finite-window-vs-GRU/self-ID evidence produced: false
```

## M2980 Route Contract

M2979 selects exactly one next route:

```text
m2980-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-nonzero-residual-target-materialization-design
```

M2980 must be design-only. It must decide whether to admit a bounded target
materialization preflight, pivot, synthesize, or stop. If it admits target
materialization, it must define:

```text
target source and provenance
per-objective target semantics
target tensor shape and dtype
target validity masks
target loss weights
success identity zero-target guard contract
stale guardrail exclusion contract
actor-input exclusion contract
claim-boundary artifact contract
```

M2980 must not fit, train, validate, rank, select, promote, mutate checkpoints,
or claim repair success, performance, paper evidence, current-sim evidence,
high-fidelity evidence, finite-window-vs-GRU evidence, full-driver completion,
or self-ID evidence.
