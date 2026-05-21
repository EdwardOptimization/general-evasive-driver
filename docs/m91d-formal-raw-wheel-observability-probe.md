# M91-D Formal Raw Wheel Observability Probe

M91-D reruns the M91 input-observability probe at formal scale using the clean
M91-C raw wheel profile.

This remains a supervised input audit. It does not train PPO and does not
promote a driver.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src conda run -n autodrift python -m autodrift.input_observability_audit \
  --env-config configs/m91c_raw_wheel_minimum_profile.json \
  --episodes 60 \
  --seed 9330 \
  --policy heuristic \
  --horizon-steps 15 \
  --sample-stride 3 \
  --max-samples 1200 \
  --ridge 0.1 \
  --run-dir runs/m91d_raw_wheel_observability_formal_seed9330
```

Artifacts:

```text
runs/m91d_raw_wheel_observability_formal_seed9330/samples.csv
runs/m91d_raw_wheel_observability_formal_seed9330/probe_summary.csv
runs/m91d_raw_wheel_observability_formal_seed9330/profile_gain_summary.csv
runs/m91d_raw_wheel_observability_formal_seed9330/summary.json
runs/m91d_raw_wheel_observability_formal_seed9330/manifest.json
```

The run collected `1143` sampled states, with an episode-disjoint train/test
split of `823` train samples and `320` test samples.

## Result

| target | P0 no-wheel R2 | P1 raw-wheel R2 | P1 - P0 R2 | P1 - P0 MAE improvement |
| --- | ---: | ---: | ---: | ---: |
| future braking decel | 0.225791 | 0.248165 | 0.022374 | 0.000588 |
| future lateral accel response | 0.442423 | 0.440049 | -0.002374 | -0.000442 |
| future yaw response | 0.155758 | 0.162888 | 0.007130 | -0.001689 |

Response-only comparison:

| target | P0 response-only R2 | P1 response-only R2 | P1 - P0 R2 |
| --- | ---: | ---: | ---: |
| future braking decel | 0.139569 | 0.183731 | 0.044162 |
| future lateral accel response | 0.498222 | 0.494154 | -0.004068 |
| future yaw response | 0.268839 | 0.269112 | 0.000273 |

## Interpretation

M91-D is a mixed weak result.

Positive:

- Clean raw wheel P1 improves held-out R2 on braking deceleration.
- Clean raw wheel P1 improves held-out R2 slightly on yaw response.
- The response-only braking lift is larger than the full-profile braking lift,
  which suggests the wheel branch contains some braking-relevant information.

Negative:

- The MAE lift is tiny.
- Lateral acceleration response gets slightly worse with raw wheel features.
- Yaw response improvement is too small to justify a PPO continuation.
- The current probe still uses only a single current frame, while the research
  claim is about online self-identification from history.

## Decision

M91-D does not unblock M90 PPO continuation.

The next step is not to tune PPO. The next step is to make the observability
probe match the research claim by adding explicit history windows:

```text
M91-E: history-window input observability probe.
```

M91-E should compare current-frame probes against short histories such as
`0.2 s`, `0.5 s`, `1.0 s`, and `2.0 s` before any minimum-set sensor ablation or
RL profile comparison.
