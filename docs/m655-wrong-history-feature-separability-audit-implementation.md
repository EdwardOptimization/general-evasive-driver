# M655 Wrong-History Feature Separability Audit Implementation

## Purpose

M655 implements and runs the no-training wrong-history feature separability
audit designed in M654.

This milestone is diagnostic-only:

```text
no training
no PPO
no actor update
no checkpoint promotion
```

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.wrong_history_feature_separability_audit \
  --corpus runs/m641_source_diverse_sequence_target_corpus/balanced_sequence_target_corpus.npz \
  --metadata runs/m641_source_diverse_sequence_target_corpus/balanced_sequence_targets.csv \
  --checkpoint runs/m568_scaled_l3_bc_seed5660/checkpoint.pt \
  --device cpu \
  --run-dir runs/m655_wrong_history_feature_separability_audit
```

## Artifacts

```text
runs/m655_wrong_history_feature_separability_audit/summary.json
runs/m655_wrong_history_feature_separability_audit/row_feature_separability.csv
runs/m655_wrong_history_feature_separability_audit/variant_summary.csv
runs/m655_wrong_history_feature_separability_audit/split_summary.csv
runs/m655_wrong_history_feature_separability_audit/source_summary.csv
runs/m655_wrong_history_feature_separability_audit/source_split_variant_summary.csv
runs/m655_wrong_history_feature_separability_audit/target_summary.csv
runs/m655_wrong_history_feature_separability_audit/surface_summary.csv
```

## Contract Checks

The run stayed within the pre-registered contract:

```text
rows: 431
sources: 9
training_started: false
optimizer_started: false
actor_training_started: false
ppo_used: false
promoted: false
checkpoint_written: false
written_pt_files: []
actor_parameters_changed: false
```

Model checksum was unchanged:

```text
d9f636b495426c606140d15ddc207243979e87f1effbd89deb2946ae7c874c88
```

## Main Classification

M655 classifies the M652 wrong-history contrast failure as:

```text
fusion_washout
```

This means the wrong-history signal is present in stored recurrent hidden state
and survives part of the GRU update, but is strongly compressed before or at the
fused response/context feature used by the actor head and auxiliary head.

## Variant Summary

| Variant | Rows | Raw Hidden L2 | Next Hidden L2 | Fused Feature L2 | Actor Action L2 |
| --- | ---: | ---: | ---: | ---: | ---: |
| delayed_history | 328 | 0.556773 | 0.182988 | 0.073534 | 0.013368 |
| wrong_matched_history | 103 | 0.097340 | 0.039664 | 0.014905 | 0.000685 |

Retention ratios:

| Variant | Next / Raw | Feature / Raw | Action / Feature |
| --- | ---: | ---: | ---: |
| delayed_history | 0.327317 | 0.132473 | 0.184880 |
| wrong_matched_history | 0.409547 | 0.154235 | 0.045922 |

Wrong-history is much weaker than delayed-history:

```text
wrong_to_delayed_feature_l2_ratio: 0.202695
wrong_to_delayed_action_l2_ratio: 0.051232
```

## Wrong-History Source Breakdown

| Source | Split | Rows | Raw Hidden L2 | Next Hidden L2 | Fused Feature L2 | Actor Action L2 |
| ---: | --- | ---: | ---: | ---: | ---: | ---: |
| 30 | train | 39 | 0.089258 | 0.038773 | 0.014962 | 0.000792 |
| 32 | source_holdout_validation | 64 | 0.105421 | 0.040556 | 0.014848 | 0.000578 |

Source `30` and source `32` agree: the gap is not a single-source artifact.
The heldout source is slightly worse at the actor-action level.

## Interpretation

M655 rejects these explanations:

```text
stored history variant is completely absent:
  wrong raw_hidden_l2 is 0.097340, not near zero

GRU update fully erases history:
  wrong next_hidden_retention_ratio is 0.409547, not below 0.20

actor/checkpoint mutation:
  checksum unchanged and no checkpoint written
```

The positive finding is that wrong-history recurrent state differences are
measurable. The negative finding is that they are weak at the exact boundary
used by M649-M652:

```text
fused_feature_l2: 0.014905
actor_tanh_action_l2: 0.000685
```

That explains why the frozen auxiliary head learned normal sequence-delta
corrections but did not create useful wrong-history gaps. It was receiving a
feature stream where wrong-history differences are much smaller than
delayed-history differences, and the actor action map suppresses them further.

## Process Decision

Do not:

- increase M652 contrast coefficients;
- couple the auxiliary head into the actor;
- run PPO from this branch;
- claim self-ID proof from feature distances alone.

The next step should audit the result and choose between:

```text
fusion-boundary objective/design
stronger wrong-history corpus mining
pre-fusion recurrent-hidden diagnostic branch
```

## Decision

`wrong_history_feature_separability_audit_implementation_fusion_washout_admit_m656`

## Next

`m656-wrong-history-feature-separability-audit`
