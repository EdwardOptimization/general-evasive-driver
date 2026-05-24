# M661 Action-Divergent Wrong-History Corpus Implementation

## Purpose

M661 implements and runs the no-training action-divergent wrong-history corpus
miner designed in M660. The goal was to stop treating hidden-distance-only rows
as sufficient self-ID supervision and require explicit preferred/rejected action
sequence evidence.

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
src/autodrift/action_divergent_wrong_history_corpus.py
tests/test_action_divergent_wrong_history_corpus.py
```

The CLI loads matched-current fresh/OOD surfaces, reconstructs requested normal
and wrong-history snapshots, rolls out the BC5660 policy under normal history
and wrong matched history, and writes:

```text
runs/m661_action_divergent_wrong_history_corpus/summary.json
runs/m661_action_divergent_wrong_history_corpus/candidate_scores.csv
runs/m661_action_divergent_wrong_history_corpus/action_divergent_rows.csv
runs/m661_action_divergent_wrong_history_corpus/action_divergent_corpus.npz
runs/m661_action_divergent_wrong_history_corpus/source_summary.csv
runs/m661_action_divergent_wrong_history_corpus/split_summary.csv
runs/m661_action_divergent_wrong_history_corpus/target_summary.csv
```

The NPZ writer includes explicit preferred and rejected sequence arrays even
when no accepted rows are found. In this first implementation the preferred
sequence is the normal-policy rollout and the rejected sequence is the
wrong-history rollout. M636 projected sequence matches are recorded as
diagnostics; they are not used to weaken the M661 thresholds.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.action_divergent_wrong_history_corpus \
  --checkpoint runs/m568_scaled_l3_bc_seed5660/checkpoint.pt \
  --surface-pairs fresh=runs/m586_bc5660_matched_current_fresh_seed25560/matched_pairs.csv \
  --surface-pairs ood=runs/m586_bc5660_matched_current_ood_seed25660/matched_pairs.csv \
  --surface-config fresh=configs/ppo_m541_matched_l3_variance_4096.json \
  --surface-config ood=configs/eval_m574_moderate_ood_l3.json \
  --preferred-sequences runs/m636_combined_source7_preserving_shape/accepted_combined_sequences.csv \
  --sequence-lengths 5,7,9 \
  --min-wrong-first-action-l2 0.002 \
  --min-wrong-action-sequence-mean-l2 0.006 \
  --min-preferred-rejected-action-mean-l2 0.010 \
  --min-margin-gap 0.010 \
  --device cpu \
  --run-dir runs/m661_action_divergent_wrong_history_corpus
```

## Result

M661 is a clean negative result:

```text
candidate_rows:                                      3207
accepted_rows:                                       0
corpus_passed:                                       false
candidate_wrong_first_action_threshold_rows:         75
candidate_wrong_sequence_threshold_rows:             0
candidate_preferred_rejected_threshold_rows:         0
candidate_margin_threshold_rows:                     0
candidate_all_action_threshold_rows:                 0
candidate_all_action_and_margin_threshold_rows:       0
```

The strongest candidates were still far below the short-horizon action and
margin thresholds:

```text
max wrong_first_action_l2:                 0.004301
max wrong_action_sequence_mean_l2:         0.001850
max preferred_vs_rejected_action_mean_l2:  0.001850
max margin_gap:                            0.000031
normal_success_rate:                       1.000
wrong_success_rate:                        1.000
```

Actor checksum was unchanged:

```text
d9f636b495426c606140d15ddc207243979e87f1effbd89deb2946ae7c874c88
```

No actor checkpoint was written.

## Interpretation

M661 did not fail because the writer omitted rejected-history fields or because
the actor was modified. The corpus artifact exists and has the expected empty
shapes. The failure is evidence-bearing:

```text
BC5660 + M586/M636 matched-current surfaces do not provide enough
wrong-history action divergence or margin divergence for a usable
action-divergent wrong-history corpus.
```

This agrees with the previous evidence line:

- M655 showed wrong-history signal exists in raw/next hidden state but is weak
  at fused actor features and actions.
- M658 showed next-hidden views improve relative signal but remain below
  absolute wrong-history thresholds.
- M661 now shows that the existing matched-current surfaces do not create
  distinct wrong-history action sequences or outcome gaps.

## Decision

```text
action_divergent_wrong_history_corpus_negative_admit_audit
```

Do not weaken the M661 thresholds inside the same gate and call the result
positive. The next step must audit the negative result and then design a source
mining branch that searches for genuinely action-critical wrong-history pairs,
not merely hidden-different pairs.

## Next

```text
m662-action-divergent-wrong-history-corpus-audit
```
