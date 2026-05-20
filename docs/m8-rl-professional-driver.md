# M8 RL Professional Driver

Last updated: 2026-05-21

## Purpose

M8 is the first implementation step toward the project goal of a true
driver-like RL operator. It keeps the M7 contract but replaces pure
history-stacked MLP inference with an explicit temporal actor baseline.

The target behavior is:

```text
deployable observation history + previous actions
  -> recurrent/latent RL actor
  -> steering and throttle/brake
  -> vehicle response
  -> updated history
```

The actor is still direct low-level control. It does not receive rule labels,
controller modes, true friction, mass, CG, tire stiffness, brake scale, or
actuator parameters.

## M8 Baseline

Tracked config:

- `configs/ppo_m8_temporal_gru_driver.json`

Actor and observation interface:

- `actor_encoder="temporal_gru"`;
- `actor_history_length=4`;
- `history_length=4`;
- `action_history_mode="full"`;
- base frame dimension is 19 for the obstacle task;
- total actor observation dimension is 76.

The temporal actor encodes each history frame, reverses the current-first
history into chronological order, and feeds the encoded sequence through a GRU.
The final GRU hidden state is the actor/critic latent used for action, value,
sequence prediction, and latent probes.

## Stable AES Reward Shaping

M8 adds optional `ObstacleTaskConfig` fields:

- `stable_aes_beta_limit`;
- `stable_aes_sideslip_penalty`;
- `stable_aes_drift_bonus_scale`.

These fields only affect `aes_feasible` scenarios. They reduce drift reward and
penalize excessive sideslip when stable steering should be enough. Defaults
preserve the older M7 behavior, so M7 checkpoints and configs do not silently
change.

The M8 config enables this shaping because the M7 gate rejected both M7-A and
M7-B for using too much high sideslip on `aes_feasible` cases.

## Smoke Command

Short infrastructure check:

```bash
conda run -n autodrift python -m autodrift.train_ppo \
  --config configs/ppo_m8_temporal_gru_driver.json \
  --init-checkpoint runs/ppo_m7a_history_seed127/checkpoint.pt \
  --total-steps 512 \
  --rollout-steps 64 \
  --eval-episodes 2 \
  --device cpu \
  --run-dir runs/ppo_m8_temporal_gru_smoke
```

Result:

| item | value |
| --- | --- |
| run dir | `runs/ppo_m8_temporal_gru_smoke` |
| init mode | `new_temporal_encoder` |
| curriculum stage | `stable_aes_only` |
| reward mean | 1.132 |
| eval return mean | 2.529 |
| eval steps mean | 29.000 |
| eval termination rate | 1.000 |
| eval lateral RMSE mean | 0.367 |
| eval beta abs error mean | 0.086 |

Interpretation: this is an infrastructure pass only. It proves that the
temporal-GRU actor can be configured, initialized from an MLP checkpoint,
trained, saved, loaded, and evaluated. It does not prove the policy is useful;
the smoke checkpoint terminates quickly and must not be used as a performance
claim.

## Full Training Command

Planned full run:

```bash
conda run -n autodrift python -m autodrift.train_ppo \
  --config configs/ppo_m8_temporal_gru_driver.json \
  --init-checkpoint runs/ppo_m7a_history_seed127/checkpoint.pt \
  --run-name ppo_m8_temporal_gru_driver
```

The resulting checkpoint must go through the driver gate before it can be called
an RL professional driver.

## Next Work

- Add the M8 checkpoint to the gate comparison after full training.
- Compare AEB, heuristic AES, envelope AES, M5, M7-A, M7-B, and M8 on the same
  label-balanced held-out corpus.
- Run no-action-history, single-frame, and shuffled-history ablations for M8.
- Run latent probes on the M8 GRU state and require temporal lift over shuffled
  history.
- Keep negative results if M8 fails, then iterate reward/curriculum or actor
  design instead of claiming success.
