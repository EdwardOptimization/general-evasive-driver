# M55: Conservative Margin Retention

## Motivation

M54 improved mean margin but still flipped near-boundary positive outcomes on
M38 seed `4457` and broad seed `3037`. M55 tests whether a smaller update
window can preserve those positives:

- lower learning rate: `3e-5` to `1e-5`;
- lower hard-seed mix: `0.35` to `0.15`;
- no low-mu-only curriculum stage;
- dense checkpoints every `4096` steps over `32768` total steps.

## Training

Command:

```bash
conda run -n autodrift python -m autodrift.train_ppo \
  --config configs/ppo_m55_conservative_dedup_margin_retention_driver.json \
  --seed 2355 \
  --device cuda \
  --init-checkpoint runs/ppo_m37_multistep_response_aux_seed1637/checkpoints/checkpoint_step_102400.pt \
  --run-dir runs/ppo_m55_conservative_margin_retention_seed2355
```

Result:

- return code: `0`;
- init load mode: `strict`;
- curriculum stage: `base`;
- final eval return mean: `65.608`;
- final eval termination rate: `0.200`;
- checkpoints: `4096`, `8192`, `12288`, `16384`, `20480`, `24576`, `28672`,
  and `32768`.

## Evaluation

Checkpoint sweeps:

- `runs/m55_m38_margin_benchmark_seed4300`;
- `runs/m55_broad_margin_benchmark_seed3000`;
- `runs/m55_fresh_margin_benchmark_seed5200`.

Margin corpus and strict gate:

- `runs/m55_margin_critical_corpus`;
- `runs/m55_margin_retention_gate_strict`.

Strict gate summary:

| Candidate | Passed | Success delta | Binary regressions | Near-margin regressions | Margin delta mean |
| --- | --- | ---: | ---: | ---: | ---: |
| m55_004 | false | 0.00000 | 0 | 1 | -0.001267 |
| m55_008 | false | 0.00000 | 0 | 2 | -0.001564 |
| m55_012 | false | 0.00000 | 0 | 4 | -0.000718 |
| m55_016 | false | 0.00000 | 0 | 4 | -0.001653 |
| m55_020 | false | -0.00625 | 1 | 4 | -0.002702 |
| m55_024 | false | 0.00000 | 0 | 3 | -0.003250 |
| m55_028 | false | 0.00000 | 0 | 1 | -0.004328 |
| m55_032 | false | -0.01250 | 2 | 0 | -0.005191 |

Source-level result:

| Source | M37 success | Best M55 success | Best M55 margin delta |
| --- | ---: | ---: | ---: |
| M38 | 0.625 | 0.625 | -0.002810 |
| broad3000 | 0.825 | 0.825 | 0.000218 |
| fresh5200 | 0.825 | 0.825 | 0.000334 |

## Diagnosis

M55 fixes the M54 broad-regression failure mode:

- broad seed3000 success is retained at `0.825` for every checkpoint;
- fresh seed5200 success is retained at `0.825` for every checkpoint;
- the earliest checkpoint `m55_004` has zero binary regressions.

However, M55 still fails strict margin retention:

- `m55_004` has one near-margin regression and negative mean margin delta;
- later checkpoints progressively lose M38 margin and eventually introduce
  binary regressions;
- the conservative update mostly preserves behavior, but it does not learn a
  positive clearance-margin improvement.

M55 therefore shows that data mixture and learning-rate conservatism are not
enough. The training objective still lacks a direct signal for near-boundary
clearance margin.

## Conclusion

M55 is not promotable. Current best remains `m37_102`.

## Next Step

M56 should add terminal clearance-margin reward shaping for training only:

- actor observations remain unchanged and deployable;
- reward may use simulator clearance margin because it is not an actor input;
- the strict promotion gate stays unchanged;
- the experiment should start from M37_102 and reuse the M55 conservative
  schedule, so any improvement can be attributed to margin reward shaping.
