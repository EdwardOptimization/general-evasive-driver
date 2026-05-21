# M59 Trust-Region Checkpoint Interpolation

Last updated: 2026-05-21

## Motivation

M56_028 was the closest non-promoted checkpoint after the M56-M58 margin
retention experiments: it had zero binary regressions and zero near-margin
regressions, but still lost mean clearance margin versus M37_102. M59 tests a
small trust-region question before adding more reward shaping:

Can a partial parameter-space move from M37_102 toward M56_028 pass the
unchanged strict margin-retention gate?

## Harness

M59 adds `autodrift.checkpoint_interpolation`:

- validates identical `model_state` keys, tensor shapes, and dtypes;
- validates compatible actor model config keys;
- interpolates floating tensors as
  `base + alpha * (target - base)`;
- rejects changed non-floating tensors;
- writes loadable checkpoint artifacts, `manifest.json`,
  `checkpoint_policies.csv`, and pasteable checkpoint-policy args.

Focused validation:

```bash
conda run -n autodrift pytest -q \
  tests/test_checkpoint_interpolation.py \
  tests/test_checkpoints.py
```

Result: `31 passed`.

## Source Checkpoints

- base: `m37_102`
  (`runs/ppo_m37_multistep_response_aux_seed1637/checkpoints/checkpoint_step_102400.pt`)
- target: `m56_028`
  (`runs/ppo_m56_clearance_margin_reward_seed2456/checkpoints/checkpoint_step_28672.pt`)
- alphas: `0.125`, `0.25`, `0.375`, `0.5`, `0.625`, `0.75`, `0.875`
- artifacts: `runs/m59_m37_m56_028_interpolated_checkpoints`

Command:

```bash
conda run -n autodrift python -m autodrift.checkpoint_interpolation \
  --base-checkpoint runs/ppo_m37_multistep_response_aux_seed1637/checkpoints/checkpoint_step_102400.pt \
  --target-checkpoint runs/ppo_m56_clearance_margin_reward_seed2456/checkpoints/checkpoint_step_28672.pt \
  --alphas 0.125 0.25 0.375 0.5 0.625 0.75 0.875 \
  --base-label m37_102 \
  --target-label m56_028 \
  --label-prefix m59 \
  --run-dir runs/m59_m37_m56_028_interpolated_checkpoints
```

All generated checkpoints load through the existing actor loader with the
canonical 72-value human-view observation contract.

## Evaluation

Benchmarks used the unchanged M38/broad/fresh margin-retention setup:

- `runs/m59_m38_margin_benchmark_seed4300`
- `runs/m59_broad_margin_benchmark_seed3000`
- `runs/m59_fresh_margin_benchmark_seed5200`
- `runs/m59_margin_critical_corpus`
- `runs/m59_margin_retention_gate_strict`

Strict gate thresholds:

- `min_success_delta = 0.0`
- `max_binary_regressed_seeds = 0`
- `max_near_margin_regressed_seeds = 0`
- `min_margin_delta_mean = 0.0`

## Results

| Candidate | Success Delta | Binary Regressions | Near-Margin Regressions | Mean Margin Delta | Passed |
| --- | ---: | ---: | ---: | ---: | --- |
| `m59_a125` | 0.000000 | 0 | 0 | -0.000193 | false |
| `m59_a250` | 0.000000 | 0 | 0 | -0.000384 | false |
| `m59_a375` | 0.000000 | 0 | 0 | -0.000575 | false |
| `m59_a500` | 0.000000 | 0 | 0 | -0.000765 | false |
| `m59_a625` | 0.000000 | 0 | 0 | -0.000956 | false |
| `m59_a750` | 0.000000 | 0 | 0 | -0.001145 | false |
| `m59_a875` | 0.000000 | 0 | 0 | -0.001335 | false |

Aggregate benchmark observations:

| Source | Baseline Success | Candidate Success | Best Alpha By Margin | Best Mean Margin Delta |
| --- | ---: | ---: | --- | ---: |
| M38 shared seed | 0.625 | 0.625 | `m59_a125` | -0.000205 |
| broad seed3000 | 0.825 | 0.825 | `m59_a125` | -0.000159 |
| fresh seed5200 | 0.825 | 0.825 | `m59_a125` | -0.000201 |

The corpus contains 1120 candidate-baseline pairs. There are no binary outcome
changes and no near-margin regressions, but every nonzero alpha lowers mean
clearance margin. The margin loss is almost linear in alpha, which suggests the
M37-to-M56_028 parameter direction is behaviorally conservative but not a
positive-margin direction.

## Conclusion

M59 is a negative but useful diagnostic. Interpolation toward M56_028 creates a
smooth, low-risk policy family, but it does not pass strict mean-margin
retention. This argues against more reward-scale tuning along the same
continuation direction.

Next work should use the M59/M56 evidence to build a more explicit constrained
update path:

- keep M37_102 as the behavior anchor;
- target only seed/action snippets where margin can improve without changing
  binary outcome;
- penalize deterministic action drift from M37 on non-critical states;
- evaluate with the unchanged strict margin-retention gate.
