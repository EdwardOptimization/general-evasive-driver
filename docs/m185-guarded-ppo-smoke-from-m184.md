# M185 Guarded PPO Smoke From M184

M184 admitted only a tiny guarded PPO smoke. M185 tests whether one 1024-step
PPO update from the M184 actor-update candidate can preserve the M183
boundary-replay proof surface.

This is a positive single-seed PPO smoke. It admits repeat experiments, not long
PPO.

## Config

Added:

```text
configs/ppo_m185_guarded_from_m184_smoke.json
```

Key constraints:

```text
init checkpoint: runs/m184_m168_actor_coupling_anchor100_s20_seed9840/optimized_checkpoint.pt
total_steps: 1024
learning_rate: 1e-6
baseline_action_anchor_checkpoint: M184
baseline_action_anchor_coef: 100.0
outcome_intervention_snapshot_npz: runs/m183_m168_boundary_outcome_corpus_dedup_seed9510/boundary_outcome_corpus.npz
outcome_intervention_aux_coef: 0.03
actor inputs: unchanged human-view online GRU with zero obstacle relative velocity
```

The actor does not receive M183 labels, hidden dynamics, or oracle feasibility.

## PPO Run

Command:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.train_ppo \
  --config configs/ppo_m185_guarded_from_m184_smoke.json \
  --init-checkpoint runs/m184_m168_actor_coupling_anchor100_s20_seed9840/optimized_checkpoint.pt \
  --run-dir runs/ppo_m185_guarded_from_m184_seed5185
```

Training result:

```text
loaded_init_checkpoint=.../m184.../optimized_checkpoint.pt load_mode=strict
loaded_baseline_action_anchor=.../m184.../optimized_checkpoint.pt load_mode=strict
training_device=cuda num_envs=8 curriculum_stage=base
step=1024 update=1 stage=base rollout_return_mean=82.41 reward_mean=1.136 episode_count=11
saved=runs/ppo_m185_guarded_from_m184_seed5185/checkpoint.pt
```

Training metrics:

| Metric | Value |
| --- | ---: |
| response prediction loss | 0.054329 |
| outcome intervention loss | 0.173028 |
| baseline action-anchor loss | 0.000003576 |

Eval summary:

| Metric | Value |
| --- | ---: |
| return mean | 78.626983 |
| steps mean | 69.8 |
| termination rate | 0.0 |
| lateral RMSE mean | 1.051279 |
| beta abs error mean | 0.106848 |

Candidate:

```text
runs/ppo_m185_guarded_from_m184_seed5185/checkpoint.pt
```

## Fixed M183 Objective

Command:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.outcome_intervention_eval \
  --snippet-npz runs/m183_m168_boundary_outcome_corpus_dedup_seed9510/boundary_outcome_corpus.npz \
  --checkpoint-policy m184_s20=runs/m184_m168_actor_coupling_anchor100_s20_seed9840/optimized_checkpoint.pt \
  --checkpoint-policy m185_1024=runs/ppo_m185_guarded_from_m184_seed5185/checkpoint.pt \
  --device cpu \
  --batch-size 64 \
  --batches 50 \
  --seed 37 \
  --logprob-margin 0.05 \
  --run-dir runs/m185_fixed_batch_outcome_eval_seed37
```

| Policy | Loss mean |
| --- | ---: |
| m184_s20 | 0.171518 |
| m185_1024 | 0.171432 |

Independent fixed-objective improvement:

```text
0.000086
```

The improvement is small, but it is in the right direction and does not justify
promotion by itself.

## Boundary Replay

M185 must retain both M183 boundary replay surfaces.

M168 corpus:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.boundary_outcome_replay_gate \
  --checkpoint-policy m184_s20=runs/m184_m168_actor_coupling_anchor100_s20_seed9840/optimized_checkpoint.pt \
  --checkpoint-policy m185_1024=runs/ppo_m185_guarded_from_m184_seed5185/checkpoint.pt \
  --corpus-csv runs/m183_m168_boundary_outcome_corpus_dedup_seed9510/boundary_outcome_corpus.csv \
  --env-config configs/m121_human_view_zero_obstacle_relvel.json \
  --max-continuation-steps 60 \
  --baseline-policy m184_s20 \
  --candidate-policy m185_1024 \
  --max-normal-success-drop 0.0 \
  --max-normal-margin-regression 0.005 \
  --max-margin-gap-regression 0.001 \
  --max-success-drop-count-regression 0 \
  --device cpu \
  --run-dir runs/m185_m168_boundary_replay_gate_seed9510
