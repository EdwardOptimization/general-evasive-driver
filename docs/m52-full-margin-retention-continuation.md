# M52: Full Margin-Retention Continuation

## Motivation

M51 added a strict margin-retention gate and a continuation training config
that oversamples the M50 top-100 margin-critical corpus. M52 runs the full
training cycle and checks whether any checkpoint can replace `m37_102`.

## Training

Command:

```bash
conda run -n autodrift python -m autodrift.train_ppo \
  --config configs/ppo_m51_margin_retention_driver.json \
  --seed 2151 \
  --device cuda \
  --init-checkpoint runs/ppo_m37_multistep_response_aux_seed1637/checkpoints/checkpoint_step_102400.pt \
  --run-dir runs/ppo_m51_margin_retention_seed2151
```

Result:

- return code: `0`;
- init load mode: `strict`;
- final eval return mean: `68.008`;
- final eval termination rate: `0.100`;
- final checkpoint: `runs/ppo_m51_margin_retention_seed2151/checkpoint.pt`;
- periodic checkpoints:
  - `checkpoint_step_28672.pt`;
  - `checkpoint_step_53248.pt`;
  - `checkpoint_step_77824.pt`;
  - `checkpoint_step_102400.pt`;
  - `checkpoint_step_126976.pt`;
  - `checkpoint_step_151552.pt`;
  - `checkpoint_step_176128.pt`;
  - `checkpoint_step_200000.pt`.

## Evaluation Commands

M38 benchmark:

```bash
conda run -n autodrift python -m autodrift.benchmark \
  --env-config configs/ppo_m24_human_view_gru_driver.json \
  --seed-csv runs/m38_m37_102_matched_response_corpus_seed4300/scenario_corpus.csv \
  --policies envelope_aes \
  --checkpoint-policy m37_102=runs/ppo_m37_multistep_response_aux_seed1637/checkpoints/checkpoint_step_102400.pt \
  --checkpoint-policy m51_028=runs/ppo_m51_margin_retention_seed2151/checkpoints/checkpoint_step_28672.pt \
  --checkpoint-policy m51_053=runs/ppo_m51_margin_retention_seed2151/checkpoints/checkpoint_step_53248.pt \
  --checkpoint-policy m51_077=runs/ppo_m51_margin_retention_seed2151/checkpoints/checkpoint_step_77824.pt \
  --checkpoint-policy m51_102=runs/ppo_m51_margin_retention_seed2151/checkpoints/checkpoint_step_102400.pt \
  --checkpoint-policy m51_126=runs/ppo_m51_margin_retention_seed2151/checkpoints/checkpoint_step_126976.pt \
  --checkpoint-policy m51_151=runs/ppo_m51_margin_retention_seed2151/checkpoints/checkpoint_step_151552.pt \
  --checkpoint-policy m51_176=runs/ppo_m51_margin_retention_seed2151/checkpoints/checkpoint_step_176128.pt \
  --checkpoint-policy m51_200=runs/ppo_m51_margin_retention_seed2151/checkpoints/checkpoint_step_200000.pt \
  --device cpu \
  --run-dir runs/m52_m38_margin_benchmark_seed4300
```

Broad and fresh benchmarks use the same policy set:

- `runs/m52_broad_margin_benchmark_seed3000`;
- `runs/m52_fresh_margin_benchmark_seed5200`.

Margin corpus:

```bash
conda run -n autodrift python -m autodrift.margin_critical_corpus \
  --episodes-csv runs/m52_m38_margin_benchmark_seed4300/episodes.csv \
  --episodes-csv runs/m52_broad_margin_benchmark_seed3000/episodes.csv \
  --episodes-csv runs/m52_fresh_margin_benchmark_seed5200/episodes.csv \
  --baseline-policy m37_102 \
  --candidate-policy m51_028 \
  --candidate-policy m51_053 \
  --candidate-policy m51_077 \
  --candidate-policy m51_102 \
  --candidate-policy m51_126 \
  --candidate-policy m51_151 \
  --candidate-policy m51_176 \
  --candidate-policy m51_200 \
  --near-margin 0.05 \
  --min-abs-margin-delta 0.02 \
  --top-k 120 \
  --run-dir runs/m52_margin_critical_corpus
```

