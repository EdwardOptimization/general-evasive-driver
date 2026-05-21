# M39 M37 Response-Corpus Training

Last updated: 2026-05-21

## Hypothesis

M37 multi-step response prediction created the first clean unfavorable
reset/zero-response outcome changes, but hidden-swap remains outcome-neutral.
M39 continues from M37_102 on the sharper M38 response-critical corpus with a
lower learning rate. This tests whether the response-critical behavior can be
reinforced without erasing broad success.

## Config

```text
configs/ppo_m39_m37_response_corpus_driver.json
```

Key choices:

- init checkpoint: `M37_102`;
- response corpus:
  `runs/m38_m37_102_matched_response_corpus_seed4300/scenario_corpus.csv`;
- `response_prediction_horizon = 4`;
- `response_prediction_aux_coef = 0.03`;
- `training_seed_mix_probability = 0.70`;
- `learning_rate = 3e-5`;
- `total_steps = 200000`;
- checkpoint interval: 25k steps.

## Command

```bash
conda run -n autodrift python -m autodrift.train_ppo \
  --config configs/ppo_m39_m37_response_corpus_driver.json \
  --seed 1739 \
  --device cuda \
  --init-checkpoint runs/ppo_m37_multistep_response_aux_seed1637/checkpoints/checkpoint_step_102400.pt \
  --run-dir runs/ppo_m39_m37_response_corpus_seed1739
```

## Validation

After training:

- sweep M39 checkpoints on M38 and M35 response-change corpora;
- repeat M29 and broad sweeps;
- run hidden-swap gate on the best checkpoint;
- compare reset/zero-response unfavorable outcome-change counts against
  M37_102.

M39 only counts as progress if it keeps or improves M37_102 aggregate success
and increases unfavorable reset/zero-response or hidden-swap sensitivity.
