# M1379 Paper-Route Promoted-Base Source-Rich Sequence Expanded Probe

## Purpose

M1379 runs the expanded no-training sequence intervention probe admitted by
M1378.

Question:

```text
Can expanded source-row coverage resolve the M1377 accepted-seed diversity miss
while preserving temporal-history positives?
```

M1379 does not train, run PPO, promote, use private holdout, change actor inputs,
mutate the checkpoint, export a corpus, or make high-fidelity physical claims.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.capability_step_sequence_intervention_probe \
  --checkpoint runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt \
  --config configs/m991_capability_step_fault_source_wave.json \
  --source-rows runs/m1375_promoted_base_source_rich_public_wave/reset_only_rows.csv \
  --max-source-rows 768 \
  --per-fault-pair-cap 96 \
  --history-lengths 4,8,12 \
  --max-continuation-steps 48 \
  --min-margin-gap 0.012 \
  --min-sequence-action-l2 0.025 \
  --device auto \
  --run-dir runs/m1379_promoted_base_source_rich_sequence_expanded_probe
```

## Result

```text
result_class: sequence_temporal_history_positive
selected_source_rows: 768
intervention_rows: 13824
accepted_sequence_rows: 224
accepted_temporal_sequence_rows: 224
accepted_cross_fault_sequence_rows: 0
sequence_action_critical_rows: 2790
normal_failed_rows: 0
rejected_trace_rows: 0
unique_temporal_accepted_fault_pairs: 9
unique_temporal_accepted_seeds: 10
actor_parameters_changed: false
training_started: false
ppo_used: false
promoted: false
```

M1379 passes structurally:

```text
summary.json exists
selected_source_rows > 0
intervention_rows > 0
actor_parameters_changed == false
training_started == false
ppo_used == false
promoted == false
temporal and cross-fault accepted rows are separated
variant and history-length summaries exist
```

## Threshold Interpretation

Pre-registered expanded thresholds:

```text
accepted_temporal_sequence_rows >= 200
unique_temporal_accepted_fault_pairs >= 8
unique_temporal_accepted_seeds >= 12
```

Observed:

```text
accepted_temporal_sequence_rows: 224
unique_temporal_accepted_fault_pairs: 9
unique_temporal_accepted_seeds: 10
```

Interpretation:

```text
temporal rows: pass
fault-pair diversity: pass
seed diversity: still below threshold
```

Expanded source-row coverage improves rows, fault pairs, and seeds, but it still
does not clear the accepted-seed threshold for source-diverse temporal corpus
export.

## Variant Summary

```text
cross_fault_response_window:
  rows: 2304
  accepted: 0
  margin_gap_mean: 0.0000582608
  sequence_action_l2_mean: 0.0037038942

delayed_capability_history:
  rows: 2304
  accepted: 47
  margin_gap_mean: 0.0002161653
  sequence_action_l2_mean: 0.0270165585

reset_then_warm_history:
  rows: 2304
  accepted: 177
  margin_gap_mean: 0.0071849258
  sequence_action_l2_mean: 0.0755116078

wrong_commands_preferred_response:
  rows: 2304
  accepted: 0
  margin_gap_mean: 0.0000003575
  sequence_action_l2_mean: 0.0000407177

wrong_response_preferred_commands:
  rows: 2304
  accepted: 0
  margin_gap_mean: 0.0000172403
  sequence_action_l2_mean: 0.0017983335

zero_command_history_window:
  rows: 2304
  accepted: 0
  margin_gap_mean: -0.0010325124
  sequence_action_l2_mean: 0.0098932894
```

All accepted rows are temporal variants. Cross-fault/action-response mismatch
variants remain zero-accepted.

## History-Length Summary

```text
history_length 4:
  rows: 4608
  accepted_rows: 74
  margin_gap_mean: 0.0012396904
  sequence_action_l2_mean: 0.0217937694

history_length 8:
  rows: 4608
  accepted_rows: 83
  margin_gap_mean: 0.0010260940
  sequence_action_l2_mean: 0.0186868314

history_length 12:
  rows: 4608
  accepted_rows: 67
  margin_gap_mean: 0.0009564342
  sequence_action_l2_mean: 0.0185015997
```

The result is not tied to a single history length.

## Fault-Pair And Seed Coverage

Accepted temporal rows cover nine fault pairs:

```text
global_mu_drop->brake_authority_drop: 38
global_mu_drop->front_lateral_authority_drop: 37
front_lateral_authority_drop->global_mu_drop: 30
brake_authority_drop->global_mu_drop: 27
drive_authority_drop->rear_lateral_authority_drop: 23
combined_fault->front_lateral_authority_drop: 21
mass_cg_shift->brake_authority_drop: 19
delay_noise_fault->steering_fault: 16
combined_fault->brake_authority_drop: 13
```

Accepted seeds:

```text
137511
137524
137529
137533
137536
137537
137540
137541
137543
137563
```

The accepted-seed count improved from `9` in M1377 to `10` in M1379, still below
the threshold `12`.

## Supported Claims

M1379 supports:

```text
1. The promoted M1362 base has repeatable temporal-history dependence under
   expanded M1375 reset-only source rows.
2. Temporal accepted rows scale from 180 to 224 with larger source coverage.
3. Fault-pair coverage increases from 8 to 9.
4. Cross-fault sequence variants remain zero-accepted.
5. Actor/checkpoint contract remains unchanged.
```

## Unsupported Claims

M1379 does not support:

```text
1. source-diverse temporal corpus export without audit or redesign;
2. cross-fault wrong-history self-identification;
3. training, objective update, PPO, or promotion;
4. private-holdout generalization;
5. L0/L1/L2/L3 comparison conclusions;
6. high-fidelity per-wheel or real-vehicle transfer claims;
7. level3 anticipatory recurrent-belief self-identification.
```

## Decision

M1379 passes as a structural expanded no-training sequence probe and confirms
temporal-history dependence, but the accepted-seed threshold still misses. This
should be audited before any further sequence expansion or corpus export.

Decision:

```text
promoted_base_source_rich_sequence_expanded_probe_temporal_positive_seed_thin_route_to_audit
```

Next:

```text
m1380-paper-route-promoted-base-source-rich-sequence-expanded-result-audit
```

M1380 should decide whether to synthesize the source-rich branch, redesign
source selection for seed diversity, or design a temporal sequence corpus with
explicit seed-thin caveats. Do not run another local expansion before the audit.

## Artifacts

```text
runs/m1379_promoted_base_source_rich_sequence_expanded_probe/summary.json
runs/m1379_promoted_base_source_rich_sequence_expanded_probe/selected_source_rows.csv
runs/m1379_promoted_base_source_rich_sequence_expanded_probe/sequence_intervention_rows.csv
runs/m1379_promoted_base_source_rich_sequence_expanded_probe/accepted_sequence_rows.csv
runs/m1379_promoted_base_source_rich_sequence_expanded_probe/rejected_sequence_rows.csv
runs/m1379_promoted_base_source_rich_sequence_expanded_probe/variant_summary.csv
runs/m1379_promoted_base_source_rich_sequence_expanded_probe/fault_pair_summary.csv
runs/m1379_promoted_base_source_rich_sequence_expanded_probe/history_length_summary.csv
```
