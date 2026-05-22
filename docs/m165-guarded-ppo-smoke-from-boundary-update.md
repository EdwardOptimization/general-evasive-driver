# M165 Guarded PPO Smoke From Boundary Update

M164 admitted only a guarded PPO smoke from M163. M165 tests the smallest
existing PPO-smoke pattern: 2048 PPO steps, very low learning rate, M163 action
anchor, and the M162 boundary-outcome corpus as an auxiliary objective.

This milestone is a PPO-smoke rejection. It does not admit longer PPO.

## Config

Added:

```text
configs/ppo_m165_guarded_boundary_smoke.json
```

Key constraints:

```text
init checkpoint: runs/m163_boundary_outcome_actor_coupling_anchor100_s20_seed9832/optimized_checkpoint.pt
total_steps: 2048
learning_rate: 1e-6
baseline_action_anchor_checkpoint: M163
baseline_action_anchor_coef: 20.0
outcome_intervention_snapshot_npz: runs/m162_m156_boundary_outcome_corpus_dedup_seed9510/boundary_outcome_corpus.npz
outcome_intervention_aux_coef: 0.03
actor inputs: unchanged human-view online GRU
```

Run:

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.train_ppo \
  --config configs/ppo_m165_guarded_boundary_smoke.json \
  --init-checkpoint runs/m163_boundary_outcome_actor_coupling_anchor100_s20_seed9832/optimized_checkpoint.pt \
  --run-dir runs/ppo_m165_guarded_boundary_smoke_seed5165
```

Training result:

```text
loaded_init_checkpoint=.../m163.../optimized_checkpoint.pt load_mode=strict
loaded_baseline_action_anchor=.../m163.../optimized_checkpoint.pt load_mode=strict
training_device=cuda num_envs=8 curriculum_stage=base
step=2048 update=2 stage=base rollout_return_mean=70.70 reward_mean=1.043 episode_count=16
saved=runs/ppo_m165_guarded_boundary_smoke_seed5165/checkpoint.pt
```

Eval summary:

| Metric | Value |
| --- | ---: |
| return mean | 86.800152 |
| steps mean | 88.6 |
| termination rate | 0.0 |
| lateral RMSE mean | 1.460800 |
| beta abs error mean | 0.175865 |

## Fixed Outcome Objective

Run:

```text
runs/m165_fixed_batch_outcome_eval_seed37
```

| Policy | Loss mean |
| --- | ---: |
| m163_a100_s20 | 0.398315 |
| m165_2048 | 0.398201 |

The fixed M162 loss improves slightly.

## Behavior Retention

Seed `9503`:

| Policy | Success | Collision | Mean margin |
| --- | ---: | ---: | ---: |
| m156_s20 | 0.8625 | 0.1375 | 1.845927 |
| m163_a100_s20 | 0.8625 | 0.1375 | 1.846266 |
| m165_2048 | 0.8625 | 0.1375 | 1.846492 |
| m165_2048_reset | 0.8500 | 0.1250 | 1.842085 |
| m165_2048_zero_current | 0.8000 | 0.1250 | 1.856503 |
| m165_2048_zero_all | 0.8000 | 0.1250 | 1.856503 |
| m165_2048_noact | 0.8625 | 0.1375 | 1.847635 |

Seed `9504`:

| Policy | Success | Collision | Mean margin |
| --- | ---: | ---: | ---: |
| m156_s20 | 0.8625 | 0.1375 | 1.853662 |
| m163_a100_s20 | 0.8625 | 0.1375 | 1.853828 |
| m165_2048 | 0.8625 | 0.1375 | 1.854054 |
| m165_2048_reset | 0.8500 | 0.1250 | 1.850224 |
| m165_2048_zero_current | 0.8000 | 0.1250 | 1.868473 |
| m165_2048_zero_all | 0.8000 | 0.1250 | 1.868473 |
| m165_2048_noact | 0.8625 | 0.1375 | 1.856576 |

Behavior retention passes on the two cheap zero-relvel seeds.

## Protected Critical Key

Run:

```text
runs/m165_critical_key_seed9944
```

| Policy | Accepted cases | Pass |
| --- | ---: | --- |
| m156_s20 | 1 / 1 | true |
| m163_a100_s20 | 1 / 1 | true |
| m165_2048 | 1 / 1 | true |

Protected key passes.

## Boundary Replay Gate

Run:

```text
runs/m165_boundary_outcome_replay_gate_seed9510
```

Baseline is M163. Candidate is M165.

| Metric | M163 | M165 | Delta |
| --- | ---: | ---: | ---: |
| normal success rate | 0.681818 | 0.681818 | 0.000000 |
| wrong-history success rate | 0.500000 | 0.511364 | +0.011364 |
| success-drop count | 16 | 15 | -1 |
| normal margin mean | 0.017946 | 0.018536 | +0.000591 |
| margin gap mean | -0.001989 | -0.001766 | +0.000223 |

Gate checks:

| Gate | Pass |
| --- | --- |
| normal success retention | true |
| normal margin retention | true |
| wrong-history gap retention | true |
| success-drop count retention | false |

The M165 checkpoint preserves normal behavior and even slightly improves the
mean margin gap, but it loses one wrong-history-induced success drop on the
fixed M162 boundary rows. The M165 manifest required zero regression on this
count, so the boundary replay gate fails.

## Decision

M165 is rejected for longer PPO admission.

What passed:

- short PPO training ran from M163 with strict checkpoint loading;
- fixed M162 objective improves slightly;
- behavior seeds 9503 and 9504 retain success and response-ablation gaps;
- protected critical key passes.

What failed:

- M164 boundary replay retention fails by one success-drop count.

Decision: do not run longer PPO from M165. The next attempt should either use a
shorter PPO continuation or introduce an explicit boundary-replay retention
guard before PPO can advance.

## Validation

Commands executed:

```text
PYTHONPATH=src python -m autodrift.outcome_intervention_eval ...
PYTHONPATH=src python -m autodrift.benchmark ... --seed 9503
PYTHONPATH=src python -m autodrift.benchmark ... --seed 9504
PYTHONPATH=src python -m autodrift.critical_key_replay_guard ...
PYTHONPATH=src python -m autodrift.boundary_outcome_replay_gate ...
```
