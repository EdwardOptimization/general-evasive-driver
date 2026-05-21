# M91-C Clean Raw Wheel Minimum Profile

M91-C implements a cleaner wheel-response input profile before any further PPO
continuation. The goal is infrastructure: separate raw wheel-speed-like
measurements from the older derived slip/ABS/TCS proxy branch, then confirm the
input observability harness can run on the new profile.

## Implementation

New config-gated mode:

```text
wheel_observation_mode = "front_rear_raw"
```

The default 72-value actor frame is unchanged. The raw wheel profile keeps the
same 85-value wheel actor frame used by the wheel GRU:

```text
0-11   body response + previous commands
12-24  raw front/rear wheel response slots
25-84  road and obstacle context
```

The 13 wheel slots preserve compatibility with the wheel-response actor shape,
but the derived slip and ABS/TCS slots are zeroed:

```text
front_wheel_speed
rear_wheel_speed
front_wheel_accel
rear_wheel_accel
0.0
0.0
0.0
brake_pressure_front
brake_pressure_rear
drive_torque_rear
0.0
0.0
0.0
```

This is still a compact simulator approximation, not a high-fidelity wheel
dynamics model. It is cleaner than the legacy `front_rear` branch because the
actor no longer receives explicit slip proxies or ABS/TCS proxy flags.

## Smoke Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src conda run -n autodrift python -m autodrift.input_observability_audit \
  --env-config configs/m91c_raw_wheel_minimum_profile.json \
  --episodes 20 \
  --seed 9320 \
  --policy heuristic \
  --horizon-steps 15 \
  --sample-stride 4 \
  --max-samples 400 \
  --ridge 0.1 \
  --run-dir runs/m91c_raw_wheel_minimum_profile_smoke_seed9320
```

Artifacts:

```text
runs/m91c_raw_wheel_minimum_profile_smoke_seed9320/samples.csv
runs/m91c_raw_wheel_minimum_profile_smoke_seed9320/probe_summary.csv
runs/m91c_raw_wheel_minimum_profile_smoke_seed9320/profile_gain_summary.csv
runs/m91c_raw_wheel_minimum_profile_smoke_seed9320/summary.json
runs/m91c_raw_wheel_minimum_profile_smoke_seed9320/manifest.json
```

The smoke collected `291` sampled states with an episode-disjoint split of
`203` train samples and `88` test samples.

## Smoke Result

| target | P0 no-wheel R2 | P1 raw-wheel R2 | P1 - P0 R2 | P1 - P0 MAE improvement |
| --- | ---: | ---: | ---: | ---: |
| future braking decel | -1.761059 | -1.512847 | 0.248212 | 0.041535 |
| future lateral accel response | 0.416590 | 0.445004 | 0.028414 | 0.023157 |
| future yaw response | -0.806228 | -0.936767 | -0.130540 | -0.025938 |

Response-only comparison:

| target | P0 response-only R2 | P1 response-only R2 | P1 - P0 R2 |
| --- | ---: | ---: | ---: |
| future braking decel | -0.184633 | -0.082047 | 0.102586 |
| future lateral accel response | 0.445475 | 0.470619 | 0.025144 |
| future yaw response | 0.392659 | 0.386010 | -0.006649 |

## Interpretation

M91-C is an infrastructure pass and a mixed signal.

Positive:

- The clean raw wheel profile is config-gated and preserves the canonical
  85-value wheel actor shape.
- Slip and ABS/TCS proxy slots are not part of the clean profile.
- The observability harness runs and writes the required artifacts.
- Raw wheel response improves the smoke probe on braking and lateral response.

Negative:

- The run is intentionally small, so it is not a scientific promotion.
- Full-profile yaw prediction gets worse with raw wheel slots.
- Braking full-profile R2 remains negative despite the P1-P0 lift.

## Decision

M91-C passes as infrastructure only. It does not promote a driver and does not
unblock M90 PPO continuation by itself.

Next step:

```text
M91-D: run a formal raw-wheel input observability probe using the M91-C profile.
```
