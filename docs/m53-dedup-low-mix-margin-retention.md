# M53: Deduplicated Low-Mix Margin Retention

## Motivation

M52 showed that direct high-probability replay of the M50 row-level corpus
overweights a small set of near-boundary seeds. The M50 top-100 corpus contains
100 rows but only 41 unique seeds, and M51 sampled those rows with 70%
probability.

M53 changes the data mixture before another full run:

- deduplicate to seed level;
- reduce hard-seed mix probability;
- keep broad randomized retention dominant.

## Seed Corpus

M53 adds:

- `src/autodrift/training_seed_corpus.py`;
- `tests/test_training_seed_corpus.py`;
- CLI script: `autodrift-training-seed-corpus`.

Command:

```bash
conda run -n autodrift python -m autodrift.training_seed_corpus \
  --corpus-csv runs/m50_margin_critical_corpus_m38_broad_fresh/scenario_corpus.csv \
  --run-dir runs/m53_dedup_margin_training_seeds
```

Result:

- input rows: 100;
- unique seeds: 41;
- source count: 3.

Source distribution:

| Source | Unique seeds |
| --- | ---: |
| m50_m38_margin_benchmark_seed4300 | 26 |
| m50_broad_margin_benchmark_seed3000 | 9 |
| m50_fresh_margin_benchmark_seed5200 | 6 |

Artifact:

```text
runs/m53_dedup_margin_training_seeds/seed_sequence.csv
```

## Training Config

M53 adds:

```text
configs/ppo_m53_dedup_low_mix_margin_retention_driver.json
```

Changes from M51:

- `training_seed_csv` uses the deduplicated seed sequence;
- `training_seed_mix_probability` drops from `0.70` to `0.35`;
- actor observation contract is unchanged;
- response-prediction auxiliary loss is retained;
- paired-hidden action contrast remains disabled.

## Smoke

Training smoke:

```bash
conda run -n autodrift python -m autodrift.train_ppo \
  --config configs/ppo_m53_dedup_low_mix_margin_retention_driver.json \
  --total-steps 4096 \
  --rollout-steps 128 \
  --seed 2253 \
  --device cuda \
  --init-checkpoint runs/ppo_m37_multistep_response_aux_seed1637/checkpoints/checkpoint_step_102400.pt \
  --run-dir runs/ppo_m53_dedup_low_mix_smoke_seed2253
```

Smoke result:

- init load mode: `strict`;
- rollout return mean at 4096 steps: `55.74`;
- final eval return mean: `67.225`;
- final eval termination rate: `0.100`;
- checkpoint: `runs/ppo_m53_dedup_low_mix_smoke_seed2253/checkpoint.pt`.

## Smoke Gate

M38/broad/fresh smoke benchmark artifacts:

- `runs/m53_smoke_m38_margin_benchmark_seed4300`;
- `runs/m53_smoke_broad_margin_benchmark_seed3000`;
- `runs/m53_smoke_fresh_margin_benchmark_seed5200`.

Strict gate result:

| Candidate | Passed | Success delta | Binary regressions | Near-margin regressions | Margin delta mean |
| --- | --- | ---: | ---: | ---: | ---: |
| m53_smoke | false | -0.00625 | 1 | 2 | 0.001714 |

Source detail:

- M38: success retained, margin delta `0.000962`, 1 near-margin regression;
- broad: success drops by `0.025`, margin delta `-0.000265`, 1 binary
  regression, 1 near-margin regression;
- fresh: success retained, margin delta `0.005200`, no near-margin regression.

## Conclusion

M53 is an infrastructure and smoke improvement over M51, but not a promotable
checkpoint. The deduplicated low-mix smoke preserves M38 success and improves
combined mean margin, unlike M51 smoke, but the broad seed regression means the
strict gate still correctly rejects it.

Current best remains `m37_102`.

## Next Step

M54 should run the full deduplicated low-mix continuation, then sweep
checkpoints through the same M51 strict gate. This is justified because the
M53 smoke is materially less damaging than M51 smoke, but promotion still
requires zero broad regressions and zero near-boundary margin regressions.
