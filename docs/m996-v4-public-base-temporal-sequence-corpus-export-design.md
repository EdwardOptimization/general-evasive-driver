# M996 V4 Public Base Temporal Sequence Corpus Export Design

## Purpose

M996 designs the export step for M994's temporal-history positive rows.

This milestone does not train, optimize, run PPO, promote a checkpoint, or
change actor inputs. It only defines the corpus that M997 should export and the
exact no-update sanity checks that must pass before any objective design.

## Evidence Boundary

M995 fixed the claim scope:

```text
positive evidence:
  temporal-history dependence under capability-step events

blocked evidence:
  source-diverse cross-fault wrong-history self-identification
```

M997 must therefore export positives only from these variants:

```text
reset_then_warm_history
delayed_capability_history
```

These variants remain diagnostic-only:

```text
cross_fault_response_window
wrong_commands_preferred_response
wrong_response_preferred_commands
zero_command_history_window
```

The diagnostic-only rows can be copied to metadata artifacts, but they must not
enter the positive target tensor set.

## Why A New Export Is Needed

`accepted_sequence_rows.csv` is not a trainable or exact-auditable corpus. It
contains source metadata and outcome metrics, but it does not contain the
decision observation, recurrent hidden state, action sequence, rollout mask, or
the variant initial hidden state.

M997 should reconstruct each accepted temporal row using the same deterministic
trace logic as M994:

```text
accepted_sequence_rows.csv
  -> seed / preferred fault / wrong fault / preferred step / wrong step
  -> collect preferred and wrong trace windows
  -> build variant hidden
  -> replay normal and variant continuations
  -> export tensors plus metadata
```

The `source_index` in M994's accepted CSV is the index into
`selected_source_rows.csv`, not a stable global row id. The exporter should treat
it only as a join key for M994 artifacts and should preserve all source fields
in the final metadata.

## Required Artifacts

M997 should write a run directory such as:

```text
runs/m997_v4_public_base_temporal_sequence_corpus_export/
```

Required files:

```text
temporal_sequence_corpus.npz
metadata.csv
diagnostic_rows.csv
summary.json
corpus_manifest.json
```

Optional but useful files:

```text
source_filtered_rows.csv
variant_summary.csv
fault_pair_summary.csv
history_length_summary.csv
```

## Tensor Schema

The `.npz` file should contain only deployable actor inputs, hidden states, and
actions. Hidden fault names and outcome labels stay in metadata files.

Required arrays:

```text
decision_observation              float32 [N, 72]
normal_initial_hidden             float32 [N, H]
variant_initial_hidden            float32 [N, H]
normal_rollout_observations        float32 [N, K, 72]
normal_rollout_actions             float32 [N, K, 3]
variant_rollout_actions            float32 [N, K, 3]
sequence_mask                      bool    [N, K]
normal_terminal_margin             float32 [N]
variant_terminal_margin            float32 [N]
terminal_margin_gap                float32 [N]
first_action_l2                    float32 [N]
sequence_action_l2_mean            float32 [N]
sequence_action_l2_max             float32 [N]
row_weight                         float32 [N]
variant_id                         int64   [N]
history_length                     int64   [N]
```

`K` should be fixed for the corpus. The first implementation should use the M994
continuation horizon:

```text
K = 48
```

Shorter rollouts should be padded with zeros and marked by `sequence_mask`.

The exporter should also store enough read-only manifest fields to make the
corpus reproducible:

```text
checkpoint_path
checkpoint_sha256
scenario_config_path
source_summary_path
accepted_rows_path
selected_source_rows_path
observation_dim
action_dim
hidden_dim
max_sequence_len
allowed_positive_variants
diagnostic_variants
```

## Metadata Schema

`metadata.csv` should preserve all source and diagnostic fields needed to audit
source diversity and failure modes without feeding them to the actor.

Required columns:

```text
row_id
source_index
seed
preferred_fault
preferred_fault_family
wrong_fault
wrong_fault_family
fault_pair
history_length
variant
preferred_step
wrong_step
normal_success
variant_success
success_drop
normal_margin
variant_margin
margin_gap
normal_terminal_reason
variant_terminal_reason
first_action_l2
sequence_action_l2_mean
sequence_action_l2_max
row_weight
positive_target
diagnostic_only
```

`positive_target` must be true only for accepted rows from:

```text
reset_then_warm_history
delayed_capability_history
```

