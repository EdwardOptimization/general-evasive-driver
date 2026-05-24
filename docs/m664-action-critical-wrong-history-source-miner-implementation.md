# M664 Action-Critical Wrong-History Source Miner Implementation

## Purpose

M664 implements the M663 no-training action-critical wrong-history source miner.
It tests whether broader action/outcome-first source mining can find
wrong-history rows that M661 missed.

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
src/autodrift/action_critical_wrong_history_source_miner.py
tests/test_action_critical_wrong_history_source_miner.py
```

The miner:

1. Builds a BC5660 snapshot bank from fresh and OOD surfaces.
2. Uses human-view scene geometry plus ego-response compatibility filters.
3. Ranks compatible wrong histories by hidden distance but does not accept by
   hidden distance alone.
4. Replays normal and wrong-history branches.
5. Accepts only rows that pass action-sequence thresholds and success/margin
   sensitivity thresholds.
6. Writes explicit preferred/rejected sequence corpus fields.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.action_critical_wrong_history_source_miner \
  --checkpoint runs/m568_scaled_l3_bc_seed5660/checkpoint.pt \
  --surface-config fresh=configs/ppo_m541_matched_l3_variance_4096.json \
  --surface-config ood=configs/eval_m574_moderate_ood_l3.json \
  --surface-seed-range fresh=25560:25619 \
  --surface-seed-range ood=25660:25719 \
  --sequence-lengths 5,7,9 \
  --max-right-candidates-per-left 64 \
  --max-candidate-pairs-per-surface 1200 \
  --context-distance-threshold 0.25 \
  --response-distance-threshold 0.20 \
  --obstacle-x-abs-delta 8.0 \
  --obstacle-y-abs-delta 1.5 \
  --step-abs-delta 20 \
  --min-wrong-first-action-l2 0.002 \
  --min-wrong-action-sequence-mean-l2 0.006 \
  --min-preferred-rejected-action-mean-l2 0.010 \
  --min-margin-gap 0.010 \
  --device cpu \
  --run-dir runs/m664_action_critical_wrong_history_source_miner
```

## Artifacts

```text
runs/m664_action_critical_wrong_history_source_miner/summary.json
runs/m664_action_critical_wrong_history_source_miner/snapshot_bank_summary.csv
runs/m664_action_critical_wrong_history_source_miner/candidate_scores.csv
runs/m664_action_critical_wrong_history_source_miner/action_critical_rows.csv
runs/m664_action_critical_wrong_history_source_miner/action_critical_corpus.npz
runs/m664_action_critical_wrong_history_source_miner/source_summary.csv
runs/m664_action_critical_wrong_history_source_miner/split_summary.csv
runs/m664_action_critical_wrong_history_source_miner/target_summary.csv
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

## Result

M664 is negative:

```text
snapshot_count:                         473
fresh snapshots:                        240
ood snapshots:                          233
candidate_pairs:                       2400
candidate_rows:                        7200
accepted_rows:                            0
corpus_passed:                         false
```

Compared with M661, the broader source miner did find larger action gaps:

```text
max wrong_first_action_l2:                 0.013062
max wrong_action_sequence_mean_l2:         0.010464
max preferred_vs_rejected_action_mean_l2:  0.010464
wrong_first_action_l2 >= 0.002 rows:       5352
wrong_action_sequence_mean_l2 >= 0.006:      60
preferred/rejected mean_l2 >= 0.010:          3
all action thresholds:                       3
```

But it still found no usable action-critical rows:

```text
margin_gap >= 0.010 rows:      0
success_drop_rate:             0.000
normal_success_rate:           0.610
wrong_success_rate:            0.610
max margin_gap:                0.000039
```

The only rows that crossed all action thresholds were already failed under the
normal-history branch:

```text
normal_margin: negative
wrong_margin: approximately unchanged
normal_success: false
wrong_success: false
success_drop: false
```

Actor checksum was unchanged:

```text
d9f636b495426c606140d15ddc207243979e87f1effbd89deb2946ae7c874c88
```

No actor checkpoint was written.

## Interpretation

M664 improves the diagnosis relative to M661:

```text
M661: existing matched-current surfaces do not produce action divergence.
M664: broader source mining can produce action divergence, but the strongest
      action-divergent wrong-history rows occur in already-failed normal states
      and do not create wrong-history-specific outcome degradation.
```

So the blocker is not only weak hidden-to-action coupling. It is also source
window quality:

```text
action-sensitive rows are too late / too failed;
normal-success near-boundary decision windows are not yet isolated.
```

## Decision

```text
action_critical_wrong_history_source_miner_negative_admit_audit
```

Do not train from the empty corpus. Do not weaken the outcome threshold. The
next step should audit whether M664 needs a normal-success / near-boundary
decision-window source filter before another mining implementation.

## Next

```text
m665-action-critical-source-miner-audit
```
