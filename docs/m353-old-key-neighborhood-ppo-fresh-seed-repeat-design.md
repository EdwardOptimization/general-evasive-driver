# M353 Old-Key Neighborhood PPO Fresh-Seed Repeat Design

M353 designs a fresh-seed repeat after M352 promotion. It does not run PPO,
repair, replay, behavior gates, or promotion.

## Rationale

M351/M352 produced a second accepted short-PPO step under the old-key
neighborhood policy, but it was still one PPO seed. The repaired endpoint was
not acceptable and required bounded interpolation. Before any longer PPO
escalation, the correct next step is a fresh-seed repeat from the new public
base.

## Base

Current public-gate base:

```text
runs/m351_m349_to_repaired_old_key_neighborhood_interpolation/checkpoints/alpha_0_0075.pt
```

## Registered Config

Config:

```text
configs/ppo_m354_old_key_neighborhood_repeat.json
```

Key PPO settings:

| Field | Value |
| --- | ---: |
| total_steps | 4096 |
| rollout_steps | 128 |
| num_envs | 8 |
| minibatch_size | 512 |
| learning_rate | 5e-7 |
| seed | 5240 |
| checkpoint_interval_steps | 1024 |

This keeps the same PPO length and guard coefficients as M351. Only the PPO
seed and base/anchor checkpoint change.

## Planned M354 Commands

Raw PPO proposal:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.train_ppo \
  --config configs/ppo_m354_old_key_neighborhood_repeat.json \
  --init-checkpoint runs/m351_m349_to_repaired_old_key_neighborhood_interpolation/checkpoints/alpha_0_0075.pt \
  --run-dir runs/ppo_m354_old_key_neighborhood_repeat_seed5240
```

Exact post-PPO repair:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.exact_post_ppo_repair \
  --base-checkpoint runs/m351_m349_to_repaired_old_key_neighborhood_interpolation/checkpoints/alpha_0_0075.pt \
  --raw-checkpoint runs/ppo_m354_old_key_neighborhood_repeat_seed5240/checkpoint.pt \
  --preference-npz runs/m297_current_family_rejected_preference_objective/rejected_history_preference_corpus.npz \
  --outcome-npz runs/m270_source_balanced_multi_surface_anchor/outcome_intervention_snippets.npz \
  --device cpu \
  --start-mode repair_from_raw \
  --steps 40 \
  --seed 10103 \
  --run-dir runs/m354_exact_repair_from_raw_s40_seed10103
```

If the repaired endpoint fails source-diverse or old-key neighborhood gates,
run interpolation from the M352 base to the repaired endpoint before first
replay:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.checkpoint_interpolation \
  --base-checkpoint runs/m351_m349_to_repaired_old_key_neighborhood_interpolation/checkpoints/alpha_0_0075.pt \
  --target-checkpoint runs/m354_exact_repair_from_raw_s40_seed10103/candidate_checkpoint.pt \
  --alphas 0 0.0025 0.005 0.0075 0.01 0.02 0.05 0.1 0.2 0.4 0.6 0.8 1.0 \
  --label-prefix m354_a \
  --run-dir runs/m354_m352_to_repaired_old_key_neighborhood_interpolation
```

## Gate Order

M354 must use this order:

1. Run raw PPO as proposal only.
2. Run exact M297/M270 repair from raw.
3. Reject immediately if exact M297 or M270 regress versus M352.
4. Run source-diverse protected gates.
5. Run old-key neighborhood targeted replay and replay-gate adapter.
6. If needed, run bounded interpolation from M352 to repaired candidate and
   re-evaluate exact/source-diverse/old-key neighborhood gates on selected
   alphas.
7. Run M183/M170 and M267/M264 first replay gates.
8. Admit a separate full public gate only if all proof gates pass.

M354 must not promote directly. A passing M354 should admit M355 full public
gate. If M354 requires another micro-alpha, treat that as fresh-seed evidence
that endpoint proof washout remains the main limiter before longer PPO.

## Decision

Admit:

```text
m354-old-key-neighborhood-ppo-fresh-seed-repeat
```

Decision:

```text
admit_m354_old_key_neighborhood_ppo_fresh_seed_repeat
```
