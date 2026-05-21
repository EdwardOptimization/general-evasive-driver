# M57: Clearance-Margin Reward Scale 4

## Motivation

M56 showed that terminal clearance-margin reward scale `2.0` can produce a
checkpoint with zero binary regressions and zero near-margin regressions, but
the combined mean margin remains slightly negative. M57 repeats the same
schedule with terminal reward scale `4.0`.

## Training

Command:

```bash
conda run -n autodrift python -m autodrift.train_ppo \
  --config configs/ppo_m57_clearance_margin_reward_scale4_driver.json \
  --seed 2557 \
  --device cuda \
  --init-checkpoint runs/ppo_m37_multistep_response_aux_seed1637/checkpoints/checkpoint_step_102400.pt \
  --run-dir runs/ppo_m57_clearance_margin_reward_scale4_seed2557
```

Result:

- return code: `0`;
- init load mode: `strict`;
- curriculum stage: `base`;
- final eval return mean: `79.304`;
- final eval termination rate: `0.100`;
- checkpoints: `4096`, `8192`, `12288`, `16384`, `20480`, `24576`, `28672`,
  and `32768`.

## Evaluation

Checkpoint sweeps:

- `runs/m57_m38_margin_benchmark_seed4300`;
- `runs/m57_broad_margin_benchmark_seed3000`;
- `runs/m57_fresh_margin_benchmark_seed5200`.

Margin corpus and strict gate:

- `runs/m57_margin_critical_corpus`;
- `runs/m57_margin_retention_gate_strict`.

Strict gate summary:

| Candidate | Passed | Success delta | Binary regressions | Near-margin regressions | Margin delta mean |
| --- | --- | ---: | ---: | ---: | ---: |
| m57_004 | false | 0.00000 | 0 | 1 | -0.000729 |
| m57_008 | false | 0.00000 | 0 | 4 | -0.001912 |
| m57_012 | false | 0.00000 | 0 | 4 | -0.001559 |
| m57_016 | false | -0.00625 | 1 | 7 | -0.002055 |
| m57_020 | false | -0.00625 | 1 | 6 | -0.001771 |
| m57_024 | false | 0.00000 | 0 | 3 | -0.001863 |
| m57_028 | false | 0.00000 | 0 | 2 | -0.003078 |
| m57_032 | false | 0.00000 | 0 | 6 | -0.001813 |

## Diagnosis

Increasing terminal reward scale from `2.0` to `4.0` does not improve the best
gate point:

- M56 best checkpoint `m56_028`: zero binary regressions, zero near-margin
  regressions, margin delta mean `-0.001527`;
- M57 best by binary outcome is not better: every zero-binary checkpoint still
  has near-margin regressions or a negative mean margin;
- broad and fresh success are retained, but M38 mean margin remains below
  M37_102.

The sparse terminal reward is too weak or too delayed for margin retention.
More terminal scale mostly changes the policy trajectory without solving the
credit-assignment problem.

## Conclusion

M57 is not promotable. Current best remains `m37_102`; the closest non-promoted
candidate remains `m56_028`.

## Next Step

M58 should move from sparse terminal margin reward to a config-gated dense
near-obstacle clearance signal, active only near the obstacle encounter window.
The strict promotion gate should remain unchanged.
