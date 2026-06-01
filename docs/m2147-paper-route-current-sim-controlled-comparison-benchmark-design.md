# M2147 Paper-Route Current-Sim Controlled Comparison Benchmark Design

- status: completed
- decision: `current_sim_controlled_comparison_benchmark_design_admit_spec_preflight_implementation`
- manifest: `experiments/manifests/m2147-paper-route-current-sim-controlled-comparison-benchmark-design.json`
- reset/rollout/measured execution in M2147: `false`
- policy actions executed in M2147: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- winner selected: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Design Principle

M2146 closes the generated-proxy comparison-support branch as useful
scaffolding, not as paper evidence. M2147 starts the next branch with a stricter
principle:

```text
first freeze the current-simulator benchmark contract,
then materialize specs,
then reset-validate,
then execute,
then audit,
then compare.
```

No profile ranking or finite-window-vs-GRU verdict is allowed until the same
current-sim benchmark has been executed and audited under this contract.

## Controller Matrix

All variants must preserve the same deployable actor boundary and actuator-level
action:

```text
u_t = [steer_command, throttle_command, brake_command]
```

Deployable inputs may include ego response, IMU-like signals, actuator states,
previous physical commands, road/free-space/obstacle geometry in ego frame, and
history represented either explicitly or recurrently. Hidden parameters, slip,
tire forces, oracle labels, controller mode, TTC, reference trajectory, path
error, heading error, required clearance, collision/success/progress labels, or
other precomputed answers remain forbidden.

Primary profiles for the first benchmark pack:

```text
L0_current_masked
L1_one_step
L2_window_13
L2_window_25
L2_window_50
L2_window_100
L3_online_gru
L3_reset_control
```

Profile roles:

```text
L0: current-response lower-bound control.
L1: one-step command/actuator feedback.
L2: finite-window engineering challengers at multiple practical windows.
L3 online: recurrent controller candidate.
L3 reset: recurrent architecture control for hidden-memory interpretation.
```

The first comparison must report parameter count, observation contract, history
length, recurrent state use, reset/truncation behavior, and inference budget for
each profile. M2147 does not compute these values; it requires M2148 to preserve
the metadata in a preflight artifact.

## Task Families

The first current-sim controlled benchmark should use five task families from
the governing paper-route plans:

```text
T1_reactive_emergency_avoidance:
  ordinary emergency avoidance where current response should be strong.

T2_delayed_actuator_response:
  delayed or weak actuator/ego response where one-step feedback may be too short.

T3_diagnostic_warmup_obstacle_reveal:
  low-risk warmup before obstacle reveal to test whether history is usable.

T4_same_current_different_older_history:
  matched current and recent-window state with older diagnostic history varied.

T5_terminal_boundary_near_constraint:
  near-boundary avoidance where small action/history differences can change the
  terminal outcome.
```

T1 primarily supports the engineering driver-performance claim. T2-T5 are the
mechanism-sensitive families. Strong self-identification claims require
source-diverse outcome-relevant positives in T4/T5; aggregate T1 success is not
enough.

## Metrics

Primary outcome metrics:

```text
success_rate
collision_rate
road_departure_rate
spin_rate
clearance_margin_tail
terminal_margin_tail
recovery_after_maneuver
control_smoothness
```

Mechanism metrics:

```text
first_critical_action_gap
short_horizon_maneuver_gap
future_braking_authority_prediction
future_yaw_authority_prediction
adaptation_latency
wrong_history_margin_gap
delayed_history_margin_gap
reset_or_truncated_history_margin_gap
source_diversity
max_single_source_share
```

M2148 should materialize these as required or deferred fields. It must not
silently approximate unsupported metrics. Unsupported metrics must be explicit
gaps with a route to instrumentation or a narrower benchmark claim.

## Claim Ladder

The branch must use the weakest claim supported by evidence:

```text
Claim A: deployable feedback driver.
Claim B: history-conditioned output feedback.
Claim C: recurrent belief advantage.
Claim D: strong self-identification.
```

Claim C requires L3 online to beat matched finite-window profiles and reset
controls on the relevant task families under fair budgets.

Claim D requires wrong/delayed/reset/mismatched history interventions to degrade
first-critical action or terminal outcome on source-diverse T4/T5 cases.

If L1 or L2 matches L3, the result is still useful: the paper route becomes a
simpler deployable finite-window/current-response driver with a negative or
conditional self-ID finding.

## Spec Preflight Requirements

M2148 should implement a no-rollout benchmark-spec preflight that writes one
machine-readable spec artifact before any reset or measured execution.

Minimum fields per benchmark spec:

```text
benchmark_spec_id
task_family
claim_level_target
scenario_source
source_kind
difficulty_band
dynamics_band
obstacle_timing_band
road_geometry_band
history_requirement
primary_metrics
mechanism_metrics
paper_validity_status
generated_proxy_source
profile_specific_tuning
forbidden_actor_input_flags
reset_validation_required
measured_execution_required
private_holdout_policy
```

Minimum profile matrix fields:

```text
profile_name
profile_level
history_representation
history_window_steps
uses_recurrent_state
reset_or_truncated_control
observation_dim
action_contract
actor_input_contract_hash_or_label
profile_specific_tuning
```

The first preflight can be small and schema-focused. It should not run reset or
rollout. Its pass condition is a clean benchmark contract, not performance.

## Stop Conditions

Stop or synthesize instead of executing if:

```text
the spec cannot separate generated-proxy scaffolding from current-sim benchmark tasks;
the profile matrix omits reset/truncated controls;
L2 finite-window variants are missing;
task families collapse into only reactive T1 scenarios;
unsupported mechanism metrics are silently approximated;
any forbidden actor input enters the deployed profile contract;
the route jumps directly to ranking before reset validation and measured audit.
```

## Next

Immediate next milestone:

```text
m2148-paper-route-current-sim-controlled-comparison-benchmark-spec-preflight-implementation
```

M2148 should materialize the design into a schema-level benchmark spec artifact
and profile matrix without reset, rollout, measured execution, training, replay,
PPO, ranking, or paper interpretation.
