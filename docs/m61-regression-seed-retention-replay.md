# M61 Regression-Seed Retention Replay

Last updated: 2026-05-21

## Motivation

M60 proved that baseline-action anchoring can produce non-negative mean-margin
deltas, but strict promotion still failed because a small set of near-boundary
seeds became worse. M61 focuses directly on those regressions instead of
another broad reward-scale change.

M60 primary blockers:

- M38 seed `4413`;
- M38 seed `4378`;
- M38 seed `4457`;
- broad seed `3019`.

## Replay Corpus

M61 creates `runs/m61_regression_seed_replay/seed_sequence.csv` from the M53
deduplicated margin seed corpus plus 12 repeats of each M60 regression seed.

Artifacts:

- `runs/m61_regression_seed_replay/manifest.json`;
- `runs/m61_regression_seed_replay/seed_sequence.csv`;
- `runs/m61_regression_seed_replay/regression_seed_summary.csv`.

Corpus summary:

| Item | Value |
| --- | ---: |
| Base rows | 41 |
| Base unique seeds | 41 |
| Regression seeds | 4 |
| Repeats per regression seed | 12 |
| Total rows | 89 |

Each regression seed appears 13 times total: once from the M53 base corpus plus
12 replay rows.

## Config

M61 config:

- `configs/ppo_m61_regression_seed_retention_driver.json`;
- init checkpoint: `m37_102`;
- anchor checkpoint: `m37_102`;
- `baseline_action_anchor_coef`: `1.0`;
- `baseline_action_anchor_negative_advantage_only`: `true`;
- `training_seed_csv`: `runs/m61_regression_seed_replay/seed_sequence.csv`;
- `training_seed_mix_probability`: `0.30`;
- learning rate: `3e-6`.

Full run command:

```bash
conda run -n autodrift python -m autodrift.train_ppo \
  --config configs/ppo_m61_regression_seed_retention_driver.json \
  --seed 2861 \
  --device cuda \
  --init-checkpoint runs/ppo_m37_multistep_response_aux_seed1637/checkpoints/checkpoint_step_102400.pt \
  --run-dir runs/ppo_m61_regression_seed_retention_seed2861
```

## Smoke

Command:

```bash
conda run -n autodrift python -m autodrift.train_ppo \
  --config configs/ppo_m61_regression_seed_retention_driver.json \
  --total-steps 4096 \
  --rollout-steps 64 \
  --num-envs 4 \
  --vector-env-mode sync \
  --seed 2861 \
  --device cuda \
  --init-checkpoint runs/ppo_m37_multistep_response_aux_seed1637/checkpoints/checkpoint_step_102400.pt \
  --run-dir runs/ppo_m61_regression_seed_retention_smoke_seed2861
```

Result:

- smoke completed successfully;
- run dir: `runs/ppo_m61_regression_seed_retention_smoke_seed2861`;
- eval return mean: `74.0360`;
- eval termination rate: `0.100`;
- metrics include `response_prediction_loss_mean`;
- metrics include `baseline_action_anchor_loss_mean`.

## Next Step

Run the full M61 continuation and evaluate it through the unchanged
M38/broad/fresh margin-retention gate. Promotion still requires:

- zero binary regressions;
- zero near-margin regressions;
- non-negative mean margin delta;
- broader driver gates before replacing M37_102 as current best.
