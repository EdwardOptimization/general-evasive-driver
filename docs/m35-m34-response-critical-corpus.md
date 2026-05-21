# M35 M34 Response-Critical Corpus

Last updated: 2026-05-21

## Motivation

M34 response-prediction auxiliary training did not make hidden-swap behavior
critical, but it did create a small number of `reset` and `zero_response`
outcome changes in perturbed accepted hidden-swap cases. M35 enlarges that
sample so the next training run can focus on cases where observable response
features are already behavior-sensitive.

This is still not proof of recurrent self-identification. It is a corpus
construction step.

## Gate Command

```bash
conda run -n autodrift python -m autodrift.hidden_swap_gate \
  --env-config configs/ppo_m24_human_view_gru_driver.json \
  --checkpoint runs/ppo_m34_response_aux_mixed_seed1434/checkpoints/checkpoint_step_151552.pt \
  --episodes 300 \
  --seed 4300 \
  --device cpu \
  --run-dir runs/m35_m34_151_hidden_swap_gate_seed4300
```

Result:

- accepted visible matches: 281 / 300;
- accepted nominal normal/reset/zero-response/hidden-swap success:
  0.932 / 0.932 / 0.932 / 0.932;
- accepted perturbed normal/reset/zero-response/hidden-swap success:
  0.662 / 0.669 / 0.665 / 0.662;
- perturbed accepted reset outcome changes: 4 total, 1 unfavorable and 3
  favorable;
- perturbed accepted zero-response outcome changes: 5 total, 2 unfavorable and
  3 favorable;
- hidden-swap outcome changes: 0.

Conclusion: M35 confirms the M34 negative result for hidden-swap, while also
finding enough response-ablation-sensitive seeds to build a sharper follow-up
corpus.

## Corpus Command

```bash
conda run -n autodrift python -m autodrift.matched_response_corpus \
  --pairs-csv runs/m35_m34_151_hidden_swap_gate_seed4300/pairs.csv \
  --replays-csv runs/m35_m34_151_hidden_swap_gate_seed4300/replays.csv \
  --top-k 80 \
  --min-hidden-state-distance 0.8 \
  --max-context-observation-distance 0.15 \
  --run-dir runs/m35_m34_151_matched_response_corpus_seed4300
```

Corpus summary:

- candidate seeds: 300;
- accepted seeds: 281;
- selected seeds: 80;
- success-changed seeds: 5;
- success-changed edges: 9;
- condition-changed seeds: 76;
- perturbed-failure seeds: 95;
- accepted mean hidden-state distance: 1.292;
- selected score mean: 10.064.

Next step: M36 should fine-tune from M34_151 on this corpus, then re-run M29,
broad same-seed, and hidden-swap gates. The pass condition is not higher broad
success alone; hidden-swap or reset/zero-response ablations must become
unfavorably behavior-critical on accepted matched cases.
