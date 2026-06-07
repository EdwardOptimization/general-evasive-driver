# M3034 Active Safety Driver v1 Baseline Freeze Design

## Summary

- status: completed
- decision: `active_safety_driver_v1_baseline_freeze_route_to_m3035_contract_materialization`
- branch: `active_safety_driver_v1_engineering_mainline`
- route plan: `docs/active-safety-driver-v1-route-plan.md`
- pivot audit: `docs/m3033-engineering-controller-route-a-post-residual-stop-new-source-broad-failure-target-tensor-materialization-result-audit.md`
- follow-up manifest: `experiments/manifests/m3035-engineering-controller-active-safety-driver-v1-baseline-contract-materialization-preflight.json`
- next: `m3035-engineering-controller-active-safety-driver-v1-baseline-contract-materialization-preflight`

M3034 freezes the Active Safety Driver v1 baseline and benchmark contract before
any training, validation, ranking, promotion, high-fidelity rollout,
finite-window-vs-GRU result, paper claim, or self-ID claim.

The project objective is:

```text
Build and validate a deployable actuator-level active-safety reflex driver.
```

The deployable output remains:

```text
[steer, throttle, brake]
```

## Frozen Actor Contract

The Active Safety Driver v1 actor contract is frozen as:

```text
observation shape: 72
action shape: 3
action semantics: [steer, throttle, brake]
```

Allowed actor-side inputs are only deployable human-view state and history:

```text
ego response
actuator state
previous commands
road geometry
obstacle geometry
finite-window history or recurrent hidden state derived from actor-visible inputs
```

Forbidden actor-side shortcuts remain:

```text
hidden dynamics
mu
slip ratio
tire force
oracle feasibility
TTC labels
reference trajectory
precomputed success/progress/verdict labels
source labels
route labels
outcome labels
target tensor labels or provenance
```

M3034 does not change actor inputs, action outputs, checkpoint files,
controller profiles, environment configs, or training code.

## Baseline Evidence Inputs

The baseline-freeze input surface is limited to already audited, claim-safe
artifacts:

```text
M3033 pivot audit:
  docs/m3033-engineering-controller-route-a-post-residual-stop-new-source-broad-failure-target-tensor-materialization-result-audit.md

Route plan:
  docs/active-safety-driver-v1-route-plan.md

Current diagnostic execution surface:
  runs/m3015_engineering_controller_route_a_post_residual_stop_new_source_bounded_execution_preflight/summary.json
  runs/m3015_engineering_controller_route_a_post_residual_stop_new_source_bounded_execution_preflight/episode_rows.csv
  runs/m3015_engineering_controller_route_a_post_residual_stop_new_source_bounded_execution_preflight/profile_aggregate_rows.csv
  runs/m3015_engineering_controller_route_a_post_residual_stop_new_source_bounded_execution_preflight/source_aggregate_rows.csv

Failure localization surface:
  runs/m3018_engineering_controller_route_a_post_residual_stop_new_source_failure_localization_materialization_preflight/failure_localization_rows.csv

Objective-contract surface:
  runs/m3022_engineering_controller_route_a_post_residual_stop_new_source_broad_failure_objective_contract_materialization_preflight/objective_family_rows.csv
  runs/m3022_engineering_controller_route_a_post_residual_stop_new_source_broad_failure_objective_contract_materialization_preflight/objective_component_rows.csv
  runs/m3022_engineering_controller_route_a_post_residual_stop_new_source_broad_failure_objective_contract_materialization_preflight/row_assignment_rows.csv

Target tensor surface:
  runs/m3032_engineering_controller_route_a_post_residual_stop_new_source_broad_failure_target_tensor_materialization_preflight/summary.json
  runs/m3032_engineering_controller_route_a_post_residual_stop_new_source_broad_failure_target_tensor_materialization_preflight/target_tensor_rows.csv
```

These artifacts can define denominators, fields, exclusions, and candidate
families. They do not themselves establish validation, repair success, driver
performance, current-sim verdict, high-fidelity readiness, paper evidence,
finite-window-vs-GRU evidence, or self-ID evidence.

## Candidate Baselines

M3034 freezes the initial baseline candidate set as a candidate table, not as a
winner table.

