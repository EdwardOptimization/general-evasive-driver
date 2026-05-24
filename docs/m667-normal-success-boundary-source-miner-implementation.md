# M667 Normal-Success Boundary Source Miner Implementation

## Purpose

M667 implements the M666 normal-success near-boundary source miner. It tests
whether filtering left snapshots by valid normal-history preferred branches
before wrong-history pairing can produce usable action/outcome-critical
wrong-history rows.

This milestone is diagnostic infrastructure only:

```text
no actor update
no optimizer
no PPO
no checkpoint promotion
```

## Implementation

Added:

```text
src/autodrift/normal_success_boundary_source_miner.py
tests/test_normal_success_boundary_source_miner.py
```

The miner:

1. Builds a wider obstacle decision-window snapshot bank.
2. Runs a normal-history prepass for each source snapshot.
3. Classifies windows into:

```text
near_boundary_preferred
early_safe_diagnostic
already_failed_diagnostic
```

4. Pairs wrong histories only for `near_boundary_preferred` left snapshots.
5. Applies the same action/outcome thresholds as M664.
6. Writes explicit preferred/rejected sequence corpus fields.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.normal_success_boundary_source_miner \
  --checkpoint runs/m568_scaled_l3_bc_seed5660/checkpoint.pt \
  --surface-config fresh=configs/ppo_m541_matched_l3_variance_4096.json \
  --surface-config ood=configs/eval_m574_moderate_ood_l3.json \
  --surface-seed-range fresh=25560:25619 \
  --surface-seed-range ood=25660:25719 \
  --sequence-lengths 5,7,9 \
  --obstacle-distance-min 0.0 \
  --obstacle-distance-max 35.0 \
  --normal-margin-min 0.0 \
  --normal-margin-max 1.0 \
  --max-right-candidates-per-left 64 \
  --max-candidate-pairs-per-surface 1600 \
  --context-distance-threshold 0.25 \
  --response-distance-threshold 0.20 \
  --obstacle-x-abs-delta 10.0 \
  --obstacle-y-abs-delta 2.0 \
  --step-abs-delta 30 \
  --min-wrong-first-action-l2 0.002 \
  --min-wrong-action-sequence-mean-l2 0.006 \
  --min-preferred-rejected-action-mean-l2 0.010 \
  --min-margin-gap 0.010 \
  --device cpu \
  --run-dir runs/m667_normal_success_boundary_source_miner
```

## Artifacts

```text
runs/m667_normal_success_boundary_source_miner/summary.json
runs/m667_normal_success_boundary_source_miner/snapshot_bank_summary.csv
runs/m667_normal_success_boundary_source_miner/normal_window_summary.csv
runs/m667_normal_success_boundary_source_miner/normal_window_rows.csv
runs/m667_normal_success_boundary_source_miner/candidate_scores.csv
runs/m667_normal_success_boundary_source_miner/normal_success_boundary_rows.csv
runs/m667_normal_success_boundary_source_miner/normal_success_boundary_corpus.npz
runs/m667_normal_success_boundary_source_miner/source_summary.csv
runs/m667_normal_success_boundary_source_miner/split_summary.csv
runs/m667_normal_success_boundary_source_miner/target_summary.csv
```

The empty accepted NPZ has the expected explicit sequence shapes:

```text
observation:                 (0, 72)
normal_hidden:               (0, 64)
variant_hidden:              (0, 64)
preferred_action_sequence:   (0, 9, 3)
rejected_action_sequence:    (0, 9, 3)
target_action_sequence:      (0, 9, 3)
sequence_mask:               (0, 9)
variant_base_action:         (0, 3)
```

## Normal Window Result

M667 confirms that normal-success near-boundary preferred windows do exist:

```text
snapshot_count:                     644
near_boundary_preferred_snapshots:  204
early_safe_diagnostic:              296
already_failed_diagnostic:          144
```

By surface:

```text
fresh near_boundary_preferred: 108 rows, 38 seeds, 3 targets
ood near_boundary_preferred:    96 rows, 34 seeds, 2 targets
```

Near-boundary margin statistics:

```text
mean normal_margin: 0.520157
min normal_margin:  0.000474
max normal_margin:  0.997193
```

So M667 is not blocked by missing normal-success source windows.

## Candidate Result

M667 scored `3200` candidate pairs and `9600` sequence rows:

```text
candidate_pairs: 3200
candidate_rows:  9600
accepted_rows:      0
corpus_passed:  false
```

The normal/wrong branches both succeed:

```text
candidate_normal_success_rate: 1.000
candidate_wrong_success_rate:  1.000
success_drop_rate:             0.000
```

Action and margin thresholds:

```text
wrong_first_action_l2 >= 0.002 rows:       8934
wrong_action_sequence_mean_l2 >= 0.006:       4
preferred/rejected mean_l2 >= 0.010:          0
margin_gap >= 0.010:                          0
all action thresholds:                        0
```

Maximum observed values:

```text
max wrong_first_action_l2:                 0.015159
max wrong_action_sequence_mean_l2:         0.006325
max preferred_vs_rejected_action_mean_l2:  0.006325
max margin_gap:                            0.000034
```

Actor checksum was unchanged:

```text
d9f636b495426c606140d15ddc207243979e87f1effbd89deb2946ae7c874c88
```

No actor checkpoint was written.

## Interpretation

M667 rules out one major failure mode:

```text
No near-boundary normal-success windows.
```

That is false. The miner found `204` valid preferred windows.

The current blocker is:

```text
near_boundary_exists_but_wrong_history_has_no_outcome_effect
```

Wrong history changes the first action often, but the change is not sustained
enough over the short horizon and does not affect margin or success. The
BC5660 actor is still too insensitive at the action/outcome boundary for these
compatible wrong-history substitutions.

## Decision

```text
normal_success_boundary_source_miner_negative_admit_audit
```

Do not train from the empty corpus. Do not lower the preferred-vs-rejected or
margin thresholds. The next audit should decide whether to extend outcome
horizon/window sharpness or move to representation/action-boundary design.

## Next

```text
m668-normal-success-boundary-source-miner-audit
```
