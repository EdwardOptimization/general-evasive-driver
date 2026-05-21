# M93 M62 Hidden-Envelope Probe

M93 checks whether the current best no-wheel recurrent driver already encodes a
useful handling-envelope belief in its online GRU hidden state.

This is not a PPO run and not a promoted driver. It is a checkpoint diagnostic
that follows the M91/M92 input decision: keep the no-wheel human-view stream as
primary, then test whether the existing recurrent hidden state actually adds
future-envelope information beyond a per-step reset hidden state.

## Question

For the M62 current-best margin-retention candidate:

```text
runs/m62_m37_m61_032_interpolated_checkpoints/checkpoints/alpha_0_25.pt
```

does the normal recurrent hidden state predict future handling envelope targets
better than the hidden state produced by the current frame alone?

Targets:

```text
future_braking_deceleration
future_yaw_response
future_lateral_accel_response
```

Feature sets:

```text
full_observation
current_response
policy_features
response_hidden
reset_policy_features
reset_response_hidden
```

`response_hidden` is the normal GRU hidden after the current observation.
`reset_response_hidden` is produced from the same current observation but with
the recurrent state reset to zero. Their difference is the direct test for
whether M62's carried history improves future-envelope observability.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src conda run -n autodrift python -m autodrift.hidden_envelope_probe \
  --checkpoint runs/m62_m37_m61_032_interpolated_checkpoints/checkpoints/alpha_0_25.pt \
  --env-config configs/ppo_m24_human_view_gru_driver.json \
  --episodes 30 \
  --seed 9410 \
  --horizon-steps 15 \
  --sample-stride 3 \
  --max-samples 800 \
  --ridge 0.1 \
  --device cpu \
  --run-dir runs/m93_m62_hidden_envelope_probe_seed9410
```

Artifacts:

```text
runs/m93_m62_hidden_envelope_probe_seed9410/samples.csv
runs/m93_m62_hidden_envelope_probe_seed9410/probe_summary.csv
runs/m93_m62_hidden_envelope_probe_seed9410/hidden_gain_summary.csv
runs/m93_m62_hidden_envelope_probe_seed9410/summary.json
runs/m93_m62_hidden_envelope_probe_seed9410/manifest.json
```

The run collected `704` sampled states across `30` episodes.

## Results

| target | response hidden R2 | reset hidden R2 | normal - reset R2 | normal - reset MAE improvement |
| --- | ---: | ---: | ---: | ---: |
| braking | 0.483314 | 0.585666 | -0.102351 | -0.040365 |
| lateral accel | 0.571544 | 0.515213 | 0.056331 | 0.006155 |
| yaw | 0.077073 | 0.349812 | -0.272739 | -0.023984 |

Policy fused features are also worse than reset fused features on all three
targets:

| target | policy feature R2 | reset policy feature R2 | normal - reset R2 |
| --- | ---: | ---: | ---: |
| braking | 0.232840 | 0.441181 | -0.208341 |
| lateral accel | 0.147087 | 0.370026 | -0.222939 |
| yaw | -0.461107 | 0.163148 | -0.624256 |

## Interpretation

M93 is negative for the claim that M62 already carries a stable
future-envelope belief in its recurrent hidden state.

Key observations:

- Normal `response_hidden` is better than reset hidden only on lateral
  acceleration, and only weakly.
- Reset hidden is better on braking and yaw, which are the key emergency
  maneuver authority targets.
- The fused policy feature is worse than its reset-hidden counterpart on every
  target, suggesting that the policy feature space is not organized around
  future handling-envelope prediction.
- This explains why earlier reset/wrong-history gates often failed to show a
  strong behavioral dependence on recurrent history: the carried hidden state
  is not yet a reliable envelope belief.

## Decision

Do not treat M62 as a self-identifying driver just because it has good aggregate
margin retention.

The next research direction should be a no-wheel envelope-belief objective or
pretraining path that explicitly makes the response hidden predict future
braking/yaw/lateral authority before or during PPO continuation.

The objective should be tested outside PPO first, following the M80/M89 pattern:

```text
fixed rollout/snippet batch
frozen or anchored actor behavior
optimize response encoder + GRU + envelope head
verify response_hidden beats reset_response_hidden on held-out envelope targets
only then reintroduce PPO
```
