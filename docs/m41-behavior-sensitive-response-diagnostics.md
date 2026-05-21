# M41 Behavior-Sensitive Response Diagnostics

Last updated: 2026-05-21

## Motivation

M40 showed that M39_053 has lower response-prediction MSE than M37_102 while
having a weaker reset/zero-response ablation signal. M41 adds per-seed
diagnostics to test whether prediction error correlates with behavior-critical
seeds.

## Implementation

`autodrift.response_prediction_eval` now writes:

- `prediction_summary.csv`: aggregate response prediction metrics;
- `prediction_episodes.csv`: per-policy, per-seed response prediction metrics.

This makes it possible to join prediction error against mined
`variant_edges.csv` outcome-change labels.

## Command

```bash
conda run -n autodrift python -m autodrift.response_prediction_eval \
  --env-config configs/ppo_m24_human_view_gru_driver.json \
  --seed-csv runs/m38_m37_102_matched_response_corpus_seed4300/scenario_corpus.csv \
  --checkpoint-policy m37_102=runs/ppo_m37_multistep_response_aux_seed1637/checkpoints/checkpoint_step_102400.pt \
  --checkpoint-policy m39_053=runs/ppo_m39_m37_response_corpus_seed1739/checkpoints/checkpoint_step_53248.pt \
  --device cpu \
  --run-dir runs/m41_response_prediction_per_seed_m38_seed4300
```

Aggregate result:

| Policy | Total MSE | H1 MSE | H2 MSE | H3 MSE | H4 MSE |
| --- | ---: | ---: | ---: | ---: | ---: |
| M37_102 | 0.019116 | 0.015900 | 0.021383 | 0.021512 | 0.017723 |
| M39_053 | 0.011935 | 0.012043 | 0.012367 | 0.012476 | 0.010822 |

Per-seed join against M38 `variant_edges.csv`:

| Policy | Success-Changed Seeds | Non-Changed Seeds | MSE on Changed | MSE on Non-Changed |
| --- | ---: | ---: | ---: | ---: |
| M37_102 | 4 | 76 | 0.017595 | 0.018401 |
| M39_053 | 4 | 76 | 0.011282 | 0.011254 |

M39 minus M37 MSE delta:

| Seed Group | Seeds | Delta Mean |
| --- | ---: | ---: |
| not success-changed | 76 | -0.007147 |
| success-changed | 4 | -0.006313 |

## Conclusion

Prediction MSE does not identify behavior-critical seeds. The success-changed
seeds are not harder under the response-prediction metric, and M39 reduces MSE
on both success-changed and non-changed seeds while weakening ablation
sensitivity.

The next objective should be intervention or behavior sensitive. M42 should
not simply add more MSE supervision or continue replaying hard seeds; it should
use gate labels, action differences, or reset/zero-response interventions as
training or selection signals.
