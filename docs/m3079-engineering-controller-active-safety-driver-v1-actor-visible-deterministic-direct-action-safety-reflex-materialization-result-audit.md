# M3079 Active Safety Driver v1 Actor-Visible Deterministic Direct-Action Safety-Reflex Materialization Result Audit

## Summary

- status: completed
- decision: `accept_m3078_safety_reflex_materialization_route_to_m3080_same_denominator_measurement_preflight`
- audited milestone: `m3078-engineering-controller-active-safety-driver-v1-actor-visible-deterministic-direct-action-safety-reflex-materialization-preflight`
- next route: `m3080-engineering-controller-active-safety-driver-v1-actor-visible-deterministic-direct-action-safety-reflex-closed-loop-measurement-preflight`

M3079 accepts M3078 as a complete and claim-safe materialization artifact for
the selected actor-visible deterministic direct-action safety-reflex route. It
does not accept M3078 as rollout evidence, validation evidence, ranking,
promotion, repair success, driver performance, high-fidelity readiness, paper
evidence, finite-window-vs-GRU evidence, full-driver completion, or self-ID
evidence.

## Audited Facts

M3078 materialized:

```text
status_pass: true
gate_matrix_pass: true
actor-visible feature contract rows: 6
safety-reflex rule rows: 6
actor-input exclusion rows: 10
measurement admission rows: 12
claim-boundary rows: 19
gate matrix rows: 16
actor contract: observation 72 / action 3
candidate output: direct_action_clipped [steer throttle brake]
runtime_base_policy_required: false
environment reset/step/rollout run: false
fitting/training/PPO run: false
validation/ranking/promotion run: false
forbidden claim made: false
follow-up manifest exists: true
```

M3078 also materialized a callable deterministic direct-action policy skeleton
in `src/autodrift/engineering_controller_active_safety_driver_v1_actor_visible_deterministic_direct_action_safety_reflex_materialization_preflight.py`.
That function maps obs72 to clipped `[steer, throttle, brake]` using only:

```text
ego_response obs[0:5]
actuator_state obs[5:9]
previous_action obs[9:12]
road_left_boundary obs[12:28]
road_right_boundary obs[28:44]
obstacle_slots obs[44:72]
```

The materialized rule families are:

```text
collision approach braking
collision lateral avoidance
offtrack corridor centering
offtrack edge braking
stability damping
bounded direct-action clipping
```

## Supported Claims

M3079 supports only these claims:

```text
M3078 materialized one deterministic obs72-to-action3 safety-reflex policy skeleton
M3078 preserved direct [steer throttle brake] output semantics
M3078 requires no runtime base policy
M3078 excluded hidden/oracle/TTC/target/provenance/source/route/outcome/progress/verdict actor inputs
M3078 defined measurement admission gates before any performance claim
M3078 registered M3079 result audit
M3078 kept validation/ranking/promotion/driver-performance/high-fidelity/paper/full-driver/repair-success/self-ID claims out of scope
```

## Rejected Claims

M3079 rejects these interpretations:

```text
M3078 proves the deterministic safety-reflex driver performs well
M3078 repairs the M3067/M3075 same-denominator failure surface
M3078 is a validation result or current-sim verdict
M3078 is a ranking, winner-selection, or promotion result
M3078 establishes high-fidelity readiness
M3078 provides paper, finite-window-vs-GRU, full-driver, repair-success, or self-ID evidence
```

## Next Route

M3079 routes exactly one follow-up:

```text
m3080-engineering-controller-active-safety-driver-v1-actor-visible-deterministic-direct-action-safety-reflex-closed-loop-measurement-preflight
```

M3080 must execute the M3078 deterministic safety-reflex policy as the full
obs72-to-action3 actor on the same 32-row denominator used by M3067/M3075
unless a separate pre-registered manifest changes the denominator before
execution.

M3080 must report:

```text
success rows
collision rows
offtrack rows
speed-too-low rows
clearance margin mean and row distribution
stability and recovery rows
raw action pressure
final action bounds
action clip fraction
actor-contract guards
claim-boundary guards
```

M3080 must not claim validation, ranking, promotion, driver performance,
current-sim verdict, repair success, high-fidelity readiness, paper evidence,
finite-window-vs-GRU evidence, full-driver completion, or self-ID.

## Boundary

M3079 is a result audit only. It runs no reset, step, rollout, replay, fitting,
PPO, training, validation, ranking, promotion, high-fidelity simulation,
finite-window-vs-GRU comparison, or self-ID test.
