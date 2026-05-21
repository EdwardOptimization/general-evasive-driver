# M86 Wheel Response Relevance Audit

M84 and M85 showed that the wheel-response branch can retain M62-class
aggregate behavior, but `zero_wheel_response` does not hurt. M86 asks a more
basic question before adding more training pressure:

```text
Do the current front/rear wheel features contain predictive information beyond
the 12-value body response stream?
```

## Harness

Added:

```text
src/autodrift/wheel_response_relevance_audit.py
```

The harness collects rollout samples from a wheel-profile checkpoint and trains
episode-disjoint linear probes over four feature sets:

```text
body_response      observation[0:12]
wheel_response     observation[12:25]
body_plus_wheel    observation[0:25]
full_observation   observation[:]
```

It writes:

- `samples.csv`;
- `probe_summary.csv`;
- `wheel_gain_summary.csv`;
- `summary.json`;
- `manifest.json`.

The key metric is:

```text
body_plus_wheel_gain =
  test_accuracy(body_plus_wheel) - test_accuracy(body_response)
```

This is not a self-identification pass/fail gate. It is an information audit:
if wheel response adds no predictive information even offline, then stronger
policy training is unlikely to make it causally useful.

## Tests

Added:

```text
tests/test_wheel_response_relevance_audit.py
```

Focused tests verify:

- body and wheel slices use the intended 0:12 and 12:25 ranges;
- non-wheel observations are rejected;
- gain summaries compare `body_plus_wheel` against `body_response`.

Focused validation:

```text
3 passed
```

## Audit Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 conda run -n autodrift python -m autodrift.wheel_response_relevance_audit \
  --checkpoint runs/ppo_m85_wheel_response_aux_smoke_seed3985/checkpoint.pt \
  --env-config configs/ppo_m85_wheel_response_aux_driver.json \
  --episodes 30 \
  --seed 9100 \
  --device cpu \
  --max-samples 1500 \
  --epochs 120 \
  --run-dir runs/m86_wheel_response_relevance_audit_seed9100
```

## Result

The audit collected `1500` samples.

| target | body | wheel | body+wheel | full obs | body+wheel gain |
| --- | ---: | ---: | ---: | ---: | ---: |
| brake_bucket | 0.742972 | 0.610442 | 0.734940 | 0.506024 | -0.008032 |
| cg_bucket | 0.329317 | 0.351406 | 0.341365 | 0.238956 | 0.012048 |
| mass_bucket | 0.728916 | 0.624498 | 0.720884 | 0.656627 | -0.008032 |
| mu_bucket | 0.706827 | 0.445783 | 0.809237 | 0.504016 | 0.102410 |
| steering_tau_bucket | 0.417671 | 0.439759 | 0.383534 | 0.439759 | -0.034137 |
| tire_bucket | 0.399598 | 0.369478 | 0.391566 | 0.283133 | -0.008032 |

Aggregate:

```text
mean body+wheel gain = 0.009371
max body+wheel gain  = 0.102410
positive > 0.02      = mu_bucket only
```

## Interpretation

M86 is a mixed but mostly negative wheel-relevance result.

Useful signal:

- `body_plus_wheel` improves `mu_bucket` prediction by about `+0.102` test
  accuracy over body response alone.

Limits:

- wheel response alone is worse than body response for `mu_bucket`;
- no other hidden-dynamics bucket gets a meaningful gain;
- mean gain across hidden targets is only about `+0.009`;
- this is consistent with M85, where the trained policy's wheel columns remain
  small and `zero_wheel_response` does not change behavior.

The current front/rear wheel features are not useless, but their incremental
information is narrow. They mostly add friction-bucket evidence and do not
explain brake scale, tire stiffness, mass, CG, or steering delay well enough in
this audit.

## Decision

Do not keep increasing generic wheel-response auxiliary loss. M85 already shows
that full-response prediction does not make wheel inputs behavior-critical.

The next step should be targeted:

```text
M87: wheel-informed friction/envelope objective or corpus

use the M86 result to target friction / available-authority estimation;
avoid claiming broad vehicle self-ID from front/rear wheel features;
mine matched cases where body response is ambiguous but wheel response changes
mu/envelope prediction;
then gate whether zero-wheel or wrong-wheel history hurts those cases.
```

This keeps the research claim honest: the current wheel branch may help with
online friction/envelope estimation, but it is not yet evidence of general
professional-driver self-identification.
