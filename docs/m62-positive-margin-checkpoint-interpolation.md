# M62 Positive-Margin Checkpoint Interpolation

Last updated: 2026-05-21

## Motivation

M61 produced the first useful source direction for margin retention:
`m61_032` had zero binary regressions and positive combined mean margin delta,
but still had three near-margin regressions. M62 reuses the M59 interpolation
harness and tests whether a smaller M37_102 to M61_032 step can keep the
positive mean-margin direction while removing those regressions.

## Interpolation

Source checkpoints:

- base: `m37_102`
  (`runs/ppo_m37_multistep_response_aux_seed1637/checkpoints/checkpoint_step_102400.pt`);
- target: `m61_032`
  (`runs/ppo_m61_regression_seed_retention_seed2861/checkpoints/checkpoint_step_32768.pt`).

Command:

```bash
conda run -n autodrift python -m autodrift.checkpoint_interpolation \
  --base-checkpoint runs/ppo_m37_multistep_response_aux_seed1637/checkpoints/checkpoint_step_102400.pt \
  --target-checkpoint runs/ppo_m61_regression_seed_retention_seed2861/checkpoints/checkpoint_step_32768.pt \
  --alphas 0.125 0.25 0.375 0.5 0.625 0.75 0.875 \
  --base-label m37_102 \
  --target-label m61_032 \
  --label-prefix m62 \
  --run-dir runs/m62_m37_m61_032_interpolated_checkpoints
```

All generated checkpoints load through the canonical 72-value human-view actor
contract.

## Strict Margin Gate

Validation artifacts:

- `runs/m62_m38_margin_benchmark_seed4300`;
- `runs/m62_broad_margin_benchmark_seed3000`;
- `runs/m62_fresh_margin_benchmark_seed5200`;
- `runs/m62_margin_critical_corpus`;
- `runs/m62_margin_retention_gate_strict`.

Strict gate result: `passed`.

| Candidate | Success Delta | Binary Regressions | Near-Margin Regressions | Mean Margin Delta | Passed |
| --- | ---: | ---: | ---: | ---: | --- |
| `m62_a125` | 0.000000 | 0 | 0 | 0.000278 | true |
| `m62_a250` | 0.000000 | 0 | 0 | 0.000552 | true |
| `m62_a375` | 0.000000 | 0 | 1 | 0.000091 | false |
| `m62_a500` | 0.000000 | 0 | 1 | 0.000355 | false |
| `m62_a625` | 0.000000 | 0 | 1 | 0.000615 | false |
| `m62_a750` | 0.000000 | 0 | 3 | -0.000202 | false |
| `m62_a875` | 0.000000 | 0 | 3 | 0.000048 | false |

Source-level deltas for `m62_a250`:

| Source | Success Delta | Binary Regressions | Near-Margin Regressions | Mean Margin Delta |
| --- | ---: | ---: | ---: | ---: |
| M38 shared seed | 0.000000 | 0 | 0 | 0.000495 |
| broad seed3000 | 0.000000 | 0 | 0 | 0.000425 |
| fresh seed5200 | 0.000000 | 0 | 0 | 0.000791 |

## Hidden-Swap Audit

`m62_a250` was also run through the same 300-episode hidden-swap gate used for
M37_102:

```bash
conda run -n autodrift python -m autodrift.hidden_swap_gate \
  --env-config configs/ppo_m24_human_view_gru_driver.json \
  --checkpoint runs/m62_m37_m61_032_interpolated_checkpoints/checkpoints/alpha_0_25.pt \
  --episodes 300 \
  --seed 4300 \
  --device cpu \
  --run-dir runs/m62_a250_hidden_swap_gate_seed4300
```

Accepted-match success rates match M37_102:

| Condition | Normal Success | Hidden-Swap Success | Reset Success | Zero-Response Success |
| --- | ---: | ---: | ---: | ---: |
| nominal | 0.935714 | 0.935714 | 0.935714 | 0.935714 |
| perturbed | 0.675000 | 0.675000 | 0.657143 | 0.657143 |

This does not solve the recurrent self-identification blocker, but it shows
that the M62 interpolation did not make the existing hidden-swap diagnostic
worse.

## Conclusion

M62 is the first checkpoint family in the margin-retention series to pass the
strict gate. `m62_a250` is stronger than M37_102 on the current margin-retention
evidence:

- same aggregate success on M38, broad, and fresh;
- zero binary regressions;
- zero near-margin regressions;
- positive mean clearance-margin delta;
- no hidden-swap diagnostic regression versus M37_102.

`m62_a250` should replace M37_102 as the current best margin-retention driver
candidate. It is still not an ideal driver: hidden-swap remains outcome-neutral,
and a broader driver audit is required before treating it as a full driver
promotion.

## Next Step

M63 should run a broader driver audit for `m62_a250`: held-out benchmark,
history/action ablations, hidden-swap summary comparison, and any remaining
driver gates that can use the human-view observation contract.