```text
candidate_id: route_a_candidate_m2655_mitigation_preserving
role: candidate
checkpoint:
  runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution/checkpoints/m2655_mitigation_preserving_actor_head_repair.pt
config:
  runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution/repair_config_snapshot.json
status:
  allowed for same-case baseline measurement only

candidate_id: route_a_parent_l3_online_gru
role: parent
checkpoint:
  runs/m1674_controller_family_one_seed_public_pilot/profile_runs/L3_online_gru/seed_167400/checkpoint.pt
config:
  runs/m1674_controller_family_one_seed_public_pilot/profile_runs/L3_online_gru/seed_167400/config.json
status:
  allowed for same-case baseline measurement only
```

Future candidate families may be added only after the M3035 contract exists:

```text
L0 current-only actor
L1 one-step feedback actor
L2 finite-window actor at 0.5s / 1.0s / 2.0s
L3 recurrent GRU actor
single-step residual head over the frozen 72x3 contract
sequence-delta head with receding-horizon execute-u0 semantics
K action candidate head
K sequence candidate head
learned safety selector or margin critic
```

No family is selected, ranked, promoted, or rejected by M3034.

## Benchmark Roles

The Active Safety Driver v1 benchmark roles are frozen as contract rows for
M3035 materialization.

```text
ordinary_avoidance:
  obstacle avoidance and road-boundary tracking under the current human-view
  observation contract.

stable_aes:
  evasive steering that avoids collision while preserving road boundary,
  yaw/spin stability, and smooth actuator changes.

aeb_infeasible_evasive_steering:
  cases where braking alone is insufficient and lateral avoidance is required.

hidden_dynamics_robustness:
  actor-visible robustness checks for low grip proxies, actuator delay,
  steering lag, brake authority loss, drive loss, mass/CG shift, sensor noise,
  and perception delay without exposing hidden parameters to the actor.

unavoidable_mitigation:
  cases where full success may be unavailable; measure collision speed,
  clearance margin, off-track severity, and stabilization rather than marking
  all non-success rows as equivalent.

recovery_and_stability:
  recovery from off-track pressure, speed-floor pressure, high sideslip,
  delayed reveal, near-boundary warmup, and close-obstacle windows.
```

The current M3015/M3018 rows already cover useful role seeds:

```text
actuator_delay_step
brake_fade_or_loss_proxy
capability_step_down
capability_step_up
curved_boundary_obstacle
drive_loss_proxy
late_reveal_boundary
ood_low_grip_proxy
ood_mass_shift_proxy
ood_brake_loss_proxy
ood_drive_loss_proxy
sensor_noise_proxy
perception_delay_proxy
steering_lag_proxy
```

M3035 must materialize these as benchmark-role rows with explicit source,
profile, and exclusion status. M3034 does not execute them.

## Metric Families

The official Active Safety Driver v1 metric contract is:

```text
safety:
  success
  collision
  obstacle_collision termination
  off_track termination
  speed_too_low termination
  max-step or truncation status

clearance:
  min_obstacle_clearance
  obstacle_collision_radius
  min_clearance_margin
  p5 / p10 / mean clearance margin once enough rows exist

stability:
  high_sideslip_fraction
  beta_abs_error_mean
  yaw/spin proxy fields when available
  lateral_rmse

recovery:
  recoverability_window_success
  recoverability_window_success_available
  time_to_first_off_track_s
  max_off_track_overshoot
  off_track_severity_proxy

actuation:
  action_rate_mean
  steer/throttle/brake smoothness when raw traces are available
  actuator saturation or mode jump counters when implemented

robustness:
  outcome split by benchmark role, task family, source family, source edge,
  window tag, profile binding, and seed

runtime:
  checkpoint size
  inference latency p50/p95
  memory footprint
  device and batch-size assumptions

unavoidable mitigation:
  collision speed or severity proxy when available
  closest approach and off-track severity under unavoidable rows
```

M3034 allows M3035 to materialize row-level and aggregate contract tables. It
does not declare any success-rate, clearance, stability, runtime, or robustness
winner.

## Known Baseline State

Existing diagnostics are strongly negative but not validation verdicts.

