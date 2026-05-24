# M624 Longer Low-Amplitude Sequence Miner

## Purpose

M624 runs the no-training K=3/5/7 sequence diagnostic designed by M623.

Question:

```text
Does adding K=7 and intermediate low-amplitude steer deltas recover additional
source-diverse accepted sequences?
```

Answer:

```text
No. It increases candidate-level acceptance and selected margin improvement on
the same source rows, but source-level accepted diversity does not improve.
```

Scope:

```text
no actor training
no PPO
no checkpoint promotion
no optimizer admission
no target threshold change
no trust-region change
```

## Command

Executed:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.sequence_target_miner \
  --checkpoint-policy bc5660=runs/m568_scaled_l3_bc_seed5660/checkpoint.pt \
  --boundary-source-rows runs/m616_expanded_sequence_source_miner/expanded_sequence_source_rows.csv \
  --surface-config fresh=configs/ppo_m541_matched_l3_variance_4096.json \
  --surface-config ood=configs/eval_m574_moderate_ood_l3.json \
  --sequence-lengths 3,5,7 \
  --family constant_delta \
  --family decay_pulse \
  --family brake_release_then_steer \
  --family steer_then_brake \
  --steer-deltas=-0.08,-0.06,-0.04,0,0.04,0.06,0.08 \
  --throttle-deltas=-0.06,0,0.03 \
  --brake-deltas=-0.08,-0.04,0,0.04,0.08 \
  --per-step-action-l2 0.10 \
  --sequence-mean-l2-limit 0.08 \
  --sequence-max-l2-limit 0.10 \
  --max-delta-delta-l2-limit 0.08 \
  --min-margin-improvement 0.02 \
  --min-risk-improvement 0.05 \
  --max-continuation-steps 80 \
  --device cpu \
  --run-dir runs/m624_longer_low_amplitude_sequence_miner
```

## Results

Artifacts:

```text
runs/m624_longer_low_amplitude_sequence_miner/summary.json
runs/m624_longer_low_amplitude_sequence_miner/sequence_candidates.csv
runs/m624_longer_low_amplitude_sequence_miner/accepted_candidate_sequences.csv
runs/m624_longer_low_amplitude_sequence_miner/accepted_sequences.csv
runs/m624_longer_low_amplitude_sequence_miner/unaccepted_rows.csv
runs/m624_longer_low_amplitude_sequence_miner/sequence_target_corpus.npz
```

Comparison to M621:

| Metric | M621 K=3/5 | M624 K=3/5/7 |
| --- | ---: | ---: |
| source rows | `30` | `30` |
| candidate rollouts | `10440` | `22140` |
| accepted candidate sequences | `189` | `607` |
| selected accepted sequences | `6` | `6` |
| unaccepted rows | `24` | `24` |
| selected physical pairs | `5` | `5` |
| selected left seeds | `4` | `4` |
| accepted candidate physical pairs | `5` | `5` |
| accepted candidate left seeds | `4` | `4` |
| selected margin improvement mean | `0.056784` | `0.068523` |
| selected margin improvement max | `0.093048` | `0.121356` |
| best unaccepted improvement | `0.025914` | `0.030757` |

M624 improves candidate count and selected margin on already-accepted rows, but
does not add source-level accepted breadth.

## Accepted Candidates

Accepted candidate counts:

| Dimension | M624 Counts |
| --- | --- |
| family | decay_pulse `281`, constant_delta `192`, steer_then_brake `84`, brake_release_then_steer `50` |
| tier | support_boundary `304`, near_boundary `300`, core_boundary `3` |
| sequence length | K=7 `239`, K=5 `213`, K=3 `155` |

K=7 is useful at candidate level:

```text
K=7 accepted candidate rows: 239
```

But these candidates remain concentrated on the same accepted source rows:

```text
accepted candidate physical pairs: 5
accepted candidate left seeds: 4
```

## Selected Accepted Rows

All selected accepted rows remain the same six source indices:

```text
5, 7, 13, 14, 20, 32
```

M624 changes the best selected sequence length for most of them:

| Source | Tier | M621 Best | M624 Best | M624 Margin Improvement |
| ---: | --- | --- | --- | ---: |
| `5` | near_boundary | K=5 | K=7 | `0.036655` |
| `7` | core_boundary | K=5 | K=5 | `0.020817` |
| `13` | support_boundary | K=5 | K=7 | `0.121356` |
| `14` | support_boundary | K=5 | K=7 | `0.121356` |
| `20` | near_boundary | K=5 | K=7 | `0.055476` |
| `32` | near_boundary | K=5 | K=7 | `0.055476` |

The selected family remains narrow:

```text
accepted_sequence_counts_by_family:
  constant_delta: 6
```

## Remaining Near Misses

Top unaccepted rows:

| Source | Tier | Best Length | Best Improvement | Rejection |
| ---: | --- | ---: | ---: | --- |
| `30` | support_boundary | `7` | `0.030757` | outside_sequence_trust_region |
| `1` | core_boundary | `3` | `0.025914` | outside_sequence_trust_region |
| `0` | support_boundary | `7` | `0.023657` | outside_sequence_trust_region |
| `8` | core_boundary | `7` | `0.022960` | outside_sequence_trust_region |
| `2` | core_boundary | `7` | `0.021347` | outside_sequence_trust_region |
| `15` | core_boundary | `5` | `0.021143` | candidate_collision |
| `21` | core_boundary | `7` | `0.020580` | outside_sequence_trust_region |

Many near misses exceed the margin threshold but remain outside the pre-
registered sequence trust region. M624 confirms that simply adding K=7 is not
enough to convert these source rows under the current trust metrics.

## Interpretation

M624 is a useful diagnostic negative for source diversity:

```text
candidate-level count improved
selected margin improved
source-level accepted diversity did not improve
```

Do not train from this corpus. Do not claim optimizer admission.

The next audit should decide whether to:

```text
1. inspect near-miss trust-region geometry;
2. design source-conditioned lower-amplitude candidates around near-miss rows;
3. expand source mining again;
4. or pause sequence-target mining and return to capability/action coupling.
```

## Contract Checks

```text
diagnostic_only: true
labels_enter_actor_input: false
actor_parameters_changed: false
ppo_used: false
promoted: false
optimizer_admission: false
target_acceptance_thresholds_changed: false
trust_regions_changed: false
```

## Decision

Decision:

```text
longer_low_amplitude_sequence_miner_diagnostic_negative_admit_audit
```

Next blocker:

```text
m625-longer-low-amplitude-sequence-audit
```
