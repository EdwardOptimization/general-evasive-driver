# M36 Response-Change Corpus Training

Last updated: 2026-05-21

## Hypothesis

M34 learned a weak current-response sensitivity signal but did not make the
recurrent hidden state behavior-critical. M36 fine-tunes from M34_151 on the
larger M35 response-change corpus, with ordinary randomized resets still mixed
in, to see whether the weak response sensitivity can be turned into a stronger
closed-loop recurrent policy.

## Config

```text
configs/ppo_m36_response_change_corpus_driver.json
```

Key choices:

- init checkpoint: `runs/ppo_m34_response_aux_mixed_seed1434/checkpoints/checkpoint_step_151552.pt`;
- response-change corpus:
  `runs/m35_m34_151_matched_response_corpus_seed4300/scenario_corpus.csv`;
- `training_seed_mix_probability = 0.75`;
- `response_prediction_aux_coef = 0.05`;
- `response_prediction_dim = 12`;
- `total_steps = 200000`;
- checkpoint interval: 25k steps;
- `vector_env_mode = parallel`.

## Command

```bash
conda run -n autodrift python -m autodrift.train_ppo \
  --config configs/ppo_m36_response_change_corpus_driver.json \
  --seed 1536 \
  --device cuda \
  --init-checkpoint runs/ppo_m34_response_aux_mixed_seed1434/checkpoints/checkpoint_step_151552.pt \
  --run-dir runs/ppo_m36_response_change_corpus_seed1536
```

## Validation

After training:

- sweep M36 checkpoints on the M35 response-change corpus;
- repeat the M29 selected-corpus sweep;
- repeat the broad 40-seed same-seed sweep;
- run hidden-swap gates on the best M36 checkpoint;
- compare against envelope AES, M26_602, M30_053, and M34_151.

M36 only counts as real progress if it improves response-critical ablation
behavior without losing the M30/M34 aggregate success level.

## Result

Command:

```bash
conda run -n autodrift python -m autodrift.train_ppo \
  --config configs/ppo_m36_response_change_corpus_driver.json \
  --seed 1536 \
  --device cuda \
  --init-checkpoint runs/ppo_m34_response_aux_mixed_seed1434/checkpoints/checkpoint_step_151552.pt \
  --run-dir runs/ppo_m36_response_change_corpus_seed1536
```

Run artifacts:

- final checkpoint: `runs/ppo_m36_response_change_corpus_seed1536/checkpoint.pt`;
- periodic checkpoints: 28672, 53248, 77824, 102400, 126976, 151552,
  176128, and 200000;
- command log: `runs/research/m36-response-change-corpus-training_20260521T041525Z/command.log`.

Final eval:

- return mean: 65.342;
- steps mean: 65.300;
- termination rate: 0.200;
- lateral RMSE mean: 0.707;
- beta absolute error mean: 0.133.

M35 response-change corpus sweep:

| Policy | Success | Return mean | Collision rate |
| --- | ---: | ---: | ---: |
| envelope AES | 0.4625 | 40.454 | 0.5375 |
| M26_602 | 0.5875 | 48.295 | 0.4125 |
| M30_053 | 0.6125 | 49.446 | 0.3875 |
| M34_151 | 0.6125 | 48.768 | 0.3875 |
| M36_028 | 0.6125 | 48.934 | 0.3875 |
| M36_053 | 0.6000 | 48.284 | 0.4000 |
| M36_077 | 0.5875 | 47.529 | 0.4125 |
| M36_102 | 0.6000 | 47.929 | 0.4000 |
| M36_126 | 0.6125 | 48.458 | 0.3875 |
| M36_151 | 0.6000 | 47.762 | 0.4000 |
| M36_176 | 0.6000 | 47.653 | 0.4000 |
| M36_final | 0.6000 | 47.717 | 0.4000 |

M29 selected-corpus sweep:

| Policy | Success | Return mean | Collision rate |
| --- | ---: | ---: | ---: |
| envelope AES | 0.725 | 61.882 | 0.275 |
| M30_053 | 0.875 | 70.795 | 0.125 |
| M34_151 | 0.875 | 69.411 | 0.125 |
| M36_028 | 0.875 | 69.500 | 0.125 |
| M36_126 | 0.850 | 67.616 | 0.150 |
| M36_final | 0.850 | 67.590 | 0.150 |

Broad 40-seed sweep:

| Policy | Success | Return mean | Collision rate |
| --- | ---: | ---: | ---: |
| envelope AES | 0.675 | 56.594 | 0.300 |
| M30_053 | 0.825 | 67.732 | 0.175 |
| M34_151 | 0.825 | 65.783 | 0.175 |
| M36_028 | 0.825 | 65.934 | 0.175 |
| M36_126 | 0.800 | 63.391 | 0.200 |
| M36_final | 0.800 | 63.245 | 0.200 |

M36_028 hidden-swap gate:

- accepted visible matches: 73 / 80;
- accepted nominal normal/reset/zero-response/hidden-swap success:
  0.973 / 0.973 / 0.973 / 0.973;
- accepted perturbed normal/reset/zero-response/hidden-swap success:
  0.644 / 0.658 / 0.658 / 0.644;
- perturbed reset outcome changes: 3, with 1 unfavorable and 2 favorable;
- perturbed zero-response outcome changes: 3, with 1 unfavorable and 2
  favorable;
- hidden-swap outcome changes: 0.

## Conclusion

M36 is a negative result. The best early checkpoint, M36_028, preserves
M34_151-level aggregate success on M35, M29, and broad sweeps, but it does not
improve any gate. Later checkpoints regress. Hidden-swap remains
outcome-neutral.

The likely failure mode is that one-step response prediction plus hard corpus
oversampling creates small current-response sensitivity but does not force the
GRU hidden state to carry an action-relevant dynamics belief. The next
architecture should use a multi-step future-response auxiliary target so the
latent must predict how the vehicle will keep reacting over several closed-loop
steps, not just the immediate next frame.
