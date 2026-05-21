# M50: Margin-Critical Corpus

## Motivation

M49 made obstacle clearance margin measurable. M50 turns that metric into a
corpus-mining gate so the next training cycle can target near-boundary driver
failures instead of optimizing only aggregate success.

The key correction in M50 is that not every margin regression is useful for a
driver gate. A policy can lose several centimeters of clearance while still
passing meters away from the obstacle. The corpus therefore treats a regression
as critical only when it is near the collision boundary.

## Harness

M50 adds:

- `src/autodrift/margin_critical_corpus.py`;
- `tests/test_margin_critical_corpus.py`;
- CLI script: `autodrift-margin-critical-corpus`.

Inputs:

- one or more benchmark `episodes.csv` files;
- one baseline policy;
- one or more candidate policies;
- `near_margin`: boundary threshold for near misses/collisions;
- `min_abs_margin_delta`: material margin delta threshold.

Outputs:

- `seed_margin_deltas.csv`: all shared-seed policy deltas with margin features;
- `scenario_corpus.csv`: selected critical rows;
- `policy_margin_summary.csv`: policy-level margin counts and means;
- `margin_bucket_summary.csv`: grouped margin/bucket diagnostics;
- `manifest.json`.

The harness processes each source benchmark independently before concatenating
deltas, so identical seed IDs from different sweeps do not collide.

## Critical Definition

M50 records raw `margin_regressed` for analysis, but `critical_reason` is
restricted to:

- binary outcome changes;
- near-boundary cases;
- near-boundary margin regressions;
- low positive-margin successes;
- small-penetration collisions.

This keeps the corpus focused on driving near the obstacle boundary instead of
large-margin cosmetic differences.

## Commands

M38 margin-aware benchmark:

```bash
conda run -n autodrift python -m autodrift.benchmark \
  --env-config configs/ppo_m24_human_view_gru_driver.json \
  --seed-csv runs/m38_m37_102_matched_response_corpus_seed4300/scenario_corpus.csv \
  --policies envelope_aes \
  --checkpoint-policy m37_102=runs/ppo_m37_multistep_response_aux_seed1637/checkpoints/checkpoint_step_102400.pt \
  --checkpoint-policy m42_028=runs/ppo_m42_hidden_contrast_seed1842/checkpoints/checkpoint_step_28672.pt \
  --checkpoint-policy m46_077=runs/ppo_m46_paired_hidden_action_contrast_seed2046/checkpoints/checkpoint_step_77824.pt \
  --checkpoint-policy m46_200=runs/ppo_m46_paired_hidden_action_contrast_seed2046/checkpoints/checkpoint_step_200000.pt \
  --device cpu \
  --run-dir runs/m50_m38_margin_benchmark_seed4300
```

Broad same-seed benchmark:

```bash
conda run -n autodrift python -m autodrift.benchmark \
  --env-config configs/ppo_m24_human_view_gru_driver.json \
  --episodes 40 \
  --seed 3000 \
  --policies envelope_aes \
  --checkpoint-policy m37_102=runs/ppo_m37_multistep_response_aux_seed1637/checkpoints/checkpoint_step_102400.pt \
  --checkpoint-policy m42_028=runs/ppo_m42_hidden_contrast_seed1842/checkpoints/checkpoint_step_28672.pt \
  --checkpoint-policy m46_077=runs/ppo_m46_paired_hidden_action_contrast_seed2046/checkpoints/checkpoint_step_77824.pt \
  --checkpoint-policy m46_200=runs/ppo_m46_paired_hidden_action_contrast_seed2046/checkpoints/checkpoint_step_200000.pt \
  --device cpu \
  --run-dir runs/m50_broad_margin_benchmark_seed3000
```

Fresh randomized benchmark:

