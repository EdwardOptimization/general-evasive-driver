# M1377 Paper-Route Promoted-Base Source-Rich Sequence Intervention Probe

## Purpose

M1377 runs the no-training sequence intervention probe admitted by M1376.

Question:

```text
Can the M1375 reset-only source rows expose outcome-relevant temporal-history
dependence for the promoted M1362 public-gate base?
```

M1377 does not train, run PPO, promote, use private holdout, change actor inputs,
mutate the checkpoint, export an objective corpus, or make high-fidelity
per-wheel physics claims.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.capability_step_sequence_intervention_probe \
  --checkpoint runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt \
  --config configs/m991_capability_step_fault_source_wave.json \
  --source-rows runs/m1375_promoted_base_source_rich_public_wave/reset_only_rows.csv \
  --max-source-rows 384 \
  --per-fault-pair-cap 48 \
  --history-lengths 4,8,12 \
  --max-continuation-steps 48 \
  --min-margin-gap 0.012 \
  --min-sequence-action-l2 0.025 \
  --device auto \
  --run-dir runs/m1377_promoted_base_source_rich_sequence_intervention_probe
```

## Result

```text
result_class: sequence_temporal_history_positive
selected_source_rows: 384
intervention_rows: 6912
accepted_sequence_rows: 180
accepted_cross_fault_sequence_rows: 0
accepted_temporal_sequence_rows: 180
sequence_action_critical_rows: 1491
normal_failed_rows: 0
rejected_trace_rows: 0
unique_accepted_fault_pairs: 8
unique_accepted_seeds: 9
unique_cross_fault_accepted_fault_pairs: 0
unique_cross_fault_accepted_seeds: 0
unique_temporal_accepted_fault_pairs: 8
unique_temporal_accepted_seeds: 9
variant_count: 6
actor_parameters_changed: false
training_started: false
ppo_used: false
promoted: false
```

M1377 passes structurally:

```text
summary.json exists
selected_source_rows > 0
intervention_rows > 0
actor_parameters_changed == false
training_started == false
ppo_used == false
promoted == false
accepted temporal and cross-fault rows are reported separately
variant and history-length summaries exist
```

## Threshold Interpretation

Pre-registered temporal-positive candidate thresholds:

```text
accepted_temporal_sequence_rows >= 100
unique_temporal_accepted_fault_pairs >= 6
unique_temporal_accepted_seeds >= 12
```

Observed:

```text
accepted_temporal_sequence_rows: 180
unique_temporal_accepted_fault_pairs: 8
unique_temporal_accepted_seeds: 9
```

Interpretation:

```text
temporal rows: pass
fault-pair diversity: pass
seed diversity: below threshold
```

M1377 is therefore a strong temporal-history diagnostic result, but not yet a
fully source-diverse temporal-positive candidate for corpus export or objective
work.

## Variant Summary

```text
cross_fault_response_window:
  rows: 1152
  accepted: 0
  margin_gap_mean: 0.0000868116
  sequence_action_l2_mean: 0.0039470875

delayed_capability_history:
  rows: 1152
  accepted: 42
  margin_gap_mean: 0.0010947015
  sequence_action_l2_mean: 0.0281562177

reset_then_warm_history:
  rows: 1152
  accepted: 138
  margin_gap_mean: 0.0121516513
  sequence_action_l2_mean: 0.0848014030

wrong_commands_preferred_response:
  rows: 1152
  accepted: 0
  margin_gap_mean: 0.0000009513
  sequence_action_l2_mean: 0.0000379905

wrong_response_preferred_commands:
  rows: 1152
  accepted: 0
  margin_gap_mean: 0.0000153582
  sequence_action_l2_mean: 0.0019107382

zero_command_history_window:
  rows: 1152
  accepted: 0
  margin_gap_mean: -0.0014287071
  sequence_action_l2_mean: 0.0106411795
```

All accepted sequence rows are temporal variants:

```text
reset_then_warm_history: 138
delayed_capability_history: 42
```

All cross-fault/action-response mismatch variants remain zero-accepted.

## History-Length Summary

```text
history_length 4:
  rows: 2304
  accepted_rows: 56
  margin_gap_mean: 0.0021946128
  sequence_action_l2_mean: 0.0235267973

history_length 8:
  rows: 2304
  accepted_rows: 66
  margin_gap_mean: 0.0019154979
  sequence_action_l2_mean: 0.0205802196

history_length 12:
  rows: 2304
  accepted_rows: 58
  margin_gap_mean: 0.0018502727
  sequence_action_l2_mean: 0.0206402913
```

Accepted rows are not limited to one history length.

## Fault-Pair Coverage

Accepted temporal rows cover eight fault pairs:

```text
global_mu_drop->front_lateral_authority_drop: 35
global_mu_drop->brake_authority_drop: 31
front_lateral_authority_drop->global_mu_drop: 29
brake_authority_drop->global_mu_drop: 23
combined_fault->front_lateral_authority_drop: 21
delay_noise_fault->steering_fault: 16
drive_authority_drop->rear_lateral_authority_drop: 14
combined_fault->brake_authority_drop: 11
```

Accepted seeds:

```text
137511
137524
137529
137533
137537
137540
137541
137543
137563
```

The seed count is the main limitation.

## Supported Claims

M1377 supports:

```text
1. The promoted M1362 base has outcome-relevant temporal-history dependence on
   M1375 source-rich reset-only rows.
2. Temporal variants produce 180 accepted rows across 8 fault pairs.
3. Cross-fault sequence variants remain zero-accepted.
4. Actor and checkpoint contract remain unchanged.
```

## Unsupported Claims

M1377 does not support:

```text
1. cross-fault wrong-history self-identification;
2. source-diverse temporal corpus export without audit or expansion;
3. training, objective update, PPO, or promotion;
4. private-holdout generalization;
5. L0/L1/L2/L3 comparison conclusions;
6. high-fidelity per-wheel or real-vehicle transfer claims;
7. level3 anticipatory recurrent-belief self-identification.
```

## Decision

M1377 passes as a structural no-training sequence intervention probe. It is
temporal-history positive by row and fault-pair coverage, but seed-thin relative
to the pre-registered candidate threshold.

Decision:

```text
promoted_base_source_rich_sequence_probe_temporal_positive_seed_thin_route_to_audit
```

Next:

```text
m1378-paper-route-promoted-base-source-rich-sequence-probe-result-audit
```

M1378 should decide whether to:

```text
run an expanded sequence probe with larger source-row coverage;
export a temporal sequence corpus after a source-diversity audit;
redesign cross-fault sequence interventions;
or synthesize the source-rich branch before L0/L1/L2/L3 comparison.
```

Do not train, run PPO, promote, use private holdout, or call temporal positives
cross-fault self-identification.

## Artifacts

```text
runs/m1377_promoted_base_source_rich_sequence_intervention_probe/summary.json
runs/m1377_promoted_base_source_rich_sequence_intervention_probe/selected_source_rows.csv
runs/m1377_promoted_base_source_rich_sequence_intervention_probe/sequence_intervention_rows.csv
runs/m1377_promoted_base_source_rich_sequence_intervention_probe/accepted_sequence_rows.csv
runs/m1377_promoted_base_source_rich_sequence_intervention_probe/rejected_sequence_rows.csv
runs/m1377_promoted_base_source_rich_sequence_intervention_probe/variant_summary.csv
runs/m1377_promoted_base_source_rich_sequence_intervention_probe/fault_pair_summary.csv
runs/m1377_promoted_base_source_rich_sequence_intervention_probe/history_length_summary.csv
```
