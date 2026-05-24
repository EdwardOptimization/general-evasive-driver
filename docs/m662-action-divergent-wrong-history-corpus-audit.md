# M662 Action-Divergent Wrong-History Corpus Audit

## Purpose

M662 audits the negative M661 corpus-mining result before any new objective,
actor coupling, or PPO step. The question is whether M661 failed because the
implementation was broken or because the current M586/M636 matched-current
surfaces are not actually action-divergent under BC5660 wrong-history replay.

## M661 Evidence

M661 wrote all required artifacts:

```text
runs/m661_action_divergent_wrong_history_corpus/summary.json
runs/m661_action_divergent_wrong_history_corpus/candidate_scores.csv
runs/m661_action_divergent_wrong_history_corpus/action_divergent_corpus.npz
runs/m661_action_divergent_wrong_history_corpus/action_divergent_rows.csv
```

The NPZ is empty by accepted-row count but has valid shapes and explicit
preferred/rejected sequence fields:

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

Actor checksum was unchanged and no checkpoint was written:

```text
d9f636b495426c606140d15ddc207243979e87f1effbd89deb2946ae7c874c88
```

## Threshold Audit

M661 evaluated `3207` candidate rows across fresh and OOD surfaces:

```text
fresh candidates: 1998
ood candidates:   1209
targets:
  future_yaw_response:            1698
  future_braking_deceleration:    1101
  future_lateral_accel_response:   408
```

No candidate reached the full action-divergent gate:

```text
accepted_rows:                                  0
wrong_first_action_l2 >= 0.002:                75
wrong_action_sequence_mean_l2 >= 0.006:         0
preferred_vs_rejected_action_mean_l2 >= 0.010:  0
margin_gap >= 0.010:                            0
all action thresholds:                          0
all action + margin thresholds:                 0
```

Maximum observed values were far below the intended scale:

```text
max wrong_first_action_l2:                 0.004301
max wrong_action_sequence_mean_l2:         0.001850
max preferred_vs_rejected_action_mean_l2:  0.001850
max margin_gap:                            0.000031
normal_success_rate:                       1.000
wrong_success_rate:                        1.000
```

The dominant rejection pattern was:

```text
wrong_action_sequence_mean_l2_below_threshold
preferred_rejected_action_mean_l2_below_threshold
margin_gap_below_threshold
wrong_margin_not_lower_than_preferred
```

## Interpretation

M661 is an implementation pass and a corpus gate fail.

It did not fail because:

- preferred/rejected fields were missing;
- actor parameters changed;
- PPO or training was accidentally invoked;
- the surface had only one target;
- no candidate rows were evaluated.

It failed because the current M586/M636 matched-current surfaces are too weak
for action-divergent wrong-history supervision:

```text
same/similar current observation + wrong matched history
does not produce a distinct short-horizon action sequence
and does not produce a meaningful terminal-margin gap.
```

This preserves the previous evidence chain:

- M655: wrong-history information exists in raw/next recurrent state, but fused
  features and actor actions strongly attenuate it.
- M658: next-hidden diagnostic views improve relative signal, but absolute
  wrong-history gaps remain too small.
- M661: the matched-current rows are not outcome/action critical, so a
  stronger corpus cannot be mined from them by threshold weakening.

## Rejected Shortcuts

Do not:

- lower M661 thresholds and call the original corpus gate positive;
- use hidden-distance-only rows as action-divergent supervision;
- train a head or actor from the empty corpus;
- start PPO from this evidence;
- treat M636 projected preferred sequences as sufficient without a rejected
  wrong-history action/outcome gap.

## Decision

```text
action_divergent_wrong_history_corpus_audit_admit_action_critical_source_mining_design
```

## Next Branch

M663 should design an action-critical wrong-history source miner. The key change
is source selection, not objective tuning:

```text
from:
  matched-current rows selected mainly by current-observation/target separation

to:
  wrong-history pair candidates selected by observed action-sequence divergence
  and short-horizon outcome/margin sensitivity
```

M663 should still preserve the human-view actor contract and remain
no-training/no-PPO. It should pre-register:

- a broader snapshot bank across fresh/OOD BC5660 rollouts;
- candidate wrong-history hidden sources beyond nearest matched-current pairs;
- explicit scene/current-state similarity limits;
- first-action, sequence-action, margin, and success-drop thresholds;
- source-heldout split and source dominance caps;
- failure interpretation if no action-critical wrong-history pairs exist.

## Next

```text
m663-action-critical-wrong-history-source-mining-design
```
