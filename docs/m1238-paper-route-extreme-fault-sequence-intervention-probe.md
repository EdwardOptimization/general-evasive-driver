# M1238 Paper-Route Extreme Fault Sequence Intervention Probe

## Summary

M1238 runs the no-training sequence-level command-response intervention probe
designed in M1237.

Command:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.capability_step_sequence_intervention_probe \
  --checkpoint runs/m1212_corrected_profile_repeat/profile_runs/L3_online_gru/seed_111602/checkpoint.pt \
  --config configs/m1236_extreme_fault_timing_repair_smoke.json \
  --source-rows runs/m1236_extreme_fault_timing_repair_smoke/rejected_rows.csv \
  --max-source-rows 384 \
  --per-fault-pair-cap 48 \
  --history-lengths 4,8,12 \
  --max-continuation-steps 18 \
  --min-margin-gap 0.012 \
  --min-sequence-action-l2 0.025 \
  --device auto \
  --run-dir runs/m1238_extreme_fault_sequence_intervention_probe
```

Result:

```text
result_class: sequence_no_signal
selected_source_rows: 384
history_lengths: 4, 8, 12
intervention_rows: 6912
variant_count: 6
accepted_sequence_rows: 0
accepted_cross_fault_sequence_rows: 0
accepted_temporal_sequence_rows: 0
sequence_action_critical_rows: 0
normal_failed_rows: 2178
rejected_trace_rows: 0
actor_parameters_changed: false
training_started: false
ppo_used: false
promoted: false
```

Decision:

```text
extreme_fault_sequence_probe_no_signal_route_to_negative_audit
```

M1238 passes as a no-training probe but produces no sequence-level temporal or
cross-fault signal.

## Probe Validity

The probe is valid as an evaluation run:

```text
selected_source_rows > 0
intervention_rows > 0
variant_count >= 6
normal_failed_rows < intervention_rows
rejected_trace_rows == 0
actor_parameters_changed == false
training_started == false
ppo_used == false
promoted == false
```

Normal failure is not dominant:

```text
normal_failed_rows: 2178 / 6912
normal_success_rate: 0.6848958333
```

The no-signal result is therefore not explained by trace reconstruction failure
or all-normal failure.

## Variant Results

Variant summary:

```text
cross_fault_response_window:
  rows: 1152
  accepted_rows: 0
  sequence_action_l2_mean: 0.0001163274
  margin_gap_mean: 0.0000065565

delayed_capability_history:
  rows: 1152
  accepted_rows: 0
  sequence_action_l2_mean: 0.0002804990
  margin_gap_mean: 0.0000034736

reset_then_warm_history:
  rows: 1152
  accepted_rows: 0
  sequence_action_l2_mean: 0.0005317838
  margin_gap_mean: -0.0000207878

wrong_commands_preferred_response:
  rows: 1152
  accepted_rows: 0
  sequence_action_l2_mean: 0.0000052414
  margin_gap_mean: -0.0000003671

wrong_response_preferred_commands:
  rows: 1152
  accepted_rows: 0
  sequence_action_l2_mean: 0.0001180618
  margin_gap_mean: 0.0000065359

zero_command_history_window:
  rows: 1152
  accepted_rows: 0
  sequence_action_l2_mean: 0.0020443838
  margin_gap_mean: -0.0001298598
```

All variants are well below the action-critical threshold:

```text
min_sequence_action_l2: 0.025
max variant mean action distance: 0.0020443838
```

## History-Length Results

History lengths also show no trend:

```text
history_length 4:
  accepted_rows: 0
  sequence_action_l2_mean: 0.0006274047

history_length 8:
  accepted_rows: 0
  sequence_action_l2_mean: 0.0004622234

history_length 12:
  accepted_rows: 0
  sequence_action_l2_mean: 0.0004585205
```

Longer history does not expose hidden dependence in this source.

## Interpretation

M1238 strengthens the negative evidence from M1236:

```text
single hidden-state swaps: no signal
sequence-level command-response interventions: no signal
delayed history: no signal
cross-fault response windows: no signal
zero-command history windows: no outcome signal
```

This does not prove the broader research goal is impossible. It says this
specific M1236 source distribution and current checkpoint do not expose
history-necessity evidence, even after repairing normal survival.

## Claim Boundary

Supported:

```text
The sequence intervention probe runs successfully on M1236 source rows.
The tested variants are no-signal under the current thresholds and 18-step
continuation.
```

Not supported:

```text
history necessity
recurrent belief
online self-identification
training readiness
promotion
paper-level result
true per-wheel/asymmetric fault physics
```

## Decision

```text
extreme_fault_sequence_probe_no_signal_route_to_negative_audit
```

M1239 should audit the negative result before any new source construction or
larger run. The audit should decide whether the branch needs synthesis, stronger
source construction, longer-horizon sequence testing, or a different task family.
