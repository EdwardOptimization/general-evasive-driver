# M654 Wrong-History Feature Separability Audit Design

## Purpose

M654 designs a no-training audit after M652 showed that a frozen
wrong-history contrast head preserves normal sequence-delta learning but fails
to create wrong-history separation.

This milestone is design-only:

```text
no training
no PPO
no actor update
no checkpoint promotion
```

## Blocker From M653

M653 classified M652 as:

```text
normal_retention_positive_wrong_history_gap_negative
```

The important evidence is split:

```text
normal_validation_delta_mse:
  6510: 0.000491
  6511: 0.000508
  6512: 0.000509

wrong_history_validation_gap_mse:
  6510: -0.000003
  6511: -0.000002
  6512: -0.000003

wrong_history_validation_prediction_gap_l2:
  6510: 0.000748
  6511: 0.000624
  6512: 0.000729
```

So the next question is not whether a generic sequence-delta target is
learnable. It is:

```text
Where did the normal-vs-wrong history information disappear?
```

## Audit Chain

M655 should inspect the frozen BC5660 representation along the exact path used
by M649-M652:

```text
stored recurrent hidden
  -> GRU update with current response frame
  -> fused response/context actor feature
  -> actor mean / tanh action
  -> auxiliary sequence-delta head input
```

For each corpus row, compute the same quantities under:

```text
normal_hidden
variant_hidden
```

using the same current 72-dim observation. This isolates history effects from
scene/context effects.

## Required Inputs

Use the current BC-v2 source-diverse sequence corpus:

```text
corpus:     runs/m641_source_diverse_sequence_target_corpus/balanced_sequence_target_corpus.npz
metadata:   runs/m641_source_diverse_sequence_target_corpus/balanced_sequence_targets.csv
checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
```

The audit must treat metadata as diagnostic labels only. Source ids, variants,
targets, and split labels must not enter actor inputs.

## Required Row Metrics

M655 should write a row-level CSV with at least:

```text
row_id
source_index
split
surface
target
variant
grid_name
sequence_length
weight

raw_hidden_l2
raw_hidden_cosine_distance
next_hidden_l2
next_hidden_cosine_distance
fused_feature_l2
fused_feature_cosine_distance
actor_mean_l2
actor_tanh_action_l2

next_hidden_retention_ratio = next_hidden_l2 / raw_hidden_l2
feature_retention_ratio = fused_feature_l2 / raw_hidden_l2
action_feature_ratio = actor_tanh_action_l2 / fused_feature_l2

sequence_delta_mse
sequence_delta_mean_step_l2
sequence_delta_max_step_l2
normal_base_action_reconstruction_l2
variant_base_action_reconstruction_l2
```

The reconstruction checks compare recomputed frozen-actor first actions against
stored `normal_base_action_sequence[:, 0, :]` and `variant_base_action`. They
are contract sanity checks, not promotion metrics.

## Required Group Summaries

M655 should write group summaries for:

```text
variant
split
source_index
source_index + split + variant
target
surface
```

Each group should report:

```text
rows
sources
weight_sum
weighted_mean and median for all distance metrics
min / max for actor_tanh_action_l2
sequence_delta_mse weighted mean
```

The wrong-history rows and delayed-history rows must be kept separate:

```text
wrong_matched_history:
  train source 30
  source_holdout_validation source 32

delayed_history:
  sources 0, 5, 7, 8, 13, 14, 20
```

Delayed-history is not the same causal intervention as wrong matched history,
but it is a useful comparison. If delayed-history rows show much larger feature
distances while wrong-history rows are tiny, the current corpus may only contain
weak wrong-history evidence for this checkpoint. If both are tiny, the frozen
representation is likely current-response dominated.

## Interpretation Matrix

M655 should classify the result using this matrix:

| Pattern | Interpretation | Next branch |
| --- | --- | --- |
| `raw_hidden_l2` is tiny | The corpus variants do not supply much recurrent difference | refresh / mine stronger wrong-history corpus |
| `raw_hidden_l2` is nonzero but `next_hidden_l2` collapses | Current response GRU update overwrites past-history evidence | inspect recurrent update or earlier history snippets |
| `next_hidden_l2` is nonzero but `fused_feature_l2` collapses | Response/context fusion erases self-ID signal | design adapter or feature objective at fused-feature boundary |
| `fused_feature_l2` is nonzero but `actor_tanh_action_l2` is tiny | Actor head is insensitive to the available signal | design action/preference objective, not more feature mining |
| `actor_tanh_action_l2` is nonzero but frozen head gaps remain tiny | Auxiliary head objective/head capacity is the likely blocker | redesign head objective/capacity before actor coupling |

M655 should not promote any checkpoint from these classifications.

## Diagnostic Thresholds

These thresholds are diagnostic, not promotion criteria:

```text
raw_hidden_l2_mean < 0.01:
  likely weak stored-history intervention

next_hidden_retention_ratio_mean < 0.20:
  likely GRU update washout

feature_retention_ratio_mean < 0.20:
  likely fusion washout

actor_tanh_action_l2_mean < 0.005:
  likely action/head insensitivity

wrong_history actor_tanh_action_l2 much smaller than delayed_history:
  current wrong-history rows may be too subtle for the branch
```

M655 may revise the numeric interpretation later if row distributions show
clearer natural scales, but it must preserve the raw metrics.

## Required Artifacts

M655 should write:

```text
runs/m655_wrong_history_feature_separability_audit/summary.json
runs/m655_wrong_history_feature_separability_audit/row_feature_separability.csv
runs/m655_wrong_history_feature_separability_audit/variant_summary.csv
runs/m655_wrong_history_feature_separability_audit/split_summary.csv
runs/m655_wrong_history_feature_separability_audit/source_summary.csv
runs/m655_wrong_history_feature_separability_audit/source_split_variant_summary.csv
runs/m655_wrong_history_feature_separability_audit/target_summary.csv
runs/m655_wrong_history_feature_separability_audit/surface_summary.csv
docs/m655-wrong-history-feature-separability-audit-implementation.md
```

## Forbidden Shortcuts

Do not:

- train a head or actor;
- run PPO;
- update any checkpoint;
- use metadata as actor input;
- tune contrast coefficients before this audit runs;
- treat feature distance alone as self-ID proof.

Feature separability is a necessary diagnostic. The later proof still requires
closed-loop wrong-history degradation or behavior-level evidence.

## Pass Criteria

M654 passes as a design milestone if it:

```text
pre-registers the row metrics
pre-registers the group summaries
separates wrong-history and delayed-history rows
defines the interpretation matrix
keeps actor coupling and contrast tuning blocked
creates the M655 implementation manifest
```

## Decision

`wrong_history_feature_separability_audit_design_admit_m655`

## Next

`m655-wrong-history-feature-separability-audit-implementation`
