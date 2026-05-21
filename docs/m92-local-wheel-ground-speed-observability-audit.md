# M92 Local Wheel Ground-Speed Observability Audit

M92 implements the latest input-design correction from
`/home/quyaonan/workspace/AutoDrift - 项目评估分析.mhtml` saved on
2026-05-21 23:50 +0800.

The core question is whether a physically cleaner wheel profile can overturn
M91-I's negative decision on the current `front_rear_raw` proxy.

M92 does not test slip ratio as actor input.

## Implemented Profiles

All three profiles preserve the historical 13-slot wheel branch and therefore
the 85-value wheel actor frame:

```text
P1: front_rear_omega
P2: front_rear_omega_ground
P4: front_rear_omega_ground_error
```

`P3 = Romega + v_parallel + v_perp` remains future work because the current
single-track simulator does not expose meaningful per-wheel lateral contact
speed.

The cleanest M92 profile is `P2`. In the current bicycle approximation:

```text
v_parallel_front =
  vx * cos(steer) + (vy + yaw_rate * lf) * sin(steer)
v_parallel_rear = vx
```

`P4` uses fixed-scale speed error:

```text
(Romega_i - v_parallel_i) / 20
```

This is not a slip ratio because the denominator is a fixed normalization
constant, not a state-dependent local speed.

## Commands

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src conda run -n autodrift python -m autodrift.input_observability_audit \
  --env-config configs/m92_front_rear_omega_profile.json \
  --episodes 30 \
  --seed 9390 \
  --policy heuristic \
  --horizon-steps 15 \
  --sample-stride 3 \
  --max-samples 800 \
  --ridge 0.1 \
  --history-windows 1,10,25 \
  --run-dir runs/m92_omega_observability_seed9390

OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src conda run -n autodrift python -m autodrift.input_observability_audit \
  --env-config configs/m92_front_rear_omega_ground_profile.json \
  --episodes 30 \
  --seed 9391 \
  --policy heuristic \
  --horizon-steps 15 \
  --sample-stride 3 \
  --max-samples 800 \
  --ridge 0.1 \
  --history-windows 1,10,25 \
  --run-dir runs/m92_omega_ground_observability_seed9391

OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src conda run -n autodrift python -m autodrift.input_observability_audit \
  --env-config configs/m92_front_rear_omega_ground_error_profile.json \
  --episodes 30 \
  --seed 9392 \
  --policy heuristic \
  --horizon-steps 15 \
  --sample-stride 3 \
  --max-samples 800 \
  --ridge 0.1 \
  --history-windows 1,10,25 \
  --run-dir runs/m92_omega_ground_error_observability_seed9392
```

Artifacts:

```text
runs/m92_omega_observability_seed9390/summary.json
runs/m92_omega_observability_seed9390/profile_gain_summary.csv
runs/m92_omega_ground_observability_seed9391/summary.json
runs/m92_omega_ground_observability_seed9391/profile_gain_summary.csv
runs/m92_omega_ground_error_observability_seed9392/summary.json
runs/m92_omega_ground_error_observability_seed9392/profile_gain_summary.csv
```

Sample counts:

| profile | seed | samples |
| --- | ---: | ---: |
| P1 `front_rear_omega` | 9390 | 537 |
| P2 `front_rear_omega_ground` | 9391 | 538 |
| P4 `front_rear_omega_ground_error` | 9392 | 555 |

## Mean P1-vs-P0 Gain

The table averages over history windows `1`, `10`, and `25`.

| profile | mean R2 lift | mean MAE-improvement lift | response-only R2 lift |
| --- | ---: | ---: | ---: |
| P1 `front_rear_omega` | 0.151403 | 0.016089 | 0.104320 |
| P2 `front_rear_omega_ground` | -0.062184 | -0.008762 | 0.087813 |
| P4 `front_rear_omega_ground_error` | -0.344659 | -0.054854 | -0.108071 |

## Target-Averaged Detail

| profile | target | R2 lift | MAE-improvement lift | response-only R2 lift |
| --- | --- | ---: | ---: | ---: |
| P1 `front_rear_omega` | braking | 0.320345 | 0.045805 | 0.223247 |
| P1 `front_rear_omega` | lateral accel | 0.014914 | 0.001179 | 0.034072 |
| P1 `front_rear_omega` | yaw | 0.118950 | 0.001283 | 0.055642 |
| P2 `front_rear_omega_ground` | braking | -0.006085 | 0.012025 | 0.195266 |
| P2 `front_rear_omega_ground` | lateral accel | -0.019363 | -0.007470 | 0.111739 |
| P2 `front_rear_omega_ground` | yaw | -0.161104 | -0.030840 | -0.043565 |
| P4 `front_rear_omega_ground_error` | braking | -0.433297 | -0.070348 | -0.320268 |
| P4 `front_rear_omega_ground_error` | lateral accel | -0.380179 | -0.049698 | -0.109563 |
| P4 `front_rear_omega_ground_error` | yaw | -0.220501 | -0.044516 | 0.105618 |

## Interpretation

M92 is a negative admission result for the single-track local-ground-speed
profiles.

Key points:

- `front_rear_omega` shows a weak positive mean gain, mostly from braking, but
  absolute held-out R2 is still poor and the profile omits the local ground
  reference that motivated the M92 correction.
- `front_rear_omega_ground`, the physically cleaner M92 profile, does not
  improve the full P1-vs-P0 probe on average.
- `front_rear_omega_ground_error` is clearly harmful in this setup, so the
  fixed-scale error should not enter the primary actor profile.
- The response-only lift for `front_rear_omega_ground` suggests that wheel
  channels can contain some local response signal, but it is not stable once
  full context is included.

## Decision

Do not admit the M92 single-track wheel/local-ground-speed branch into the
primary PPO driver input.

The primary driver should remain the clean no-wheel human-view response stream
until a stronger four-wheel profile or a matched corpus proves stable benefit:

```text
body response + previous commands + actuator states + road/obstacle geometry
```

M92 does preserve useful infrastructure:

```text
front_rear_omega
front_rear_omega_ground
front_rear_omega_ground_error
```

These modes are valid experimental profiles for future four-wheel work, but
they are not promoted driver inputs.
