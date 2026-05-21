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
