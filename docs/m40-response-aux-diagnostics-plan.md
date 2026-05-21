# M40 Response-Aux Diagnostics Plan

Last updated: 2026-05-21

## Motivation

M37 produced the strongest response-critical signal so far, but M39 showed that
continuing on a sharper corpus can weaken that signal. The project currently
does not log or evaluate the response-prediction auxiliary objective directly,
so checkpoint selection is based only on downstream success and ablation
effects.

M40 should add diagnostics for the response auxiliary head before the next
training change.

## Planned Work

- Log response auxiliary loss in PPO train metrics when the auxiliary is
  enabled.
- Add an offline response-prediction evaluator for checkpoint comparisons.
- Evaluate M34, M37_102, and M39 candidates on M35/M38 corpus rollouts.
- Report prediction loss by horizon step for multi-step heads.
- Keep the actor input contract unchanged; this is diagnostic only.

## Why This Matters

If M37's response-critical behavior came from a genuinely better future
response model, M37_102 should have lower multi-step prediction error than M34
or M39 on response-change cases. If not, the auxiliary objective may be acting
as incidental regularization, and the next architecture should change the
latent objective rather than tuning the corpus mix again.

## Implementation

Implemented:

- `train_metrics.csv` now includes `response_prediction_loss_mean` when the
  auxiliary loss is enabled.
- `python -m autodrift.response_prediction_eval` evaluates checkpoint response
  heads on rollout observations and writes `prediction_summary.csv`.
- The evaluator reports total MSE and per-horizon MSE/valid-target counts.

Smoke command:

```bash
conda run -n autodrift python -m autodrift.response_prediction_eval \
  --env-config configs/ppo_m24_human_view_gru_driver.json \
  --seed-csv runs/m38_m37_102_matched_response_corpus_seed4300/scenario_corpus.csv \
  --checkpoint-policy m34_151=runs/ppo_m34_response_aux_mixed_seed1434/checkpoints/checkpoint_step_151552.pt \
  --checkpoint-policy m37_102=runs/ppo_m37_multistep_response_aux_seed1637/checkpoints/checkpoint_step_102400.pt \
  --checkpoint-policy m39_053=runs/ppo_m39_m37_response_corpus_seed1739/checkpoints/checkpoint_step_53248.pt \
  --device cpu \
  --run-dir runs/m40_response_prediction_eval_m38_seed4300
```

Result:

| Policy | Horizon | Total MSE | H1 MSE | H2 MSE | H3 MSE | H4 MSE |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| M34_151 | 1 | 0.015019 | 0.015019 | n/a | n/a | n/a |
| M37_102 | 4 | 0.019116 | 0.015900 | 0.021383 | 0.021512 | 0.017723 |
| M39_053 | 4 | 0.011935 | 0.012043 | 0.012367 | 0.012476 | 0.010822 |

Conclusion: lower response-prediction MSE is not sufficient. M39_053 predicts
future response better than M37_102 on this corpus but has a weaker
reset/zero-response ablation signal. The next objective should be behavior
sensitivity aware, not merely MSE-minimizing.