`diagnostic_only` must be true for all cross-fault/action-response mismatch
variants and for any nonaccepted temporal rows exported for comparison.

## Weighting

The temporal corpus is useful but variant-imbalanced:

```text
reset_then_warm_history: 253
delayed_capability_history: 24
```

M997 should write a deterministic `row_weight` to avoid letting
`reset_then_warm_history` dominate every later exact objective.

Recommended weighting:

```text
weight = 1 / sqrt(count_by_variant * count_by_fault_pair)
normalize weights so mean(weight) == 1.0
```

This keeps all rows available while preventing a single variant or fault pair
from becoming the whole objective.

## Exact No-Update Sanity

M997 should run exact sanity with the current M974 public base immediately after
export. It should not update parameters.

Required checks:

```text
row_count == 277
positive_row_count == 277
diagnostic_positive_count == 0
unique_positive_fault_pairs >= 8
unique_positive_seeds >= 16
accepted_cross_fault_positive_rows == 0
all tensors finite
decision_observation.shape[1] == 72
normal_rollout_actions.shape[2] == 3
normal_initial_hidden.shape == variant_initial_hidden.shape
sequence_mask has at least one true step per row
mean(row_weight) == 1.0 within tolerance
```

The replay sanity should recompute current-checkpoint deterministic actions
from the exported decision observations and hidden states:

```text
normal_action_replay_l2_max <= 1e-5
variant_action_replay_l2_max <= 1e-5
```

If numerical replay from saved hidden tensors differs beyond tolerance, M997
must stop and classify the issue before any objective design.

## Exact Objective Sanity

M997 should compute, but not optimize, these diagnostic losses:

```text
normal_sequence_nll:
  -sum log pi(normal_action_t | normal_observation_t, normal_hidden_t)

variant_on_normal_sequence_nll:
  -sum log pi(normal_action_t | normal_observation_t, variant_hidden_t)

temporal_preference_loss:
  softplus(normal_sequence_logp_under_variant_hidden
           - normal_sequence_logp_under_normal_hidden
           + margin)
```

The exact loss is not yet a training recipe. Its purpose is to verify that the
exported tensors support the intended comparison:

```text
normal uninterrupted history should score the normal safe sequence better than
the disrupted temporal history does, for rows where the disrupted temporal
history lowered terminal margin.
```

Do not train the variant branch toward its degraded action sequence. The variant
sequence is evidence that disrupted history changes behavior and outcome; it is
not a desired behavior target.

## Source-Diversity Gate

M997 should pass source-diversity before any objective design:

```text
positive_row_count >= 200
unique_positive_fault_pairs >= 8
unique_positive_seeds >= 16
max_fault_pair_fraction <= 0.25
delayed_capability_history_positive_rows >= 20
normal_failed_rows == 0
```

The variant distribution may remain imbalanced, but the imbalance must be
explicitly reported and compensated through `row_weight`.

## Contract Guard

The exporter may store hidden fault labels, success flags, and terminal margins
as metadata. Those fields must not be part of the deployable actor tensor input.

Forbidden actor inputs remain forbidden:

```text
mu / hidden dynamics parameters
fault labels
success / collision / margin labels
oracle feasibility
TTC / required clearance
reference trajectory
slip / tire force / friction margin
```

## M997 Implementation Plan

M997 should implement a no-training exporter:

```text
python -m autodrift.capability_step_temporal_sequence_corpus_export \
  --checkpoint runs/m974_exact_repair_from_base_s40_seed5974/candidate_checkpoint.pt \
  --config configs/m991_capability_step_fault_source_wave.json \
  --m994-run-dir runs/m994_v4_public_base_capability_step_sequence_intervention_probe \
  --max-sequence-len 48 \
  --device auto \
  --run-dir runs/m997_v4_public_base_temporal_sequence_corpus_export
```

Acceptance for M997:

```text
export artifacts exist
exact no-update sanity passes
source-diversity gate passes
actor checksum unchanged
training_started == false
ppo_used == false
promoted == false
```

## Blocked Routes

Do not:

```text
run PPO;
promote;
train from M994 CSV metrics;
export cross-fault zero rows as positives;
train the variant branch toward degraded actions;
add hidden fault labels to actor observations;
claim cross-fault wrong-history self-ID.
```

## Decision

```text
temporal_sequence_corpus_export_design_admit_m997
```

M997 should implement the exporter and exact no-update sanity before any
temporal-history objective design or actor update.
