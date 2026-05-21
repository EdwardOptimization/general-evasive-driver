# M30 Mixed Hard-Corpus Training

Last updated: 2026-05-21

## Motivation

M23 showed that hard-only seed replay can overfit and damage broad obstacle
performance. M29 produced a useful matched hard corpus, but it should not be
used as the only reset distribution. M30 adds mixed hard-seed sampling so hard
matched cases can be oversampled while ordinary randomized resets remain active.

## Infrastructure Change

`PPOConfig` now supports:

```text
training_seed_mix_probability
```

When `training_seed_csv` is set:

- `1.0` keeps the old hard-only behavior;
- `0.0` disables the seed corpus and uses ordinary deterministic vector-env
  seeds;
- values between 0 and 1 sample hard corpus seeds with that probability and
  default randomized seeds otherwise.

This keeps the actor input clean. The seed corpus only controls simulator reset
selection during training; it is not an actor observation.

## Config

```text
configs/ppo_m30_mixed_matched_response_driver.json
```

Key choices:

- init from `m26_602`;
- train with `human_view_online_gru`;
- use `runs/m29_matched_response_corpus_seed4200/scenario_corpus.csv`;
- `training_seed_mix_probability = 0.65`;
- checkpoint every 50k steps;
- low learning rate `6e-5`;
- 300k total steps.

## Smoke

Command:

```bash
conda run -n autodrift python -m autodrift.train_ppo \
  --config configs/ppo_m30_mixed_matched_response_driver.json \
  --total-steps 20480 \
  --seed 1330 \
  --device cuda \
  --init-checkpoint runs/ppo_m26_human_view_gru_seed2024/checkpoints/checkpoint_step_602112.pt \
  --run-dir runs/ppo_m30_mixed_matched_response_smoke_seed1330
```

Result:

- strict init checkpoint load succeeded;
- training device: `cuda`;
- final smoke step: 20480;
- rollout return mean: 59.95;
- eval return mean: 69.080;
- eval steps mean: 61.900;
- eval termination rate: 0.100;
- checkpoint: `runs/ppo_m30_mixed_matched_response_smoke_seed1330/checkpoint.pt`.

Smoke conclusion: the mixed seed sampler and M30 config train end to end.

## Full Run Plan

```bash
conda run -n autodrift python -m autodrift.train_ppo \
  --config configs/ppo_m30_mixed_matched_response_driver.json \
  --seed 1330 \
  --device cuda \
  --init-checkpoint runs/ppo_m26_human_view_gru_seed2024/checkpoints/checkpoint_step_602112.pt \
  --run-dir runs/ppo_m30_mixed_matched_response_seed1330
```

After full training, evaluate:

- M29 selected corpus success;
- M28 hidden-swap gate;
- broad same-seed human-view obstacle benchmark;
- reset, zero-response, and hidden-swap ablations.

## Full Run Result

Command:

```bash
conda run -n autodrift python -m autodrift.train_ppo \
  --config configs/ppo_m30_mixed_matched_response_driver.json \
  --seed 1330 \
  --device cuda \
  --init-checkpoint runs/ppo_m26_human_view_gru_seed2024/checkpoints/checkpoint_step_602112.pt \
  --run-dir runs/ppo_m30_mixed_matched_response_seed1330
```

Run artifacts:

- final checkpoint: `runs/ppo_m30_mixed_matched_response_seed1330/checkpoint.pt`;
- periodic checkpoints: steps 53248, 102400, 151552, 200704, 253952, and
  300000;
- train metrics: `runs/ppo_m30_mixed_matched_response_seed1330/train_metrics.csv`;
- eval summary: `runs/ppo_m30_mixed_matched_response_seed1330/eval_summary.json`;
- command log: `runs/research/m30-mixed-hard-corpus-training_20260521T031733Z/command.log`.

Final eval:

- return mean: 63.764;
- steps mean: 60.400;
- termination rate: 0.200;
- lateral RMSE mean: 0.926;
- beta absolute error mean: 0.137.

M29 selected-corpus checkpoint sweep:

| Policy | Success | Return mean | Collision rate |
| --- | ---: | ---: | ---: |
| envelope AES | 0.725 | 61.882 | 0.275 |
| M26_602 | 0.775 | 66.875 | 0.225 |
| M30_053 | 0.875 | 70.795 | 0.125 |
| M30_102 | 0.875 | 69.786 | 0.125 |
| M30_151 | 0.875 | 69.559 | 0.125 |
| M30_200 | 0.875 | 69.954 | 0.125 |
| M30_253 | 0.850 | 68.954 | 0.150 |
| M30_final | 0.800 | 67.304 | 0.200 |

Broad 40-seed checkpoint sweep:

| Policy | Success | Return mean | Collision rate |
| --- | ---: | ---: | ---: |
| envelope AES | 0.675 | 56.594 | 0.300 |
| M26_602 | 0.800 | 67.765 | 0.200 |
| M30_053 | 0.825 | 67.732 | 0.175 |
| M30_102 | 0.825 | 66.411 | 0.175 |
| M30_200 | 0.825 | 66.546 | 0.175 |
| M30_final | 0.750 | 64.167 | 0.250 |

M28-style hidden-swap gate for M30_053:

- accepted visible matches: 73 / 80;
- accepted mean hidden-state distance: 1.339;
- accepted nominal normal/reset/zero-response/hidden-swap success:
  0.973 / 0.973 / 0.973 / 0.973;
- accepted perturbed normal/reset/zero-response/hidden-swap success:
  0.644 / 0.658 / 0.658 / 0.644;
- hidden-swap changed zero accepted success outcomes;
- reset and zero-response each changed one perturbed success outcome, but in
  the favorable direction.

Conclusion: M30 is a partial positive result. Mixed hard-corpus training
improves both the M29 selected corpus and the broad same-seed benchmark at early
checkpoints, especially `checkpoint_step_53248.pt`. It still does not pass
recurrent self-identification. Hidden-swap remains outcome-neutral, and
reset/zero-response are not harmful. The current best aggregate checkpoint is
`m30_053`, but the next blocker is still proof of feedback-critical behavior,
not aggregate success.
