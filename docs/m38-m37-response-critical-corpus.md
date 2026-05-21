# M38 M37 Response-Critical Corpus

Last updated: 2026-05-21

## Motivation

M37_102 is the first human-view GRU checkpoint that improves the M35
response-change corpus while preserving M29 and broad success. It still fails
hidden-swap, but reset and zero-response ablations now create unfavorable
outcome changes on accepted perturbed cases.

M38 expands that gate to 300 episodes and mines a sharper follow-up corpus.

## Gate Command

```bash
conda run -n autodrift python -m autodrift.hidden_swap_gate \
  --env-config configs/ppo_m24_human_view_gru_driver.json \
  --checkpoint runs/ppo_m37_multistep_response_aux_seed1637/checkpoints/checkpoint_step_102400.pt \
  --episodes 300 \
  --seed 4300 \
  --device cpu \
  --run-dir runs/m37_102_hidden_swap_gate_seed4300
```

Result:

- accepted visible matches: 280 / 300;
- accepted nominal normal/reset/zero-response/hidden-swap success:
  0.936 / 0.936 / 0.936 / 0.936;
- accepted perturbed normal/reset/zero-response/hidden-swap success:
  0.675 / 0.657 / 0.657 / 0.675;
- perturbed reset outcome changes: 5, all unfavorable;
- perturbed zero-response outcome changes: 5, all unfavorable;
- hidden-swap outcome changes: 0.

Conclusion: M37_102 is not a hidden-swap self-identification pass. It is,
however, the cleanest response-critical recurrent signal so far: reset and
zero-response hurt rather than help.

## Corpus Command

```bash
conda run -n autodrift python -m autodrift.matched_response_corpus \
  --pairs-csv runs/m37_102_hidden_swap_gate_seed4300/pairs.csv \
  --replays-csv runs/m37_102_hidden_swap_gate_seed4300/replays.csv \
  --top-k 80 \
  --min-hidden-state-distance 0.8 \
  --max-context-observation-distance 0.15 \
  --run-dir runs/m38_m37_102_matched_response_corpus_seed4300
```

Corpus summary:

- candidate seeds: 300;
- accepted seeds: 280;
- selected seeds: 80;
- success-changed seeds: 11;
- success-changed edges: 18;
- condition-changed seeds: 76;
- perturbed-failure seeds: 91;
- accepted mean hidden-state distance: 1.269;
- selected score mean: 9.372.

Next step: M39 should continue from M37_102 with the same multi-step auxiliary
objective and the M38 corpus. The purpose is to test whether the clean
reset/zero-response sensitivity can be strengthened without losing aggregate
success. Hidden-swap remains the hard blocker.
