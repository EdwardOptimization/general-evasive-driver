# M3111 Residual Collision/Offtrack Actor-Visible Repair Materialization Result Audit

## Audit Decision

- decision: `accept_m3110_materialization_route_to_m3112_full_fresh_measurement_preflight`
- audit status: `accepted_for_measurement_admission`
- M3110 status_pass: `True`
- M3110 gate_matrix_pass: `True`
- required artifacts present: `True`
- policy id: `m3110_residual_collision_offtrack_actor_visible_repair`
- source residual rows: `7`
- source residual collision rows: `5`
- source residual offtrack rows: `2`
- source residual speed-too-low rows: `0`
- rule rows: `6`
- residual repair guard rows: `7`
- actor-input exclusion rows: `10`
- claim-boundary rows: `21`
- selected next action: `m3112-engineering-controller-active-safety-driver-residual-collision-offtrack-actor-visible-repair-full-fresh-measurement-preflight`

## Evidence Summary

M3110 materializes an actor-visible direct-action repair package from the M3108 residual decomposition and M3109 audit. It runs no environment execution and makes no measurement or repair-success claim.

The materialized package preserves the deployment contract:

```text
input: actor-visible obs72 only
output: direct action3 [steer, throttle, brake]
runtime_base_policy_required: false
checkpoint_model_required: false
recurrent_hidden_state_required: false
hidden/oracle/TTC/target/source/route/outcome/progress/verdict actor input: forbidden
```

M3110 covers the M3108 repair requirements:

```text
collision_lateral_intrusion_guard
offtrack_boundary_recovery_guard
speed_floor_preservation
residual_collision_reduction
residual_offtrack_recovery
deployable_actor_boundary
claim_boundary_audit
```

The probe gates remain API and materialization checks only:

```text
low_speed_probe_throttle: -0.37863999605178833
residual_high_speed_obstacle_probe_brake: 0.8299338221549988
residual_high_speed_edge_probe_brake: -0.5046315789222717
```

## Supported Claims

- M3110 is complete and claim-safe as a residual repair materialization artifact set.
- The M3110 callable action function preserves obs72 to direct action3 `[steer, throttle, brake]`.
- M3110 materializes actor-visible rules for residual collision/offtrack pressure while preserving the speed-floor guard as a named measurement requirement.
- M3110 is admissible to a same-denominator full-fresh measurement preflight after this audit.

## Rejected Claims

- M3110 is not a measurement result.
- M3110 is not a validation result.
- M3110 is not a ranking, winner-selection, checkpoint-mutation, or promotion result.
- M3110 is not a driver-performance, current-sim verdict, robustness-result, repair-success, full-driver, high-fidelity, paper, finite-window-vs-GRU, or self-ID claim.
- M3110 does not prove collision/offtrack reduction until M3112 executes the same-denominator measurement.

## Failure Taxonomy

- `contract_violation`: not observed; obs72/action3 direct-action and hidden-input exclusion gates pass.
- `lineage_invalid`: not observed; M3110 routes from M3109/M3108/M3105/M3103.
- `metric_artifact`: not observed; config, rule, residual guard, exclusion, claim, gate, doc, and M3111 manifest artifacts are present.
- `scenario_sampling_failure`: not measured in M3110 because no rollout executes.
- `behavior_regression`: unresolved until M3112 measures the same denominator.
- `objective_overfit`: active risk if M3112 improves known residual rows while reopening speed-floor or broad safety behavior.
- `proof_washout`: active risk if M3110 materialization probes are described as repair success.
- `seed_fragility`: unresolved; same-denominator measurement is required before broader validation.

## Public Gate Overfit Risk

Risk is medium. M3110 changes the deployable action rule but has not yet produced closed-loop evidence. The next step must measure the same 64-row denominator and report success, collision, offtrack, speed-too-low, clearance, action, and same-row deltas against M3105/M3095/M3100 before any broader claim.

## Next Branch Decision

Route exactly one follow-up to:

```text
m3112-engineering-controller-active-safety-driver-residual-collision-offtrack-actor-visible-repair-full-fresh-measurement-preflight
```

M3112 should execute M3110 as the full obs72-to-action3 action source on the complete M3084 fresh denominator and compare against M3105, M3095, M3100, and M3090. The hard gates remain:

- residual collision count must be reported separately
- residual offtrack count must be reported separately
- speed-too-low must remain `0`
- actor contract and hidden-input exclusion gates must pass
- no validation, ranking, promotion, repair-success, current-sim verdict, high-fidelity, paper, full-driver, robustness-result, or self-ID claim may be made before result audit

## Boundary

M3111 is a result audit only. It runs no reset, step, rollout, replay, fitting, PPO, training, validation, ranking, promotion, high-fidelity simulation, finite-window-vs-GRU comparison, or self-ID test.