```

M170 corpus:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.boundary_outcome_replay_gate \
  --checkpoint-policy m170_split=runs/ppo_m170_row67_guarded_stage2_seed7170/checkpoint.pt \
  --checkpoint-policy m185_1024=runs/ppo_m185_guarded_from_m184_seed5185/checkpoint.pt \
  --corpus-csv runs/m183_m170_boundary_outcome_corpus_dedup_seed9510/boundary_outcome_corpus.csv \
  --env-config configs/m121_human_view_zero_obstacle_relvel.json \
  --max-continuation-steps 60 \
  --baseline-policy m170_split \
  --candidate-policy m185_1024 \
  --max-normal-success-drop 0.0 \
  --max-normal-margin-regression 0.005 \
  --max-margin-gap-regression 0.001 \
  --max-success-drop-count-regression 0 \
  --device cpu \
  --run-dir runs/m185_m170_boundary_replay_gate_seed9510
```

| Corpus | Rows | Baseline drops | M185 drops | Normal margin delta | Margin gap delta | Gate pass |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| M168 strict | 16 | 16 | 16 | +0.000108 | +0.000119 | true |
| M170 split | 17 | 17 | 17 | -0.001250 | -0.000055 | true |

Both replay surfaces retain every success-drop row.

## Behavior Retention

Commands use `configs/m121_human_view_zero_obstacle_relvel.json`, 80 episodes,
and compare M184, M185, and M185 response-history ablations.

Seed `9503`:

| Policy | Success | Collision | Mean margin |
| --- | ---: | ---: | ---: |
| m184_s20 | 0.8625 | 0.1375 | 1.846415 |
| m185_1024 | 0.8625 | 0.1375 | 1.846491 |
| m185_1024_reset | 0.8500 | 0.1250 | 1.842214 |
| m185_1024_zero_all | 0.8000 | 0.1250 | 1.856606 |
| m185_1024_noact | 0.8625 | 0.1375 | 1.847665 |

Seed `9504`:

| Policy | Success | Collision | Mean margin |
| --- | ---: | ---: | ---: |
| m184_s20 | 0.8625 | 0.1375 | 1.853940 |
| m185_1024 | 0.8625 | 0.1375 | 1.854015 |
| m185_1024_reset | 0.8500 | 0.1250 | 1.850368 |
| m185_1024_zero_all | 0.8000 | 0.1250 | 1.868597 |
| m185_1024_noact | 0.8625 | 0.1375 | 1.856546 |

Behavior retention passes and the reset/zero-all degradation pattern is
preserved. No-action history remains behavior-neutral.

## Protected Key

Command:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.critical_key_replay_guard \
  --reference-manifest runs/m133_zero_relvel_s60_strict_60ep_seed9900/manifest.json \
  --reference-cases-csv runs/m133_zero_relvel_s60_strict_60ep_seed9900/outcome_sensitive_snippets.csv \
  --reference-cases-csv runs/m133_zero_relvel_s60_strict_60ep_seed9920/outcome_sensitive_snippets.csv \
  --case-key '9944|perturbed|28|28' \
  --checkpoint-policy m184_s20=runs/m184_m168_actor_coupling_anchor100_s20_seed9840/optimized_checkpoint.pt \
  --checkpoint-policy m185_1024=runs/ppo_m185_guarded_from_m184_seed5185/checkpoint.pt \
  --reference-policy m184_s20 \
  --device cpu \
  --run-dir runs/m185_critical_key_seed9944
```

| Policy | Accepted cases | Pass |
| --- | ---: | --- |
| m184_s20 | 1 / 1 | true |
| m185_1024 | 1 / 1 | true |

`guard_validated=false` only means no non-reference policy failed in this run.
The relevant evidence is `m185_1024 policy_pass=true`.

## Decision

M185 is positive as a single-seed PPO smoke.

What passed:

- one 1024-step PPO update from M184 runs with strict checkpoint loading;
- fixed M183 objective improves slightly;
- M168 and M170 boundary replay gates keep all success-drop rows;
- behavior seeds `9503` and `9504` match M184 normal success;
- reset and zero-all ablations still degrade success;
- protected key `9944|perturbed|28|28` passes.

What remains weak:

- this is one PPO seed;
- fixed objective improvement is very small;
- no-action history remains behavior-neutral;
- no longer PPO stage has passed the M183 replay gates.

Decision:

```text
admit_multiseed_guarded_ppo_repeat
```

Next step: repeat the same M185 recipe across additional seeds before any
longer PPO continuation.
