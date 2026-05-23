# M346 Old-Key Neighborhood Alpha Sweep Design

M346 designs the next no-PPO alpha sweep. It does not run replay, train, repair,
promote, or change actor inputs.

## Question

M335 accepted only `alpha=0.0075` because the old singleton `9944` gap floor
was the active bottleneck. M341-M345 replaced that singleton-dominant evidence
with a source-diverse old-key neighborhood surface and a replayable
candidate-level adapter.

The next question is:

```text
Does the distributional old-key neighborhood gate allow a larger safe movement
along the M335 repaired direction than the old singleton 9944 floor allowed?
```

This must be answered before any more PPO.

## Inputs

Interpolation family:

```text
runs/m335_m333_to_repaired_gap_bounded_interpolation/checkpoints/
```

Available alphas:

| Label | Alpha | Checkpoint |
| --- | ---: | --- |
| m335_a0_0075 | 0.0075 | `alpha_0_0075.pt` |
| m335_a010 | 0.01 | `alpha_0_01.pt` |
| m335_a020 | 0.02 | `alpha_0_02.pt` |
| m335_a050 | 0.05 | `alpha_0_05.pt` |
| m335_a100 | 0.10 | `alpha_0_1.pt` |
| m335_a200 | 0.20 | `alpha_0_2.pt` |
| m335_a1000 | 1.0 | `alpha_1.pt` |

Use `m335_a0_0075` as the baseline for candidate comparison because it is the
current promoted public-gate base from M336.

Use the M341 compact corpus:

```text
runs/m341_old_key_neighborhood_mining/old_key_neighborhood_compact_corpus.csv
```

Keep M133 / `9944` diagnostic visibility from:

```text
runs/m341_old_key_neighborhood_mining/old_key_neighborhood_candidate_pool.csv
```

## Exact Compact Replay Cases

`critical_key_replay_guard` can replay protected cases from reference case CSVs.
The M341 compact corpus is already exact but is not in that reference-case
format. M347 should first export an exact synthetic reference-case CSV from the
M341 compact rows.

Each compact row should become one reference row:

```text
seed
target_obstacle_distance
relocated_obstacle_body_y
relocated_obstacle_half_width
nominal_step
perturbed_step
nominal_accepted_outcome_sensitive
perturbed_accepted_outcome_sensitive
<source>_normal_margin
<source>_wrong_history_margin
<source>_margin_gap
```

Only the compact row's `source_condition` should be marked accepted. This avoids
the looser `--case-key` behavior, which can pull additional relocation buckets
for the same key.

Suggested output:

```text
runs/m347_old_key_alpha_sweep/compact_reference_cases.csv
```

## Replay Command Shape

Use any M341 block manifest with the same mining settings. The block-A manifest
is sufficient because `critical_key_replay_guard` takes protected seeds from the
reference cases:

```bash
PYTHONPATH=src python -m autodrift.critical_key_replay_guard \
  --reference-manifest runs/m341_old_key_neighborhood_block_a_seed9860/manifest.json \
  --reference-cases-csv runs/m347_old_key_alpha_sweep/compact_reference_cases.csv \
  --checkpoint-policy m335_a0_0075=runs/m335_m333_to_repaired_gap_bounded_interpolation/checkpoints/alpha_0_0075.pt \
  --checkpoint-policy m335_a010=runs/m335_m333_to_repaired_gap_bounded_interpolation/checkpoints/alpha_0_01.pt \
  --checkpoint-policy m335_a020=runs/m335_m333_to_repaired_gap_bounded_interpolation/checkpoints/alpha_0_02.pt \
  --checkpoint-policy m335_a050=runs/m335_m333_to_repaired_gap_bounded_interpolation/checkpoints/alpha_0_05.pt \
  --checkpoint-policy m335_a100=runs/m335_m333_to_repaired_gap_bounded_interpolation/checkpoints/alpha_0_1.pt \
  --checkpoint-policy m335_a200=runs/m335_m333_to_repaired_gap_bounded_interpolation/checkpoints/alpha_0_2.pt \
  --checkpoint-policy m335_a1000=runs/m335_m333_to_repaired_gap_bounded_interpolation/checkpoints/alpha_1.pt \
  --reference-policy m335_a0_0075 \
  --device cpu \
  --run-dir runs/m347_old_key_alpha_sweep/replay
```

If runtime is high, split this into two batches:

```text
near: 0.0075, 0.01, 0.02, 0.05
far:  0.10, 0.20, 1.0
```

Do not change thresholds based on early results.

## Candidate Gate Commands

For each candidate policy, run:

```bash
PYTHONPATH=src python -m autodrift.old_key_neighborhood_replay_gate \
  --compact-corpus-csv runs/m341_old_key_neighborhood_mining/old_key_neighborhood_compact_corpus.csv \
  --guard-results-csv runs/m347_old_key_alpha_sweep/replay/guard_results.csv \
  --candidate-pool-csv runs/m341_old_key_neighborhood_mining/old_key_neighborhood_candidate_pool.csv \
  --baseline-policy m335_a0_0075 \
  --candidate-policy <candidate_label> \
  --run-dir runs/m347_old_key_alpha_sweep/gates/<candidate_label>
```

The sweep summary should aggregate:

```text
candidate_gate_pass
candidate_accepted_regressions
candidate_normal_success_regressions
candidate_gap_p10
candidate_gap_min
candidate_repair_needed
failure_types
```

## Thresholds

Keep the M344 thresholds:

```text
candidate accepted regressions == 0
candidate gap p10 >= -0.0005
candidate gap min >= -0.002
compact diversity pass
M133 / 9944 diagnostic visible
```

Repair-needed diagnostic:

```text
candidate accepted regressions >= 2
or candidate gap p10 <= -0.001
or candidate gap min <= -0.01
```

## Gate Order

M347 is only an old-key alpha sweep. It can identify a candidate for further
checks, but cannot promote.

If a larger alpha passes the replayable old-key gate, the next milestone must
run:

```text
1. exact M297 / M270 no-regression
2. source-diverse protected gate
3. first replay gates
4. then full public gate only if the first gates pass
```

If all alphas above `0.0075` fail:

```text
classification: distributional_old_key_bottleneck
next action: repair objective or trust-region design, not more PPO
```

If the repaired endpoint or very large alpha passes unexpectedly:

```text
classification: metric_artifact
next action: audit old-key replay adapter before trusting the gate
```

## Acceptance Decision

M347 should report:

```text
largest_old_key_passing_alpha
first_failing_alpha
failure classification for each candidate
whether distributional gate is less restrictive than singleton 9944 floor
```

Possible outcomes:

| Outcome | Decision |
| --- | --- |
| alpha > 0.0075 passes | admit exact/source-diverse/first-replay probe for largest passing alpha |
| only 0.0075 passes | keep M336 base; classify distributional old-key bottleneck |
| repaired endpoint passes | reject gate as metric artifact and audit adapter |
| replay cannot reproduce 0.0075 | classify lineage invalid; stop before PPO |

## Decision

M346 admits a no-PPO run milestone:

```text
admit_m347_old_key_neighborhood_alpha_sweep_run
```
