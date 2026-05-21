# M91-B Formal Input Observability Probe

M91-B runs the first formal-sized version of the M91-A probe. It still uses the
current 85-value wheel-proxy frame; it does not yet implement clean raw wheel
dynamics.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src conda run -n autodrift python -m autodrift.input_observability_audit \
  --env-config configs/ppo_m88_wheel_masked_friction_aux_driver.json \
  --episodes 60 \
  --seed 9310 \
  --policy heuristic \
  --horizon-steps 15 \
  --sample-stride 3 \
  --max-samples 1200 \
  --ridge 0.1 \
  --run-dir runs/m91b_input_observability_formal_seed9310
```

Artifacts:

```text
runs/m91b_input_observability_formal_seed9310/samples.csv
runs/m91b_input_observability_formal_seed9310/probe_summary.csv
runs/m91b_input_observability_formal_seed9310/profile_gain_summary.csv
runs/m91b_input_observability_formal_seed9310/summary.json
runs/m91b_input_observability_formal_seed9310/manifest.json
```

The run collected `1198` sampled states, with an episode-disjoint train/test
split of `902` train samples and `296` test samples.

## Result

| target | P0 no-wheel R2 | P1 wheel R2 | P1 - P0 R2 | P1 - P0 MAE improvement |
| --- | ---: | ---: | ---: | ---: |
| future braking decel | -0.054117 | -0.052369 | 0.001748 | 0.001270 |
| future lateral accel response | 0.366895 | 0.380958 | 0.014062 | 0.008844 |
| future yaw response | 0.278130 | 0.276685 | -0.001445 | 0.000030 |

Response-only comparison:

| target | P0 response-only R2 | P1 response-only R2 | P1 - P0 R2 |
| --- | ---: | ---: | ---: |
| future braking decel | -0.034141 | -0.034191 | -0.000049 |
| future lateral accel response | 0.422835 | 0.432782 | 0.009946 |
| future yaw response | 0.309219 | 0.309380 | 0.000161 |

## Interpretation

M91-B is a mixed negative result for the current wheel-proxy profile.

Positive:

- P1 gives a small held-out lift on future lateral acceleration response.
- Response-only P1 is slightly better than response-only P0 on lateral
  acceleration and yaw response.
- The harness now has enough samples to be more informative than M91-A smoke.

Negative:

- The P1-P0 gains are tiny.
- Braking deceleration remains poorly predicted by both P0 and P1.
- Future yaw response does not improve in the full response+context profile.
- `context_only` is surprisingly competitive on some targets, which means the
  current probe still risks scene/context correlation rather than pure
  response-branch self-ID evidence.

The current 13 wheel channels are not raw wheel dynamics. They include proxy
features derived from current body state, drive force, and tire-force residuals.
M91-B therefore should not be read as "wheel speed is useless"; it says the
current proxy wheel branch is not strong enough to justify another PPO
continuation.

## Decision

Do not proceed directly to M90 PPO continuation.

Next step:

```text
M91-C: implement a cleaner raw wheel-state minimum profile.
```

M91-C should separate:

```text
raw wheel state / speed channels
low-level actuator measurements
derived slip or ABS/TCS proxy channels
```

Then rerun the formal observability probe before sensor ablations or RL profile
comparison.
