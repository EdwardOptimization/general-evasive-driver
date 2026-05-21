# M91-G Learned History Encoder Observability Probe

M91-G tests whether a small supervised learned history encoder can extract
self-identification information that linear raw-history and hand-summary probes
missed.

This is still not PPO and not a promoted driver.

## Implementation

New module:

```text
src/autodrift/learned_history_observability_probe.py
```

It collects the same M91-C raw-wheel observations and future envelope targets,
then compares:

```text
p0_current_ridge      current-frame body/command ridge baseline
p1_current_ridge      current-frame body/command/wheel ridge baseline
p0_response_history   GRU over body/command history
p1_response_history   GRU over body/command/wheel history
```

The train/test split is episode-disjoint. The GRU predicts all three future
envelope targets jointly:

```text
future_braking_deceleration
future_yaw_response
future_lateral_accel_response
```

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src conda run -n autodrift python -m autodrift.learned_history_observability_probe \
  --env-config configs/m91c_raw_wheel_minimum_profile.json \
  --episodes 40 \
  --seed 9360 \
  --policy heuristic \
  --horizon-steps 15 \
  --sample-stride 3 \
  --max-samples 1000 \
  --history-window 50 \
  --device cpu \
  --epochs 80 \
  --run-dir runs/m91g_learned_history_encoder_seed9360
```

Artifacts:

```text
runs/m91g_learned_history_encoder_seed9360/samples.csv
runs/m91g_learned_history_encoder_seed9360/probe_summary.csv
runs/m91g_learned_history_encoder_seed9360/summary.json
runs/m91g_learned_history_encoder_seed9360/manifest.json
```

The run collected `763` sampled states, with an episode-disjoint split of `522`
train samples and `241` test samples.

## Result

Held-out R2:

| profile | braking | yaw | lateral accel |
| --- | ---: | ---: | ---: |
| p0 current ridge | -0.046662 | 0.355068 | 0.258924 |
| p1 current ridge | 0.003104 | 0.357193 | 0.263521 |
| p0 response-history GRU | -0.236183 | 0.175098 | 0.519855 |
| p1 response-history GRU | -0.533310 | -0.000144 | 0.450859 |

Held-out MAE improvement over train-mean baseline:

| profile | braking | yaw | lateral accel |
| --- | ---: | ---: | ---: |
| p0 current ridge | -0.029606 | 0.132380 | 0.239231 |
| p1 current ridge | -0.012980 | 0.141035 | 0.239353 |
| p0 response-history GRU | -0.058303 | 0.104323 | 0.402276 |
| p1 response-history GRU | -0.112122 | 0.040816 | 0.359253 |

## Interpretation

M91-G is a mixed result.

Positive:

- A learned history encoder can extract useful history information for lateral
  response: P0 GRU improves lateral R2 from `0.258924` to `0.519855`.
- This supports the general belief-learning direction more than M91-E/F did.

Negative:

- The GRU overfits: train R2 is around `0.90`, but braking test R2 is negative.
- P1 wheel history is worse than P0 history on all three targets in this run.
- Current-frame ridge remains stronger for yaw.
- This still does not prove deployable self-identification or justify PPO.

## Decision

M91-G does not unblock M90 PPO continuation.

It does show that learned history can matter, but the next step should be a
regularized repeat rather than sensor ablation:

```text
M91-H: regularized learned-history probe with smaller model and repeated seeds.
```

Pass criteria for M91-H should require:

```text
lower train/test overfit gap
stable improvement over current-frame ridge on at least one target
no P1 wheel degradation relative to P0 on the same target
```
