# M23 Hard-Corpus Response Training

Last updated: 2026-05-21

## Motivation

M22 produced a small hard response-dependence corpus. It is useful as a gate,
but the current driver was not trained with a mechanism that deliberately
oversamples those hard response-dependent seeds. M23 adds that training path
without changing the actor observation contract.

## Infrastructure

`PPOConfig.training_seed_csv` allows PPO training to reset vector environments
from a fixed seed corpus. The seed is used only by the simulator reset path. It
is not part of actor observation, recurrent state, checkpoint input, or policy
metadata available to `ActorPolicy`.

The vector env cycles the seed list deterministically. This is intentionally a
small and strict mechanism for hard-case oversampling, not an oracle feature.

## Config

```text
configs/ppo_m23_hard_response_corpus_driver.json
```

The first M23 config:

- starts from the M21_503 checkpoint via strict same-architecture init;
- trains with `training_seed_csv` set to
  `runs/m22_hard_response_corpus_m21_503_seed3000/scenario_corpus.csv`;
- alternates hard actuator nominal, hard actuator perturbed, and mixed
  retention stages;
- keeps the 15-value deployable actor frame and
  `actor_encoder="response_critical_online_gru"`.

Queued command:

```bash
conda run -n autodrift python -m autodrift.train_ppo \
  --config configs/ppo_m23_hard_response_corpus_driver.json \
  --seed 1223 \
  --device cuda \
  --init-checkpoint runs/ppo_m21_response_critical_actor_seed1031/checkpoints/checkpoint_step_503808.pt \
  --run-dir runs/ppo_m23_hard_response_corpus_seed1223
```

## Validation

M23 should be evaluated on:

- M22 hard actuator gate for `m21_503`;
- M22 hard friction gate for `m21_503`;
- M21 same-corpus obstacle benchmark;
- M21 actuator-response paired gate;
- M13 friction paired gate.

The desired result is not just higher aggregate success. M23 must preserve the
M21 performance gain while increasing response-mask degradation on the hard
gate.

## Smoke Result

Command:

```bash
conda run -n autodrift python -m autodrift.train_ppo \
  --config configs/ppo_m23_hard_response_corpus_driver.json \
  --total-steps 20480 \
  --seed 1223 \
  --device cuda \
  --init-checkpoint runs/ppo_m21_response_critical_actor_seed1031/checkpoints/checkpoint_step_503808.pt \
  --run-dir runs/ppo_m23_hard_response_corpus_smoke_seed1223
```

Result:

- init checkpoint load mode: `strict`;
- run dir: `runs/ppo_m23_hard_response_corpus_smoke_seed1223`;
- saved checkpoint: `runs/ppo_m23_hard_response_corpus_smoke_seed1223/checkpoint.pt`;
- eval return mean: 64.220;
- eval steps mean: 68.500;
- eval termination rate: 0.100;
- eval lateral RMSE mean: 1.228;
- eval beta absolute error mean: 0.185.

The smoke run proves the hard seed reset schedule and strict same-architecture
initialization work. It is not a driver-quality result.