```text
M3015 scheduled workload rows: 32
M3015 episode rows: 32
M3015 failure rows: 0
M3015 diagnostic success rows: 3
M3015 diagnostic collision rows: 5
M3015 diagnostic offtrack rows: 23
M3015 diagnostic speed_too_low rows: 2
M3015 diagnostic termination counts:
  blank: 3
  obstacle_collision: 4
  off_track: 23
  speed_too_low: 2
```

Profile aggregates are report-only:

```text
route_a_candidate_m2655_mitigation_preserving:
  16 scheduled / 16 episode
  0 diagnostic success
  2 diagnostic collision
  13 diagnostic offtrack
  2 diagnostic speed_too_low
  min_clearance_margin_mean: 7.304892735923677
  return_mean: -60.01972418146164

route_a_parent_l3_online_gru:
  16 scheduled / 16 episode
  3 diagnostic success
  3 diagnostic collision
  10 diagnostic offtrack
  0 diagnostic speed_too_low
  min_clearance_margin_mean: 7.103823257262891
  return_mean: 42.78130647945515
```

These rows identify the initial engineering denominator and failure pressure.
They do not rank the two checkpoints or promote a baseline.

## Exclusion Rules

M3035 must explicitly exclude or mark as non-comparable:

```text
stale fixed-source rows outside the current denominator
static/reset-only artifacts
diagnostic-only rows used as validation or performance verdicts
target tensor rows used as closed-loop performance evidence
self-ID proof rows used as engineering baseline rows
paper-only rows used as active-safety denominator rows
rows with hidden/oracle/TTC/reference/progress/verdict actor inputs
rows with source/route/outcome labels actor-visible
rows that mutate checkpoint, config, profile, or actor input contract
rows not paired by same source, same profile role, same seed, and same metric schema
rows from high-fidelity backends before backend, P0 mapping, and action mapping are auditable
```

Target tensors remain offline material only:

```text
M3032 candidate target tensor rows: 29
M3032 success identity zero-target guard rows: 3
M3032 target tensor files: 32
M3032 target_action_delta_abs_max: 0.08
```

They are not a validation denominator and cannot be actor-visible.

## Stop Rules

Stop or pivot before any training or comparison if:

```text
1. The actor 72/action 3 contract cannot be preserved.
2. A candidate requires hidden dynamics, TTC labels, target labels, or oracle fields.
3. The denominator mixes stale, static, diagnostic-only, and live measurement rows.
4. The next milestone would rank or promote checkpoints before M3035 materializes contract rows.
5. The next milestone would train against M3032 tensors before baseline roles and metrics are machine-readable.
6. The route tries to turn self-ID or GRU proof into the main engineering objective again.
7. High-fidelity work starts before backend source/package, P0 observation mapping, and action mapping are auditable.
8. More than two process-only milestones occur before a new measurable engineering table or run.
```

## M3035 Route

M3034 selects exactly one follow-up route:

```text
m3035-engineering-controller-active-safety-driver-v1-baseline-contract-materialization-preflight
```

M3035 must materialize machine-readable tables:

```text
baseline_candidate_rows.csv
benchmark_role_rows.csv
metric_contract_rows.csv
exclusion_rule_rows.csv
actor_contract_guard_rows.csv
claim_boundary_rows.csv
gate_matrix.csv
summary.json
docs/m3035-engineering-controller-active-safety-driver-v1-baseline-contract-materialization-preflight.md
experiments/manifests/m3036-engineering-controller-active-safety-driver-v1-baseline-contract-materialization-result-audit.json
```

M3035 remains a no-training, no-validation, no-ranking materialization preflight.
It may implement a runner that reads the M3034 design and audited M3015/M3018/
M3022/M3032 artifacts, but it must not run environment steps, mutate
checkpoints, select a winner, or claim driver performance.

## Boundary

M3034 does not:

```text
fit residuals
train PPO or BC
run validation
run high-fidelity simulation
compare finite-window versus GRU
rank controllers
promote checkpoints
mutate checkpoint or config files
change actor inputs
expose target labels or provenance to actors
claim repair success
claim driver performance
claim current-sim or high-fidelity verdict
claim paper-level evidence
claim self-ID evidence
```
