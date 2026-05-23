# M334 Short Source-Diverse PPO Escalation Design

M334 designs the next escalation after M333 promotion. It does not run PPO,
repair, replay, or behavior gates.

## Rationale

M328 and M333 now provide two accepted source-diverse PPO proposal directions:

```text
M325 -> M327 repaired -> M328 promotion
M328 -> M330 repaired -> M332 alpha 0.45 -> M333 promotion
```

Both accepted paths required:

```text
raw PPO proposal
exact M297/M270 repair or bounded interpolation
source-diverse protected gates
old 9944 gap-floor audit
first replay gates
separate full public promotion gate
```

The next controlled step is a short PPO escalation, not medium or long PPO.
M334 therefore registers a 4096-step PPO recipe from the M333 base while
keeping the same human-view actor contract and proof-first acceptance stack.

## Base

Current public-gate base:

```text
runs/m332_m328_to_m330_gap_bounded_interpolation/checkpoints/alpha_0_45.pt
```

## Registered Config

Config:

```text
configs/ppo_m335_short_source_diverse_escalation.json
```

Key PPO settings:

| Field | Value |
| --- | ---: |
| total_steps | 4096 |
| rollout_steps | 128 |
| num_envs | 8 |
| minibatch_size | 512 |
| learning_rate | 5e-7 |
| seed | 5238 |
| checkpoint_interval_steps | 1024 |

The config keeps the same auxiliary guard structure as M327/M330:

```text
response_prediction_aux_coef = 0.06
outcome_intervention_aux_coef = 0.06
rejected_history_preference_aux_coef = 0.03
baseline_action_anchor_coef = 100.0
snippet_action_anchor_coef = 100.0
trajectory_action_anchor_coef = 100.0
```

The baseline and snippet action anchors are updated to the M333 public base.

## Planned M335 Commands

Raw PPO proposal:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.train_ppo \
  --config configs/ppo_m335_short_source_diverse_escalation.json \
  --init-checkpoint runs/m332_m328_to_m330_gap_bounded_interpolation/checkpoints/alpha_0_45.pt \
  --run-dir runs/ppo_m335_short_source_diverse_escalation_seed5238
```

Exact post-PPO repair:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.exact_post_ppo_repair \
  --base-checkpoint runs/m332_m328_to_m330_gap_bounded_interpolation/checkpoints/alpha_0_45.pt \
  --raw-checkpoint runs/ppo_m335_short_source_diverse_escalation_seed5238/checkpoint.pt \
  --preference-npz runs/m297_current_family_rejected_preference_objective/rejected_history_preference_corpus.npz \
  --outcome-npz runs/m270_source_balanced_multi_surface_anchor/outcome_intervention_snippets.npz \
  --device cpu \
  --start-mode repair_from_raw \
  --steps 40 \
  --seed 10099 \
  --run-dir runs/m335_exact_repair_from_raw_s40_seed10099
```

If the repaired endpoint passes exact objectives but violates the old-key gap
floor, M335 should run a base-to-repaired interpolation sweep before first
replay. The registered floor remains:

```text
old 9944 margin_gap >= 0.09
```

## Gate Order

M335 must use this order:

1. Run raw PPO as proposal only.
2. Run exact M297/M270 repair from raw.
3. Reject immediately if exact M297 or M270 regress versus M333.
4. Run source-diverse protected gate.
5. Run old `9944` gap-floor diagnostic.
6. If needed, run bounded interpolation from M333 to repaired candidate.
7. Run M183/M170 and M267/M264 first replay gates.
8. Admit a separate full public gate only if all proof gates pass.

M335 must not promote directly. A passing M335 should admit M336 full public
gate.

## Decision

Admit:

```text
m335-short-source-diverse-ppo-escalation-run
```

Decision:

```text
admit_m335_short_source_diverse_ppo_escalation_run
```
