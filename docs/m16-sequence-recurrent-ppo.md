# M16 Sequence Recurrent PPO

Last updated: 2026-05-21

## Motivation

M15 proved that deployable response features matter under the M13 perturbation
gate, but hidden reset still outperformed normal recurrent inference. The next
training blocker is the PPO update itself.

Before M16, online GRU rollouts carried hidden state during data collection, but
the update replayed each stored hidden state as a detached per-step feature.
That lets the policy use a hidden vector, but it does not train the hidden
dynamics with sequence backpropagation.

## Change

`PPOConfig.recurrent_sequence_training=true` enables sequence minibatches for
`actor_encoder="online_gru"`:

- collect the same rollout buffers as before;
- group minibatches by environment sequence instead of random individual steps;
- unroll the online GRU across the rollout;
- zero hidden state after done transitions;
- compute PPO policy/value losses over the full sequence.

The actor observation contract is unchanged.

## Training Config

Config:

```text
configs/ppo_m16_sequence_recurrent_driver.json
```

Queued command:

```bash
conda run -n autodrift python -m autodrift.train_ppo \
  --config configs/ppo_m16_sequence_recurrent_driver.json \
  --seed 733 \
  --device cuda \
  --run-dir runs/ppo_m16_sequence_recurrent_seed733
```

Smoke result:

- run dir: `runs/ppo_m16_sequence_recurrent_smoke`;
- eval return mean: 83.584;
- eval steps mean: 67.500;
- eval termination rate: 0.000;
- eval lateral RMSE mean: 0.213.

## Validation

Use the same M13 paired gate:

```bash
conda run -n autodrift python -m autodrift.paired_perturbation_gate \
  --env-config configs/m11_online_recurrent_history_critical_eval.json \
  --seed-csv runs/m13_near_threshold_corpus_seed3000/scenario_corpus.csv \
  --checkpoint runs/ppo_m16_sequence_recurrent_seed733/checkpoint.pt \
  --checkpoint-policy m16=runs/ppo_m16_sequence_recurrent_seed733/checkpoint.pt \
  --checkpoint-policy m16_reset=runs/ppo_m16_sequence_recurrent_seed733/checkpoint.pt@reset_recurrent_state \
  --checkpoint-policy m16_zero_current=runs/ppo_m16_sequence_recurrent_seed733/checkpoint.pt@zero_current_response \
  --checkpoint-policy m16_zero_all=runs/ppo_m16_sequence_recurrent_seed733/checkpoint.pt@zero_all_response \
  --device cpu \
  --run-dir runs/m16_sequence_recurrent_paired_gate_seed3000
```

Pass direction:

- normal M16 should not be worse than hidden reset;
- normal M16 should improve perturbed success relative to M15;
- response masking should remain worse than normal inference.
