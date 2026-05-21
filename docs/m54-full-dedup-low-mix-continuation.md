# M54: Full Deduplicated Low-Mix Continuation

## Motivation

M53 showed that deduplicating the M50 margin-critical corpus and reducing hard
seed mix was less damaging than M51's row-level 70% replay. M54 runs the full
M53 continuation from `m37_102` and applies the same strict margin-retention
gate used in M52.

## Training

Command:

```bash
conda run -n autodrift python -m autodrift.train_ppo \
  --config configs/ppo_m53_dedup_low_mix_margin_retention_driver.json \
  --seed 2253 \
  --device cuda \
  --init-checkpoint runs/ppo_m37_multistep_response_aux_seed1637/checkpoints/checkpoint_step_102400.pt \
  --run-dir runs/ppo_m53_dedup_low_mix_margin_retention_seed2253
```

Result:

- return code: `0`;
- init load mode: `strict`;
- final eval return mean: `67.124`;
- final eval termination rate: `0.100`;
- final checkpoint: `runs/ppo_m53_dedup_low_mix_margin_retention_seed2253/checkpoint.pt`;
- periodic checkpoints: `28672`, `53248`, `77824`, `102400`, `126976`,
  `151552`, `176128`, and `200000`.

## Evaluation

M38, broad, and fresh checkpoint sweeps:

- `runs/m54_m38_margin_benchmark_seed4300`;
- `runs/m54_broad_margin_benchmark_seed3000`;
- `runs/m54_fresh_margin_benchmark_seed5200`.

Margin corpus and strict gate:

- `runs/m54_margin_critical_corpus`;
- `runs/m54_margin_retention_gate_strict`.

Strict gate summary:

| Candidate | Passed | Success delta | Binary regressions | Binary improvements | Near-margin regressions | Margin delta mean |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| m54_028 | false | -0.00625 | 2 | 1 | 11 | 0.000091 |
| m54_053 | false | -0.01875 | 3 | 0 | 5 | -0.000904 |
| m54_077 | false | -0.01875 | 3 | 0 | 5 | 0.001423 |
| m54_102 | false | -0.02500 | 4 | 0 | 4 | 0.000941 |
| m54_126 | false | -0.00625 | 2 | 1 | 9 | 0.002993 |
| m54_151 | false | -0.02500 | 4 | 0 | 6 | 0.002676 |
| m54_176 | false | -0.02500 | 4 | 0 | 4 | -0.002094 |
| m54_200 | false | -0.00625 | 2 | 1 | 9 | 0.000970 |

Source-level checkpoint sweep:

| Source | Policy | Success | Mean margin |
| --- | --- | ---: | ---: |
| M38 | m37_102 | 0.625 | 0.283562 |
| M38 | m54_028 | 0.625 | 0.286121 |
| M38 | m54_126 | 0.625 | 0.286786 |
| M38 | m54_200 | 0.625 | 0.287458 |
| broad3000 | m37_102 | 0.825 | 1.398739 |
| broad3000 | m54_028 | 0.800 | 1.394191 |
| broad3000 | m54_126 | 0.800 | 1.393962 |
| broad3000 | m54_200 | 0.800 | 1.392698 |
| fresh5200 | m37_102 | 0.825 | 1.724806 |
| fresh5200 | m54_028 | 0.825 | 1.724599 |
| fresh5200 | m54_126 | 0.825 | 1.735107 |
| fresh5200 | m54_200 | 0.825 | 1.726935 |

## Diagnosis

M54 improves the M52 failure mode but still does not pass promotion:

- M38 success can be retained while mean margin rises slightly.
- Fresh randomized success is retained for every checkpoint.
- Broad seed `3000` still regresses by one or two binary outcomes for every
  checkpoint.
- The best checkpoints by success delta are `m54_028`, `m54_126`, and
  `m54_200`; each still has two binary regressions.

The recurring binary regressions are near-boundary unavoidable cases:

| Seed | Source | Baseline margin | Best candidate margin | Pattern |
| ---: | --- | ---: | ---: | --- |
| 4457 | M38 | 0.029278 | -0.009960 to -0.024108 | M37 passes; M54 crosses into small penetration |
| 3037 | broad3000 | 0.009387 | -0.005461 to -0.022983 | M37 passes; M54 crosses into small penetration |

M54 therefore gives useful evidence: deduplicated low-mix training can improve
mean margin, but even conservative full continuation shifts the boundary on a
few millimeter-scale positive cases. The strict gate is doing the right thing
by rejecting these checkpoints.

## Conclusion

M54 is a negative promotion result and a positive diagnosis result. No M54
checkpoint replaces `m37_102`. Current best remains `m37_102`.

## Next Step

M55 should test an even more conservative continuation:

- lower PPO learning rate from `3e-5` to `1e-5`;
- lower hard-seed mix from `0.35` to `0.15`;
- remove the low-mu-only first curriculum stage so ordinary randomized
  retention remains dominant throughout;
- save dense early checkpoints every `4096` steps over `32768` total steps;
- promote only if strict gate reports zero binary regressions and zero
  near-margin regressions.
