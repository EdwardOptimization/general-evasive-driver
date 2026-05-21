# M104 Minimum Observable Input Contract

Source: `/home/quyaonan/workspace/AutoDrift - 项目评估分析.mhtml`,
snapshot saved 2026-05-21 23:50 +0800.

This is a design and experiment-protocol note, not a completed training result.
It preserves the latest input discussion so future work does not drift back
toward engineered diagnostics or oracle-like actor features.

## Decision

The deployable actor input should be sensor-direct or minimally
calibrated/fused. It should not receive diagnostic ratios, controller mode
flags, hidden simulator parameters, or planner answers.

The minimum closed-loop observability chain is:

```text
known commands
-> actual actuator feedback
-> wheel/tire raw response when available
-> body inertial response
-> road and obstacle geometry
```

The reason is command-response observability. Without commands, weak response
cannot distinguish "no control was requested" from "control was requested but
the vehicle could not deliver it." Without actuator actuals, weak response
cannot distinguish actuator lag from tire or road limits.

## Minimum Observable Set

The ideal four-wheel minimum response branch is:

```text
commands:
  steer_cmd
  brake_cmd
  drive_cmd

actual actuator feedback:
  actual_steering_angle
  actual_brake_actuator_state
  actual_drive_actuator_state

wheel raw:
  Romega_fl
  Romega_fr
  Romega_rl
  Romega_rr

local ground-speed fusion:
  v_parallel_fl
  v_parallel_fr
  v_parallel_rl
  v_parallel_rr

body inertial response:
  ax
  ay
  yaw_rate

scene branch:
  road_boundary_points
  obstacle_present
  obstacle_x_ego
  obstacle_y_ego
  obstacle_width
  obstacle_length
```

`Romega_i` is wheel circumferential speed. `v_parallel_i` is the local
contact-patch ground speed along the wheel rolling direction, produced by a
low-level ego-motion fusion path. It must not be the vehicle-center speed and
must not be the average of wheel speeds.

For the current single-track simulator, the temporary profile is only:

```text
Romega_front
Romega_rear
v_parallel_front
v_parallel_rear
```

This approximation is not strong enough to close the four-wheel sensor question.
M92 rejected the current single-track local-ground-speed profiles as primary
PPO inputs, but that is not evidence that real four-wheel wheel sensing is
useless.

## Do Not Feed Slip Ratio

Do not feed actor:

```text
slip_ratio
slip_angle
slip_proxy
ABS_active
TCS_active
ESC_active
tire_saturation_label
friction_circle_margin
true_tire_force
true_normal_load
mu
oracle feasibility
reference trajectory
```

Slip ratio is a diagnostic quantity with state-dependent division:

```text
(Romega_i - v_parallel_i) / v_parallel_i
```

That introduces low-speed singularities, epsilon and clip choices, sign
switching, and distribution artifacts in lockup, spin, and drift-onset cases.
If a wheel-speed difference is ever tested, it should be an optional fixed-scale
affine feature:

```text
(Romega_i - v_parallel_i) / fixed_v_scale
```

M92 already tested the front/rear version of this fixed-scale error and found it
harmful in the current setup, so it is not a primary input.

## Optional Sensor Branches

Optional sensors need admission gates before entering the final actor:

```text
v_perp_fl/fr/rl/rr
steering_torque or EPS motor current
roll_rate, pitch_rate, vertical_acceleration
suspension_travel_fl/fr/rl/rr
sensor confidence or covariance
road-surface perception embedding
```

These are allowed only if they are sensor-direct or low-level fused signals and
they improve held-out evidence without weakening the self-identification claim.

Admission criteria:

```text
1. future-envelope probe accuracy improves;
2. held-out RL success or clearance margin improves;
3. wrong-history counterfactual degradation becomes clearer, not weaker;
4. noise, delay, and calibration error do not collapse the result;
5. the signal is not a hidden parameter, controller flag, or oracle label.
```

## Experiment Ladder

The input comparison should be run in this order:

```text
A. supervised information-observability probes
B. minimum-set sensor ablations
C. frozen-recipe RL profile comparison
D. matched hidden-dynamics wrong-history counterfactuals
E. optional-sensor admission gates
```

Probe profiles:

```text
P0: no-wheel minimal
P1: minimum set with Romega and v_parallel
P2: P1 + steering torque or EPS current
P3: P1 + roll/pitch/vertical acceleration
P4: P1 + suspension travel
P5: P1 + all current optional sensors
```

Wheel-specific ablation profiles:

```text
P1a: Romega only
P1b: Romega + v_parallel
P1c: Romega + v_parallel + v_perp
P1d: Romega + v_parallel + fixed-scale speed error
```

The main probe targets should be future handling-envelope quantities, not `mu`:

```text
future_braking_deceleration
future_yaw_response
future_lateral_acceleration_response
future_speed_loss_under_brake_pulse
future_yaw_rate_under_steer_pulse
stable_AES_feasibility
drift_AES_feasibility
AEB_feasibility
```

History windows should include current frame only and short histories:

```text
0.0 s
0.2 s
0.5 s
1.0 s
2.0 s
```

Expected self-ID pattern:

```text
current frame only is weaker;
0.5-1.0 s history improves future-envelope prediction;
wheel/local-ground-speed profiles improve earlier than no-wheel profiles if
the wheel sensors are actually useful.
```

## Reliability Rule

Do not tune PPO separately for each input profile. The reliable sequence is:

```text
1. use supervised probes to reject clearly weak profiles;
2. find one stable PPO recipe on the strongest plausible profile;
3. freeze reward, curriculum, network size, auxiliary losses, seeds, budget,
   and evaluation corpus;
4. train the compared profiles under that same recipe;
5. continue iteration only from the best profile after the comparison closes.
```

All paper-grade comparisons must keep the run artifacts, configs, seeds,
checkpoints, probe summaries, ablation summaries, and decision notes. The final
claim should be based on the frozen comparison, not on differently tuned runs.

## Current Project Implication

M91/M92 keep the no-wheel human-view driver as the primary PPO actor input for
now. The current single-track wheel profiles are not admitted.

The next wheel-sensor attempt should not reintroduce slip ratio, slip proxy,
ABS/TCS/ESC flags, or per-wheel brake-pressure split as actor inputs. It should
either:

```text
1. add a true four-wheel or richer wheel-contact model, then rerun M104 probes;
2. or build a matched corpus where current body response is ambiguous but raw
   wheel/contact response changes the future-envelope target.
```

Until then, M103 remains the active no-wheel actor-coupling path.
