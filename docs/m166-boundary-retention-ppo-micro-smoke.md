# M166 Boundary-Retention PPO Micro Smoke

M165 showed that a 2048-step PPO smoke from M163 passed behavior and protected
key checks but failed the fixed M164 boundary replay gate by losing one
wrong-history success-drop row. M166 retries from M163, not from the failed
M165 checkpoint, with a smaller and more tightly anchored PPO micro-smoke.

This is a positive single-seed PPO micro result. It admits repeat/staged PPO
experiments, not large PPO.

## Config

Added:

```text
configs/ppo_m166_boundary_retention_micro.json
```

Differences from M165:

| Parameter | M165 | M166 |
| --- | ---: | ---: |
| total steps | 2048 | 1024 |
| action anchor coef | 20.0 | 50.0 |
| checkpoint interval | 2048 | 1024 |
| init checkpoint | M163 | M163 |

The actor inputs remain unchanged.

## PPO Run

Command:

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.train_ppo \
  --config configs/ppo_m166_boundary_retention_micro.json \
  --init-checkpoint runs/m163_boundary_outcome_actor_coupling_anchor100_s20_seed9832/optimized_checkpoint.pt \
  --run-dir runs/ppo_m166_boundary_retention_micro_seed5166
```

Training result:

```text
loaded_init_checkpoint=.../m163.../optimized_checkpoint.pt load_mode=strict
loaded_baseline_action_anchor=.../m163.../optimized_checkpoint.pt load_mode=strict
training_device=cuda num_envs=8 curriculum_stage=base
step=1024 update=1 stage=base rollout_return_mean=77.20 reward_mean=1.113 episode_count=11
saved=runs/ppo_m166_boundary_retention_micro_seed5166/checkpoint.pt
```

Eval summary:

| Metric | Value |
| --- | ---: |
| return mean | 84.380343 |
| steps mean | 83.8 |
| termination rate | 0.0 |
| lateral RMSE mean | 1.329923 |
| beta abs error mean | 0.158083 |

## Fixed Outcome Objective

Run:

```text
runs/m166_fixed_batch_outcome_eval_seed37
```

| Policy | Loss mean |
| --- | ---: |
| m163_a100_s20 | 0.398315 |
| m166_1024 | 0.398266 |

The fixed M162 objective improves slightly.

## Boundary Replay Gate

Run:

```text
runs/m166_boundary_outcome_replay_gate_seed9510
```

Baseline is M163. Candidate is M166.

| Metric | M163 | M166 | Delta |
| --- | ---: | ---: | ---: |
| normal success rate | 0.681818 | 0.681818 | 0.000000 |
| wrong-history success rate | 0.500000 | 0.500000 | 0.000000 |
| success-drop count | 16 | 16 | 0 |
| normal margin mean | 0.017946 | 0.020594 | +0.002648 |
| margin gap mean | -0.001989 | 0.000870 | +0.002859 |

Gate checks:

| Gate | Pass |
| --- | --- |
| normal success retention | true |
| normal margin retention | true |
| wrong-history gap retention | true |
| success-drop count retention | true |

M166 fixes the exact M165 blocker: the fixed boundary replay success-drop count
does not regress.

## Behavior Retention

Seed `9503`:

| Policy | Success | Collision | Mean margin |
| --- | ---: | ---: | ---: |
| m163_a100_s20 | 0.8625 | 0.1375 | 1.846266 |
| m166_1024 | 0.8625 | 0.1375 | 1.846249 |
| m166_1024_reset | 0.8500 | 0.1250 | 1.842058 |
| m166_1024_zero_current | 0.8000 | 0.1250 | 1.856489 |
| m166_1024_zero_all | 0.8000 | 0.1250 | 1.856489 |
| m166_1024_noact | 0.8625 | 0.1375 | 1.847303 |

Seed `9504`:

| Policy | Success | Collision | Mean margin |
| --- | ---: | ---: | ---: |
| m163_a100_s20 | 0.8625 | 0.1375 | 1.853828 |
| m166_1024 | 0.8625 | 0.1375 | 1.853801 |
| m166_1024_reset | 0.8500 | 0.1250 | 1.850193 |
| m166_1024_zero_current | 0.8000 | 0.1250 | 1.868456 |
| m166_1024_zero_all | 0.8000 | 0.1250 | 1.868456 |
| m166_1024_noact | 0.8625 | 0.1375 | 1.856258 |

Behavior retention passes and response ablation gaps are preserved.

## Protected Critical Key

Run:

```text
runs/m166_critical_key_seed9944
```

| Policy | Accepted cases | Pass |
| --- | ---: | --- |
| m163_a100_s20 | 1 / 1 | true |
| m166_1024 | 1 / 1 | true |

Protected key passes.

## Decision

M166 is positive.

What passed:

- fixed M162 objective improves slightly;
- M164 boundary replay passes with no success-drop count regression;
- normal boundary margin improves versus M163;
- behavior seeds 9503 and 9504 retain success and ablation gaps;
- protected critical key passes.

What remains weak:

- this is one PPO micro seed;
- the PPO update is only 1024 steps;
- no broader repeat or longer staged PPO has passed yet;
- no-action history is still behavior-neutral.

Decision: admit a multi-seed repeat/staged PPO experiment from the M166 recipe.
Do not jump to long PPO until repeats preserve the fixed boundary replay gate.

## Validation

Commands executed:

```text
PYTHONPATH=src python -m autodrift.outcome_intervention_eval ...
PYTHONPATH=src python -m autodrift.boundary_outcome_replay_gate ...
PYTHONPATH=src python -m autodrift.benchmark ... --seed 9503
PYTHONPATH=src python -m autodrift.benchmark ... --seed 9504
PYTHONPATH=src python -m autodrift.critical_key_replay_guard ...
```
