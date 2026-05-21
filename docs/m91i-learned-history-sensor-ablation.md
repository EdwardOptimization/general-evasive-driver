# M91-I Learned-History Sensor Ablation

M91-I uses the regularized learned-history probe from M91-H to ablate response
channel groups. The goal is to identify which deployable inputs explain the
history benefit before returning to PPO.

This is still not PPO and not a promoted driver.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src conda run -n autodrift python -m autodrift.learned_history_observability_probe \
  --env-config configs/m91c_raw_wheel_minimum_profile.json \
  --episodes 40 \
  --seed 9380 \
  --policy heuristic \
  --horizon-steps 15 \
  --sample-stride 3 \
  --max-samples 1000 \
  --history-window 50 \
  --device cpu \
  --epochs 30 \
  --hidden-size 24 \
  --weight-decay 0.001 \
  --profile-set ablation \
  --run-dir runs/m91i_learned_history_sensor_ablation_seed9380
```

Artifacts:

```text
runs/m91i_learned_history_sensor_ablation_seed9380/samples.csv
runs/m91i_learned_history_sensor_ablation_seed9380/probe_summary.csv
runs/m91i_learned_history_sensor_ablation_seed9380/summary.json
runs/m91i_learned_history_sensor_ablation_seed9380/manifest.json
```

The run collected `715` sampled states, with an episode-disjoint split of `496`
train samples and `219` test samples.

## Held-Out R2

| profile | braking | yaw | lateral accel |
| --- | ---: | ---: | ---: |
| p0 current ridge | -0.079254 | 0.232854 | 0.099297 |
| p1 current ridge | -0.054407 | 0.218259 | 0.119797 |
| p1 response-history GRU | -0.090126 | 0.181417 | 0.276534 |
| p1 no commands history | -0.111095 | 0.131383 | 0.333696 |
| p1 no actuator actuals history | -0.127051 | 0.099339 | 0.328219 |
| p1 no IMU history | -0.038597 | 0.074390 | 0.432747 |
| p1 no wheel history | 0.053848 | 0.214547 | 0.441456 |

## Interpretation

M91-I is a negative result for admitting the current raw wheel branch.

Key observations:

- `p1_no_wheel_history` is the best learned-history profile on braking and
  lateral response, and it is close to the current-frame yaw baseline.
- Removing wheel channels improves all three targets relative to full P1
  history in this run.
- Removing commands or actuator actuals hurts yaw, which supports keeping
  previous command and low-level actuator-state inputs.
- Removing IMU hurts yaw but improves lateral response, so IMU treatment needs
  noise/delay care rather than blind expansion.

## Decision

Do not admit the current raw wheel branch into the primary driver input.

For the next PPO-facing profile, keep the clean no-wheel human-view response
stream:

```text
vx
vy
yaw_rate
ax
ay
steer_angle
steer_rate
throttle_actuator_state
brake_actuator_state
previous_steer_cmd
previous_throttle_cmd
previous_brake_cmd
road/obstacle geometry context
```

The raw wheel branch can remain as an experimental optional sensor, but M91-I
does not justify using it as the primary self-identification input.

This result is scoped to the current `front_rear_raw` single-track proxy. It
does not prove that physically correct wheel-speed sensing is useless. A future
wheel profile should test the raw components:

```text
Romega_i
v_parallel_i
optional v_perp_i
```

and must not input `slip_ratio` or compute ground speed from wheel-speed
averages. That follow-up is recorded in
`docs/m92-local-wheel-ground-speed-input-plan.md`.

Next research direction:

```text
Freeze a no-wheel learned-history PPO recipe and compare it against the current
M62/M65-style driver under the existing retention and wrong-history gates.
```
