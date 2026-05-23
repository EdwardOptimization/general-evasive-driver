# M398 Old-Key Normal-Margin Recovery Target Export

M398 exports replay-selected local recovery targets for the current old-key
normal-branch terminal-margin cliff after M395. It does not run PPO, promote a
checkpoint, lower thresholds, or change actor inputs.

## Source

Current public-gate base:

```text
runs/m394_s02_micro_interpolation/checkpoints/alpha_0_1.pt
```

Source rows:

```text
runs/m398_old_key_normal_margin_source_rows/old_key_normal_margin_source_rows.csv
```

The source contains the alpha `0.2` active row `9958|perturbed|39|36` and the
alpha `0.4` accepted-regression sibling `10004|perturbed|31|31`. The alpha
`0.4` row `10033|perturbed|29|23` is recorded as a gap monitor row but is not a
normal-branch failure, so it is not included in this recovery target export.

## Export

Command family:

```text
PYTHONPATH=src python -m autodrift.old_key_recovery_targets \
  --checkpoint runs/m394_s02_micro_interpolation/checkpoints/alpha_0_1.pt \
  --reference-manifest runs/m341_old_key_neighborhood_block_a_seed9860/manifest.json \
  --source-rows-csv runs/m398_old_key_normal_margin_source_rows/old_key_normal_margin_source_rows.csv \
  --steer-deltas=-0.08,-0.06,-0.04,-0.02,-0.01,0,0.01,0.02,0.04,0.06,0.08 \
  --throttle-deltas=-0.06,-0.04,-0.02,0,0.02,0.04 \
  --brake-deltas=-0.08,-0.06,-0.04,-0.02,0,0.02,0.04,0.06,0.08 \
  --min-margin-improvement 1e-5 \
  --max-action-l2 0.11 \
  --max-continuation-steps 40 \
  --device cpu \
  --run-dir runs/m398_old_key_normal_margin_recovery_targets
```

Result:

```text
rows_requested: 2
candidate_rollouts: 1188
recovery_rows: 2
accepted_recovery_rows: 2
base_retention_rows: 0
skipped_rows: 0
accepted_margin_improvement_min: 0.001218930
accepted_margin_improvement_mean: 0.001788393
accepted_margin_improvement_max: 0.002357856
candidate_margin_improvement_max: 0.002551019
```

Targets:

| Case | Baseline margin | Selected margin | Improvement | Action L2 |
| --- | ---: | ---: | ---: | ---: |
| 9958\|perturbed\|39\|36\|9.500000\|-1.200000\|0.900000 | 0.000086 | 0.002443 | 0.002358 | 0.107703 |
| 10004\|perturbed\|31\|31\|9.500000\|-1.000000\|0.800000 | 0.000145 | 0.001364 | 0.001219 | 0.107703 |

Both selected recovery actions reduce steer by `0.04`, reduce throttle by
`0.06`, and increase brake by `0.08` relative to the current base action. This
is a training-only local recovery target; closed-loop old-key replay remains
the outer proof gate.

Artifacts:

```text
runs/m398_old_key_normal_margin_recovery_targets/old_key_recovery_corpus.npz
runs/m398_old_key_normal_margin_recovery_targets/old_key_recovery_targets.csv
runs/m398_old_key_normal_margin_recovery_targets/recovery_candidates.csv
runs/m398_old_key_normal_margin_recovery_targets/skipped_rows.csv
```

## No-Update Smoke

The exported corpus loads through the current exact repair stack:

```text
runs/m398_old_key_normal_margin_recovery_no_update_smoke/summary.json
```

Key values:

```text
old_key_recovery_rows: 2
old_key_recovery_loss: 0.003866661
old_key_recovery_preferred_loss: 0.003866661
old_key_recovery_wrong_anchor_loss: 0.000000000
exact_m297_delta_vs_base: 0.0
exact_m270_delta_vs_base: 0.0
old_key_surrogate_delta_vs_base: 0.0
exact_lexicographic_pass: true
```

## Tests

Focused tests:

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
  python -m pytest -q tests/test_old_key_recovery_targets.py \
  tests/test_exact_post_ppo_repair.py
```

Result:

```text
15 passed
```

## Decision

M398 completes the target export. The next step should run a no-PPO exact
repair/interpolation probe using the refreshed normal-margin recovery corpus,
while retaining the M393 current-family conflict residual and keeping old-key
closed-loop replay as the authoritative proof gate.

Admit:

```text
m399-old-key-normal-margin-recovery-repair-probe
```
