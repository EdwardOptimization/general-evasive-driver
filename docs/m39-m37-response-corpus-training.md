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

## Result

Command:

```bash
conda run -n autodrift python -m autodrift.train_ppo \
  --config configs/ppo_m39_m37_response_corpus_driver.json \
  --seed 1739 \
  --device cuda \
  --init-checkpoint runs/ppo_m37_multistep_response_aux_seed1637/checkpoints/checkpoint_step_102400.pt \
  --run-dir runs/ppo_m39_m37_response_corpus_seed1739
```

Final eval:

- return mean: 69.884;
- steps mean: 68.900;
- termination rate: 0.100;
- lateral RMSE mean: 0.942;
- beta absolute error mean: 0.162.

M38 response-critical corpus sweep:

| Policy | Success | Return mean | Collision rate |
| --- | ---: | ---: | ---: |
| envelope AES | 0.4250 | 37.376 | 0.5750 |
| M30_053 | 0.5875 | 46.990 | 0.4125 |
| M37_102 | 0.6250 | 48.034 | 0.3750 |
| M39_028 | 0.6375 | 48.799 | 0.3625 |
| M39_053 | 0.6375 | 48.934 | 0.3625 |
| M39_077 | 0.6250 | 48.080 | 0.3750 |
| M39_102 | 0.6000 | 46.657 | 0.4000 |
| M39_126 | 0.5875 | 45.865 | 0.4125 |
| M39_final | 0.5875 | 45.752 | 0.4125 |

M35 response-change corpus sweep:

| Policy | Success | Return mean | Collision rate |
| --- | ---: | ---: | ---: |
| envelope AES | 0.4625 | 40.454 | 0.5375 |
| M37_102 | 0.6500 | 50.262 | 0.3500 |
| M39_028 | 0.6500 | 50.321 | 0.3500 |
| M39_053 | 0.6500 | 50.442 | 0.3500 |
| M39_final | 0.6125 | 48.043 | 0.3875 |

M29 and broad sweeps:

- M37_102 / M39_028 / M39_053 / M39_final M29 success:
  0.875 / 0.875 / 0.875 / 0.850;
- M37_102 / M39_028 / M39_053 / M39_final broad success:
  0.825 / 0.825 / 0.825 / 0.800.

Hidden-swap gates:

- M39_028 and M39_053 each accepted 73 / 80 matched cases;
- hidden-swap outcome changes: 0 for both;
- perturbed reset outcome changes: 1 each, all unfavorable;
- perturbed zero-response outcome changes: 1 each, all unfavorable.

## Conclusion

M39 is a negative result despite a small M38 corpus success gain. It preserves
aggregate success at early checkpoints, but it weakens the M37_102
response-critical ablation signal: reset and zero-response outcome changes fall
from 2 / 80 to 1 / 80 on the 4200 hidden-swap gate, and hidden-swap remains
outcome-neutral.

The next step should be diagnostics, not another corpus fine-tune. M40 should
log and evaluate multi-step response auxiliary loss so checkpoint selection can
test whether the recurrent state is actually learning a predictive dynamics
belief.
