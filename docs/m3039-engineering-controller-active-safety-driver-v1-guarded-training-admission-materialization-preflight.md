# M3039 Active Safety Driver v1 Guarded Training Admission Materialization Preflight

## Summary

- status: completed
- decision: `active_safety_driver_v1_guarded_training_admission_materialized_route_to_m3040_result_audit`
- objective rows: 10
- scenario panel rows: 17
- training guardrail rows: 8
- baseline pressure rows: 36
- target tensor rows: 29
- actor contract guard pass: True
- claim boundary pass: True
- gate matrix pass: True
- follow-up manifest: `experiments/manifests/m3040-engineering-controller-active-safety-driver-v1-guarded-training-admission-materialization-result-audit.json`

## Objectives

### collision_avoidance

- metric family: safety
- source metrics: collision|obstacle_collision_termination
- baseline pressure: 5/32 baseline collision rows
- training use: penalize obstacle collision and collision flags
- optimization: minimize
- guardrail: collision guardrail

### road_boundary_retention

- metric family: safety
- source metrics: off_track_termination|max_off_track_overshoot
- baseline pressure: 23/32 baseline off-track rows
- training use: penalize off-track termination and overshoot
- optimization: minimize
- guardrail: off-track guardrail

### speed_floor_retention

- metric family: safety
- source metrics: speed_too_low_termination
- baseline pressure: 2/32 baseline speed-floor rows
- training use: penalize unsafe speed-floor collapse
- optimization: minimize
- guardrail: speed-floor guardrail

### clearance_margin

- metric family: clearance
- source metrics: min_obstacle_clearance|min_clearance_margin
- baseline pressure: min_clearance_margin_min=-0.24160113106273284
- training use: increase clearance margin while preserving road boundary
- optimization: maximize
- guardrail: clearance guardrail

### yaw_sideslip_stability

- metric family: stability
- source metrics: high_sideslip_fraction|beta_abs_error_mean|lateral_rmse
- baseline pressure: high_sideslip_fraction_mean=0.296771958597116
- training use: penalize high sideslip and lateral instability
- optimization: minimize
- guardrail: stability guardrail

### recovery_after_pressure

- metric family: recovery
- source metrics: recoverability_window_success|time_to_first_off_track_s|max_off_track_overshoot
- baseline pressure: recoverability availability currently sparse; keep fields explicit
- training use: reward recovery from boundary and hazard pressure when instrumented
- optimization: maximize
- guardrail: recovery instrumentation guardrail

### actuation_smoothness

- metric family: actuation
- source metrics: action_rate_mean
- baseline pressure: action_rate_mean=0.007109280508302618
- training use: regularize steer throttle brake rate without suppressing evasive action
- optimization: minimize
- guardrail: mode-jump guardrail

### role_robustness_balance

- metric family: robustness
- source metrics: benchmark_roles|role_seed_matches|task_family|source_edge|window_tag
- baseline pressure: role-split aggregates available from M3037
- training use: preserve role-balanced sampling across ordinary avoidance, stable AES, and robustness seeds
- optimization: balance
- guardrail: role overfit guardrail

### success_identity_guard

- metric family: guard
- source metrics: success|truncated|terminated
- baseline pressure: 3/32 baseline success rows
- training use: do not turn successful baseline behavior into positive residual targets or regressions
- optimization: preserve
- guardrail: success identity guardrail

### target_tensor_trainer_context

- metric family: trainer_context
- source metrics: target_tensor_rows|target_action_delta|target_valid_mask|target_loss_weight
- baseline pressure: 29 offline target tensor rows available
- training use: allow offline trainer-side target context only after audit; never actor-visible
- optimization: bounded_hint
- guardrail: target actor-invisibility guardrail

## Interpretation

M3039 materializes trainer-side Active Safety Driver v1 admission tables from the accepted baseline measurement chain. The tables define objective families, scenario panels, pressure surfaces, and guardrails for a later bounded fitting or PPO route. They do not train, validate, rank, promote, mutate checkpoints, or claim driver performance.

Rejected claims:

```text
training execution, fitted policy quality, validation result, driver-performance verdict, checkpoint ranking, winner selection, promotion, repair success, current-sim verdict, high-fidelity validation readiness or result, finite-window-vs-GRU conclusion, paper evidence, full ideal driver completion, or level3 self-identification
```

## Boundary

M3039 does not reset, step, roll out, replay, fit, run PPO, train, validate, rank, promote, mutate checkpoints, run high-fidelity simulation, compare finite-window versus GRU, or use target tensors as actor-visible labels.

## Next

- next blocker: `m3040-engineering-controller-active-safety-driver-v1-guarded-training-admission-materialization-result-audit`
- selected next action: `m3040-engineering-controller-active-safety-driver-v1-guarded-training-admission-materialization-result-audit`
