# M3040 Active Safety Driver v1 Guarded Training Admission Materialization Result Audit

## Summary

- status: completed
- decision: `accept_m3039_guarded_training_admission_route_to_m3041_bounded_residual_fitting_preflight`
- audited milestone: `m3039-engineering-controller-active-safety-driver-v1-guarded-training-admission-materialization-preflight`
- next route: `m3041-engineering-controller-active-safety-driver-v1-bounded-residual-fitting-preflight`

M3040 accepts M3039 as a complete and claim-safe guarded training-admission
materialization. It does not accept M3039 as fitting, PPO training, validation,
driver performance, ranking, promotion, current-sim verdict, high-fidelity
readiness, paper evidence, finite-window-vs-GRU evidence, full driver
completion, or self-ID evidence.

## Artifact Audit

Accepted M3039 facts:

```text
status_pass: true
gate_matrix_pass: true
objective rows: 10
scenario panel rows: 17
training guardrail rows: 8
baseline pressure rows: 36
actor contract guard rows: 5
claim boundary rows: 11
target tensor rows: 29
target tensors trainer-side only: true
actor contract: 72/action 3
reset/step/rollout/replay/fitting/PPO/training/validation/ranking/promotion: false
driver-performance/current-sim/high-fidelity/paper/self-ID claims: false
```

Required M3039 artifacts were present:

```text
runs/m3039_engineering_controller_active_safety_driver_v1_guarded_training_admission_materialization_preflight/summary.json
runs/m3039_engineering_controller_active_safety_driver_v1_guarded_training_admission_materialization_preflight/active_safety_training_objective_rows.csv
runs/m3039_engineering_controller_active_safety_driver_v1_guarded_training_admission_materialization_preflight/scenario_panel_rows.csv
runs/m3039_engineering_controller_active_safety_driver_v1_guarded_training_admission_materialization_preflight/training_guardrail_rows.csv
runs/m3039_engineering_controller_active_safety_driver_v1_guarded_training_admission_materialization_preflight/baseline_pressure_rows.csv
runs/m3039_engineering_controller_active_safety_driver_v1_guarded_training_admission_materialization_preflight/actor_contract_guard_rows.csv
runs/m3039_engineering_controller_active_safety_driver_v1_guarded_training_admission_materialization_preflight/claim_boundary_rows.csv
runs/m3039_engineering_controller_active_safety_driver_v1_guarded_training_admission_materialization_preflight/gate_matrix.csv
docs/m3039-engineering-controller-active-safety-driver-v1-guarded-training-admission-materialization-preflight.md
experiments/manifests/m3040-engineering-controller-active-safety-driver-v1-guarded-training-admission-materialization-result-audit.json
```

## Admission Surface

M3039 provides the minimum training-admission surface needed for a bounded
offline residual fitting step:

```text
active-safety objective families:
  collision_avoidance
  road_boundary_retention
  speed_floor_retention
  clearance_margin
  yaw_sideslip_stability
  recovery_after_pressure
  actuation_smoothness
  role_robustness_balance
  success_identity_guard
  target_tensor_trainer_context

scenario roles:
  17 benchmark-role seed rows

trainer-side target context:
  29 M3032 positive residual target tensor rows
  3 M3032 success identity zero-target guard rows
```

The target tensors have matching deployable traces:

```text
raw observation trace shape: Nx72
target action delta shape: Nx3
target labels/provenance actor-visible: false
```

This supports a bounded offline residual fitting preflight. It does not support
closed-loop repair-success, policy-quality, validation, ranking, or promotion
claims.

## Rejected Claims

M3040 explicitly rejects:

```text
fitting or PPO has already happened
training success
validation result
driver-performance verdict
current-sim verdict
checkpoint ranking
winner selection
checkpoint promotion
repair success
high-fidelity validation readiness or result
finite-window-vs-GRU conclusion
paper evidence
full ideal driver completion
level3 self-identification
```

## Route Decision

M3040 selects exactly one next route:

```text
m3041-engineering-controller-active-safety-driver-v1-bounded-residual-fitting-preflight
```

The M3041 route is allowed to do bounded offline fitting of a deployable
residual/reflex layer from actor-visible raw observation traces and
actor-invisible trainer-side target deltas. It must output a candidate artifact
whose runtime contract is:

```text
input: observation vector shape 72
output: action residual shape 3
bounded composition: [steer, throttle, brake] + residual, clipped to action bounds
```

M3041 remains forbidden from environment rollout, validation, ranking,
promotion, checkpoint mutation, high-fidelity simulation, finite-window-vs-GRU
comparison, paper claims, and self-ID claims. Any fitted artifact from M3041 is
a candidate for later audit and closed-loop measurement only.

## Boundary

M3040 does not run reset, step, rollout, replay, fitting, PPO, training,
validation, ranking, promotion, high-fidelity simulation, finite-window-vs-GRU
comparison, or self-ID testing. It only audits M3039 and registers M3041.