```bash
conda run -n autodrift python -m autodrift.benchmark \
  --env-config configs/ppo_m24_human_view_gru_driver.json \
  --episodes 40 \
  --seed 5200 \
  --policies envelope_aes \
  --checkpoint-policy m37_102=runs/ppo_m37_multistep_response_aux_seed1637/checkpoints/checkpoint_step_102400.pt \
  --checkpoint-policy m42_028=runs/ppo_m42_hidden_contrast_seed1842/checkpoints/checkpoint_step_28672.pt \
  --checkpoint-policy m46_077=runs/ppo_m46_paired_hidden_action_contrast_seed2046/checkpoints/checkpoint_step_77824.pt \
  --checkpoint-policy m46_200=runs/ppo_m46_paired_hidden_action_contrast_seed2046/checkpoints/checkpoint_step_200000.pt \
  --device cpu \
  --run-dir runs/m50_fresh_margin_benchmark_seed5200
```

Corpus command:

```bash
conda run -n autodrift python -m autodrift.margin_critical_corpus \
  --episodes-csv runs/m50_m38_margin_benchmark_seed4300/episodes.csv \
  --episodes-csv runs/m50_broad_margin_benchmark_seed3000/episodes.csv \
  --episodes-csv runs/m50_fresh_margin_benchmark_seed5200/episodes.csv \
  --baseline-policy m37_102 \
  --candidate-policy m42_028 \
  --candidate-policy m46_077 \
  --candidate-policy m46_200 \
  --near-margin 0.05 \
  --min-abs-margin-delta 0.02 \
  --top-k 100 \
  --run-dir runs/m50_margin_critical_corpus_m38_broad_fresh
```

## Benchmark Summary

M38 response-critical corpus:

| Policy | Success | Margin mean | Margin min |
| --- | ---: | ---: | ---: |
| m37_102 | 0.6250 | 0.283562 | -0.225406 |
| m42_028 | 0.6250 | 0.283084 | -0.234003 |
| m46_077 | 0.6375 | 0.286226 | -0.241341 |
| m46_200 | 0.6375 | 0.288182 | -0.219801 |

Broad same-seed:

| Policy | Success | Margin mean | Margin min |
| --- | ---: | ---: | ---: |
| m37_102 | 0.8250 | 1.398739 | -0.124835 |
| m42_028 | 0.8250 | 1.400568 | -0.115022 |
| m46_077 | 0.8000 | 1.398962 | -0.142298 |
| m46_200 | 0.8000 | 1.399091 | -0.102308 |

Fresh seed 5200:

| Policy | Success | Margin mean | Margin min |
| --- | ---: | ---: | ---: |
| m37_102 | 0.8250 | 1.724806 | -0.074607 |
| m42_028 | 0.8250 | 1.735200 | -0.091574 |
| m46_077 | 0.8250 | 1.736777 | -0.069714 |
| m46_200 | 0.8250 | 1.738725 | -0.055816 |

## Corpus Summary

Final corpus source:

```text
runs/m50_margin_critical_corpus_m38_broad_fresh/scenario_corpus.csv
```

Overall:

- pairs: 480;
- selected rows: 100;
- critical rows: 118;
- near-boundary rows: 118;
- raw margin-regressed rows: 24;
- binary outcome changed rows: 4.

Policy-level deltas versus `m37_102`:

| Candidate | Pairs | Critical | Near regressed | Binary changed | Margin delta mean |
| --- | ---: | ---: | ---: | ---: | ---: |
| m42_028 | 160 | 38 | 3 | 0 | 0.002817 |
| m46_077 | 160 | 39 | 4 | 2 | 0.004381 |
| m46_200 | 160 | 41 | 10 | 2 | 0.005878 |

The selected top-100 corpus includes rows from all three sources:

- M38: 61 rows;
- broad seed 3000: 24 rows;
- fresh seed 5200: 14 rows.

## Conclusion

M50 explains why aggregate and mean margin are still insufficient. M46 improves
mean margin and M38 success, but it also introduces more near-boundary margin
regressions and keeps the broad success regression from M46. M46 therefore
still cannot replace `m37_102`.

The current best remains `m37_102`.

## Next Step

M51 should turn the M50 corpus into a margin-retention gate and training
objective:

- preserve M37_102 broad success;
- reject candidates with increased near-boundary margin regressions;
- oversample M50 near-boundary rows during continuation training;
- use margin-aware reward/checkpoint selection without adding margin or oracle
  fields to actor observations.
