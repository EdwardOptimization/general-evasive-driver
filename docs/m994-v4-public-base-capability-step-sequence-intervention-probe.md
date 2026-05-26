# M994 V4 Public Base Capability-Step Sequence Intervention Probe

## Purpose

M994 implements and runs the no-training trace-window sequence intervention
probe designed in M993.

Question:

```text
Can sequence-level interventions convert M991 reset-only evidence into cleaner
outcome-relevant self-identification evidence?
```

M994 does not train, run PPO, promote, use private holdout, or change actor
inputs.

## Implementation

M994 adds:

```text
src/autodrift/capability_step_sequence_intervention_probe.py
tests/test_capability_step_sequence_intervention_probe.py
```

The runner:

```text
1. loads the frozen M974 public-gate base;
2. reads M991 reset-only rows;
3. reconstructs preferred and wrong fault trace windows;
4. builds temporal and cross-fault sequence intervention hiddens;
5. replays each variant from the preferred current env state;
6. reports action gaps, terminal margins, success drops, and source diversity.
```

Hidden fault labels remain metadata only. The actor observation stays P0
human-view/no-oracle.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.capability_step_sequence_intervention_probe \
  --checkpoint runs/m974_exact_repair_from_base_s40_seed5974/candidate_checkpoint.pt \
  --config configs/m991_capability_step_fault_source_wave.json \
  --source-rows runs/m991_v4_public_base_capability_step_fault_source_wave/reset_only_rows.csv \
  --max-source-rows 384 \
  --per-fault-pair-cap 48 \
  --history-lengths 4,8,12 \
  --max-continuation-steps 48 \
  --min-margin-gap 0.012 \
  --min-sequence-action-l2 0.025 \
  --device auto \
  --run-dir runs/m994_v4_public_base_capability_step_sequence_intervention_probe
```

## Result

```text
result_class: sequence_temporal_history_positive
selected_source_rows: 384
intervention_rows: 6912
accepted_sequence_rows: 277
accepted_cross_fault_sequence_rows: 0
accepted_temporal_sequence_rows: 277
sequence_action_critical_rows: 1442
normal_failed_rows: 0
rejected_trace_rows: 0
unique_accepted_fault_pairs: 9
unique_accepted_seeds: 17
unique_cross_fault_accepted_fault_pairs: 0
unique_cross_fault_accepted_seeds: 0
unique_temporal_accepted_fault_pairs: 9
unique_temporal_accepted_seeds: 17
actor_parameters_changed: false
training_started: false
ppo_used: false
promoted: false
```

The first M994 run initially classified all accepted sequence rows as
`sequence_wrong_positive`. That was too broad. The code was corrected and the
run was repeated with separate cross-fault and temporal accepted counts. The
correct result is temporal-history positive, not cross-fault positive.

## Variant Summary

| Variant | Rows | Accepted | Mean margin gap | Mean sequence action L2 |
| --- | ---: | ---: | ---: | ---: |
| `cross_fault_response_window` | 1152 | 0 | -0.000099 | 0.003395 |
| `delayed_capability_history` | 1152 | 24 | 0.001293 | 0.030198 |
| `reset_then_warm_history` | 1152 | 253 | 0.010804 | 0.096883 |
| `wrong_commands_preferred_response` | 1152 | 0 | -0.000001 | 0.000044 |
| `wrong_response_preferred_commands` | 1152 | 0 | -0.000103 | 0.001808 |
| `zero_command_history_window` | 1152 | 0 | -0.000497 | 0.014166 |

Interpretation:

```text
Temporal continuity matters.
Cross-fault/action-response mismatch variants still do not produce accepted rows.
```

## Fault-Pair Coverage

Accepted temporal sequence rows cover:

```text
accepted fault pairs: 9
accepted seeds: 17
```

Top accepted fault-pair groups:

| Fault pair | Accepted rows |
| --- | ---: |
| `global_mu_drop -> brake_authority_drop` | 53 |
| `front_lateral_authority_drop -> global_mu_drop` | 43 |
| `combined_fault -> brake_authority_drop` | 32 |
| `delay_noise_fault -> steering_fault` | 30 |
| `global_mu_drop -> front_lateral_authority_drop` | 30 |
| `brake_authority_drop -> global_mu_drop` | 29 |
| `drive_authority_drop -> rear_lateral_authority_drop` | 29 |
| `combined_fault -> front_lateral_authority_drop` | 28 |

This is source-diverse for temporal-history evidence.

## History Length

| History length | Rows | Accepted rows | Mean margin gap | Mean sequence action L2 |
| ---: | ---: | ---: | ---: | ---: |
| 4 | 2304 | 126 | 0.002588 | 0.025941 |
| 8 | 2304 | 77 | 0.001758 | 0.023661 |
| 12 | 2304 | 74 | 0.001353 | 0.023644 |

Shorter reset-then-warm windows are more disruptive. That suggests the actor
needs more than a few recent frames to recover the hidden state used by the
current M974 driver, at least in these capability-step scenarios.

## Supported Claims

```text
M994 implements a reusable no-training trace-window intervention probe.
M974's recurrent state has outcome-relevant temporal-history dependence under
capability-step events.
Temporal sequence interventions produce source-diverse accepted rows.
Actor parameters and actor inputs remain unchanged.
```

## Not Supported

```text
M994 does not prove cross-fault wrong-history self-identification.
Cross-fault response-window and action-response mismatch variants produce zero
accepted rows in this probe.
The result does not justify PPO or checkpoint promotion.
The current single-track model still does not support true per-wheel/asymmetric
fault claims.
```

## Failure Taxonomy

```text
metric_artifact
```

Reason:

```text
The positive result is real but must be labeled as temporal-history positive.
Calling it cross-fault wrong-history positive would overclaim the evidence.
```

## Decision

Do not train. Do not run PPO. Do not promote.

Admit:

```text
m995-v4-public-base-capability-step-temporal-history-audit
```

M995 should decide whether to:

```text
1. export a temporal-history sequence corpus and run exact objective sanity;
2. redesign cross-fault mismatch interventions before corpus export;
3. synthesize the branch if temporal evidence is useful but cross-fault self-ID
   remains absent.
```

## Artifacts

```text
runs/m994_v4_public_base_capability_step_sequence_intervention_probe/summary.json
runs/m994_v4_public_base_capability_step_sequence_intervention_probe/selected_source_rows.csv
runs/m994_v4_public_base_capability_step_sequence_intervention_probe/sequence_intervention_rows.csv
runs/m994_v4_public_base_capability_step_sequence_intervention_probe/accepted_sequence_rows.csv
runs/m994_v4_public_base_capability_step_sequence_intervention_probe/rejected_sequence_rows.csv
runs/m994_v4_public_base_capability_step_sequence_intervention_probe/variant_summary.csv
runs/m994_v4_public_base_capability_step_sequence_intervention_probe/fault_pair_summary.csv
runs/m994_v4_public_base_capability_step_sequence_intervention_probe/history_length_summary.csv
```
