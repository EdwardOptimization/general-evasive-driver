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

## Full Training Result

Command:

```bash
conda run -n autodrift python -m autodrift.train_ppo \
  --config configs/ppo_m23_hard_response_corpus_driver.json \
  --seed 1223 \
  --device cuda \
  --init-checkpoint runs/ppo_m21_response_critical_actor_seed1031/checkpoints/checkpoint_step_503808.pt \
  --run-dir runs/ppo_m23_hard_response_corpus_seed1223
```

Result:

- run dir: `runs/ppo_m23_hard_response_corpus_seed1223`;
- saved checkpoint: `runs/ppo_m23_hard_response_corpus_seed1223/checkpoint.pt`;
- eval return mean: 43.382;
- eval steps mean: 60.300;
- eval termination rate: 0.200;
- eval lateral RMSE mean: 0.595;
- eval beta absolute error mean: 0.209;
- periodic checkpoints: steps 102400, 200704, 303104, 401408, and 500000.

## Gate Results

Hard actuator gate:

| Policy | Nominal success | Perturbed success |
| --- | ---: | ---: |
| M21_503 | 1.000 | 0.714 |
| M23_102 | 0.714 | 0.571 |
| M23_200 | 0.429 | 0.571 |
| M23_303 | 0.000 | 0.286 |
| M23_401 | 0.143 | 0.286 |
| M23_500 | 0.286 | 0.429 |

Hard friction gate:

| Policy | Nominal success | Perturbed success |
| --- | ---: | ---: |
| M21_503 | 1.000 | 0.714 |
| M23_102 | 1.000 | 0.714 |
| M23_200 | 0.857 | 0.429 |
| M23_303 | 0.857 | 0.143 |
| M23_401 | 0.857 | 0.143 |
| M23_500 | 0.857 | 0.143 |

Same-contract obstacle benchmark:

| Policy | Success | Termination rate |
| --- | ---: | ---: |
| `envelope_aes` | 0.250 | 0.750 |
| M21_503 | 0.500 | 0.500 |
| M23_102 | 0.500 | 0.500 |
| M23_500 | 0.300 | 0.700 |

## Conclusion

M23 is a negative result. The hard seed reset infrastructure is valid, but
hard-only replay is too narrow: it overfits a seven-seed corpus and damages the
general obstacle policy. The earliest M23 checkpoint preserves the same-corpus
benchmark but already loses the hard actuator gate, while the final checkpoint
regresses both hard-gate behavior and same-corpus success.

The next training path should mix the hard response corpus with ordinary
randomized resets, or add a separate KL-constrained fine-tune. The actor
contract should stay strict and deployable: no hidden parameter inputs, no target
labels, no abstract slip fields, and no backward-compatible checkpoint adapter.