Strict gate:

```bash
conda run -n autodrift python -m autodrift.margin_retention_gate \
  --seed-delta-csv runs/m52_margin_critical_corpus/seed_margin_deltas.csv \
  --min-success-delta 0.0 \
  --max-binary-regressed-seeds 0 \
  --max-near-margin-regressed-seeds 0 \
  --min-margin-delta-mean 0.0 \
  --run-dir runs/m52_margin_retention_gate_strict
```

## Checkpoint Sweep

Strict gate summary versus `m37_102`:

| Candidate | Passed | Success delta | Binary regressions | Near-margin regressions | Margin delta mean |
| --- | --- | ---: | ---: | ---: | ---: |
| m51_028 | false | -0.01875 | 3 | 10 | -0.015016 |
| m51_053 | false | -0.02500 | 4 | 21 | -0.038968 |
| m51_077 | false | -0.02500 | 4 | 24 | -0.046410 |
| m51_102 | false | -0.03125 | 5 | 28 | -0.052912 |
| m51_126 | false | -0.02500 | 4 | 23 | -0.042541 |
| m51_151 | false | -0.02500 | 4 | 23 | -0.040641 |
| m51_176 | false | -0.02500 | 4 | 20 | -0.041229 |
| m51_200 | false | -0.02500 | 4 | 19 | -0.043070 |

Best snapshot by strict-gate damage is `m51_028`, but it still fails all
promotion checks.

M38 success:

| Policy | Success | Margin mean |
| --- | ---: | ---: |
| m37_102 | 0.6250 | 0.283562 |
| m51_028 | 0.6000 | 0.269437 |
| m51_053 | 0.5875 | 0.255787 |
| m51_077 | 0.5875 | 0.248985 |
| m51_102 | 0.5875 | 0.244520 |
| m51_126 | 0.5875 | 0.253071 |
| m51_151 | 0.5875 | 0.255747 |
| m51_176 | 0.5875 | 0.257972 |
| m51_200 | 0.5875 | 0.256948 |

Broad success:

| Policy | Success | Margin mean |
| --- | ---: | ---: |
| m37_102 | 0.8250 | 1.398739 |
| m51_028 | 0.8000 | 1.388842 |
| m51_053 | 0.8000 | 1.360290 |
| m51_077 | 0.8000 | 1.352828 |
| m51_102 | 0.7750 | 1.349159 |
| m51_126 | 0.8000 | 1.356667 |
| m51_151 | 0.8000 | 1.357504 |
| m51_176 | 0.8000 | 1.354054 |
| m51_200 | 0.8000 | 1.352439 |

Fresh seed 5200 success stays at `0.8250` for all M51 snapshots, but mean
margin is lower than M37 for all snapshots.

## Diagnosis

M51 oversampled the M50 top-100 corpus with 70% seed mixing. That corpus has:

- 100 selected rows;
- only 41 unique seeds;
- 62 rows from the M38 source;
- repeated rows for the same seed because each policy comparison contributes a
  candidate row.

The training signal therefore overweights a small near-boundary set and appears
to push the policy away from the broader M37 behavior. The result is the
opposite of the intended retention objective:

- M38 success drops from `0.6250` to at best `0.6000`;
- broad success drops from `0.8250` to at best `0.8000`;
- mean margin drops on every combined sweep candidate;
- strict gate rejects every checkpoint.

## Conclusion

M52 is a negative result. Full M51 continuation is trainable, but direct
high-probability replay of the row-level M50 corpus damages aggregate success
and near-boundary margin retention. No checkpoint is promotable. Current best
remains `m37_102`.

## Next Step

M53 should change the data mixture before another long run:

- deduplicate the M50 corpus into a seed-level training sequence;
- reduce hard-seed mix probability;
- keep broad randomized retention dominant;
- optionally stratify by source so M38 does not dominate fresh/broad cases;
- rerun a short training smoke before any full continuation.
