# M997 V4 Public Base Temporal Sequence Corpus Export Implementation

## Purpose

M997 implements the no-training exporter designed in M996.

It converts M994 temporal accepted rows into exact-auditable tensors and runs
sanity checks before any temporal objective design, actor update, PPO, or
promotion.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.capability_step_temporal_sequence_corpus_export \
  --checkpoint runs/m974_exact_repair_from_base_s40_seed5974/candidate_checkpoint.pt \
  --config configs/m991_capability_step_fault_source_wave.json \
  --m994-run-dir runs/m994_v4_public_base_capability_step_sequence_intervention_probe \
  --max-sequence-len 48 \
  --device auto \
  --run-dir runs/m997_v4_public_base_temporal_sequence_corpus_export
```

## Artifacts

```text
runs/m997_v4_public_base_temporal_sequence_corpus_export/summary.json
runs/m997_v4_public_base_temporal_sequence_corpus_export/temporal_sequence_corpus.npz
runs/m997_v4_public_base_temporal_sequence_corpus_export/metadata.csv
runs/m997_v4_public_base_temporal_sequence_corpus_export/diagnostic_rows.csv
runs/m997_v4_public_base_temporal_sequence_corpus_export/corpus_manifest.json
```

## Result

```text
result_class: temporal_sequence_corpus_export_pass
row_count: 277
positive_row_count: 277
diagnostic_row_count: 4608
unique_positive_fault_pairs: 9
unique_positive_seeds: 17
max_fault_pair_fraction: 0.191336
delayed_capability_history_positive_rows: 24
reset_then_warm_history_positive_rows: 253
normal_failed_rows: 0
accepted_cross_fault_positive_rows: 0
actor_parameters_changed: false
training_started: false
ppo_used: false
promoted: false
```

The source-diversity gate passes:

```text
positive_row_count >= 200
unique_positive_fault_pairs >= 8
unique_positive_seeds >= 16
max_fault_pair_fraction <= 0.25
delayed_capability_history_positive_rows >= 20
normal_failed_rows == 0
```

## Tensor Shapes

```text
decision_observation:           (277, 72)       float32
normal_initial_hidden:          (277, 128)      float32
variant_initial_hidden:         (277, 128)      float32
normal_rollout_observations:    (277, 48, 72)   float32
variant_rollout_observations:   (277, 48, 72)   float32
normal_rollout_actions:         (277, 48, 3)    float32
variant_rollout_actions:        (277, 48, 3)    float32
sequence_mask:                  (277, 48)       bool
variant_sequence_mask:          (277, 48)       bool
row_weight:                     (277,)          float32
history_length:                 (277,)          int64
variant_id:                     (277,)          int64
```

The exporter includes `variant_rollout_observations` in addition to the M996
minimum schema so the variant action sequence can be replay-checked exactly.

## Sanity Checks

Replay sanity:

```text
normal_action_replay_l2_max: 0.0
variant_action_replay_l2_max: 0.0
replay_sanity_passed: true
```

Exact no-update sanity:

```text
normal_sequence_logp_mean: 63.870464
variant_on_normal_sequence_logp_mean: 30.271999
temporal_logp_gap_mean: 33.598469
temporal_preference_loss_mean: 0.034725
exact_sanity_passed: true
tensor_sanity_passed: true
source_diversity_passed: true
```

Interpretation:

```text
Under the exported normal observation sequence, the current M974 public base
scores the normal uninterrupted hidden history substantially higher than the
temporal-disrupted hidden history on the same normal action sequence.
```

This is a no-update diagnostic, not a training claim.

## Variant Split

```text
delayed_capability_history: 24 rows, 5 seeds, 8 fault pairs
reset_then_warm_history: 253 rows, 17 seeds, 9 fault pairs
```

The reset-then-warm variant dominates row count. The corpus therefore stores a
normalized `row_weight` that balances variant and fault-pair frequency. Any
future exact objective should use the stored weights or explicitly justify a
different weighting.

## Fault-Pair Coverage

```text
brake_authority_drop -> global_mu_drop: 29
brake_authority_drop -> mass_cg_shift: 3
combined_fault -> brake_authority_drop: 32
combined_fault -> front_lateral_authority_drop: 28
delay_noise_fault -> steering_fault: 30
drive_authority_drop -> rear_lateral_authority_drop: 29
front_lateral_authority_drop -> global_mu_drop: 43
global_mu_drop -> brake_authority_drop: 53
global_mu_drop -> front_lateral_authority_drop: 30
```

The largest fault pair is `53 / 277 = 0.191336`, below the M996 source
dominance limit.

## Contract Check

Actor inputs remain P0 human-view:

```text
decision_observation: 72 deployable actor features
normal_initial_hidden / variant_initial_hidden: recurrent hidden state only
actions: steer / throttle / brake
```

Hidden fault names, terminal margins, success flags, and source metadata are
stored only in metadata artifacts. They are not actor inputs.

## Claim Scope

Allowed claim:

```text
The M994 temporal-history evidence can be represented as an exact-auditable
sequence corpus. The corpus passes replay, source-diversity, tensor, and
no-update log-prob sanity under the M974 public base.
```

Blocked claims:

```text
The corpus proves cross-fault wrong-history self-ID.
The corpus is a promoted driver checkpoint.
The corpus justifies PPO or training without objective design.
The corpus supports per-wheel/asymmetric failure claims.
```

## Decision

```text
temporal_sequence_corpus_export_pass_route_to_branch_synthesis
```

M989-M997 have now produced a coherent temporal-history corpus, while
cross-fault wrong-history evidence remains absent. The next step should be a
branch synthesis before opening a temporal objective branch.
