# M91-A Input Observability Probe Smoke

M91-A implements the first version of the input observability audit harness from
`docs/m91-input-observability-audit-protocol.md`.

## Harness

Added:

```text
src/autodrift/input_observability_audit.py
tests/test_input_observability_audit.py
```

The harness:

- samples states from a wheel-profile environment;
- applies standardized short-horizon brake and steering probes from copied
  environment states;
- builds future handling-envelope targets:

```text
future_braking_deceleration
future_yaw_response
future_lateral_accel_response
```

- compares current-code input profiles with ridge regression:

```text
p0_no_wheel_response_context = observation[0:12] + observation[25:85]
p1_wheel_response_context    = observation[0:85]
p0_response_only             = observation[0:12]
p1_response_only             = observation[0:25]
wheel_only                   = observation[12:25]
context_only                 = observation[25:85]
```

This is a smoke approximation over the current 85-value wheel-proxy frame, not
the final clean raw-wheel sensor contract.

## Validation

Focused tests:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src conda run -n autodrift pytest -q tests/test_input_observability_audit.py
```

Result:

```text
4 passed
```

## Smoke Commands

Tiny harness smoke:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src conda run -n autodrift python -m autodrift.input_observability_audit \
  --env-config configs/ppo_m88_wheel_masked_friction_aux_driver.json \
  --episodes 4 \
  --seed 9300 \
  --policy heuristic \
  --horizon-steps 10 \
  --sample-stride 8 \
  --max-samples 80 \
  --run-dir runs/m91a_input_observability_smoke_seed9300
```

Slightly larger smoke:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src conda run -n autodrift python -m autodrift.input_observability_audit \
  --env-config configs/ppo_m88_wheel_masked_friction_aux_driver.json \
  --episodes 16 \
  --seed 9301 \
  --policy heuristic \
  --horizon-steps 15 \
  --sample-stride 4 \
  --max-samples 300 \
  --ridge 0.1 \
  --run-dir runs/m91a_input_observability_smoke_seed9301
```

## Result

The larger smoke produced `219` sampled states.

| target | P0 no-wheel R2 | P1 wheel R2 | P1 - P0 R2 | P1 - P0 MAE improvement |
| --- | ---: | ---: | ---: | ---: |
| future braking decel | -3.853873 | -3.871869 | -0.017996 | -0.002567 |
| future lateral accel response | -0.849670 | -0.849388 | 0.000282 | 0.000120 |
| future yaw response | -1.546608 | -1.548673 | -0.002065 | 0.000001 |

Response-only profile deltas were also near zero:

| target | P1 response - P0 response R2 |
| --- | ---: |
| future braking decel | -0.000300 |
| future lateral accel response | 0.000202 |
| future yaw response | -0.001752 |

## Interpretation

M91-A is an infrastructure pass, not evidence that wheel response helps.

What it proves:

- the future-envelope probe harness runs end to end;
- it writes `samples.csv`, `probe_summary.csv`, `profile_gain_summary.csv`,
  `summary.json`, and `manifest.json`;
- the current 85-value frame can be compared as P0 versus P1 without PPO.

What the smoke suggests:

- the current front/rear wheel proxy channels do not yet add useful predictive
  signal for these future-envelope targets under this small heuristic-rollout
  sample;
- high-dimensional profiles with scene context can overfit badly at low sample
  counts;
- response-only profiles are more stable than response+context for this probe,
  which supports keeping M91-B focused on response/self-ID branch features.

## Decision

Proceed to M91-B:

```text
Run a formal input observability probe with more episodes, response-branch
history windows, stronger train/test splits, and then decide whether to
implement cleaner raw wheel dynamics before RL profile comparison.
```

Do not treat the current wheel-proxy smoke as a final negative result. It is a
warning that the formal audit must separate clean raw sensor channels from
derived wheel/slip proxies.
