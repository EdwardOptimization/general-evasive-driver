# M1236 Paper-Route Extreme Fault Timing Repair Smoke

## Summary

M1236 runs the no-training timing/horizon/source-window repair designed in
M1235.

Command:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.extreme_dynamics_scenario_corpus \
  --checkpoint runs/m1212_corrected_profile_repeat/profile_runs/L3_online_gru/seed_111602/checkpoint.pt \
  --config configs/m1236_extreme_fault_timing_repair_smoke.json \
  --pairing-mode cross_fault \
  --seed-start 123600 \
  --seed-count 64 \
  --device auto \
  --run-dir runs/m1236_extreme_fault_timing_repair_smoke
```

Result:

```text
result_class: history_insensitive_too_mild
scenario_count: 832
snapshot_count: 4095
matched_pair_count: 768
matched fault-family pairs: 14
matched seeds: 14
accepted_rows: 0
reset_only_rows: 0
rejected_rows: 768
normal_failed_rejected: 214
history_insensitive_rejected: 554
wrong_history_action_critical_rows: 0
reset_history_action_critical_rows: 0
actor_parameters_changed: false
training_started: false
ppo_used: false
promoted: false
```

Decision:

```text
extreme_fault_timing_repair_pass_route_to_sequence_intervention_design
```

M1236 passes the normal-survival timing-repair gate, but it does not produce
wrong-history or reset-hidden source-positive evidence.

## Timing Repair

M1236 changed only timing / horizon / source-window fields relative to M990:

```text
max_continuation_steps: 36 -> 18
max_snapshots_per_scenario: 4 -> 5
obstacle_longitudinal_min: -8.0 -> -4.0
obstacle_longitudinal_max: 80.0 -> 95.0
fault families unchanged
pairing rules unchanged
```

The normal-survival target was:

```text
normal_surviving_fraction >= 0.35
```

M1236 achieved:

```text
normal_surviving_rows = matched_pair_count - normal_failed_rejected
normal_surviving_rows = 768 - 214 = 554
normal_surviving_fraction = 0.7213541667
```

This is a real repair over M1233:

```text
M1233 normal_surviving_fraction: 0.171875
M1236 normal_surviving_fraction: 0.7213541667
```

## Source Coverage

Matched coverage remains adequate for a smoke:

```text
matched_pair_count: 768
matched fault-family pairs: 14
matched seeds: 14
```

Largest matched groups:

```text
brake_authority_drop -> global_mu_drop: 105
global_mu_drop -> brake_authority_drop: 81
combined_fault -> brake_authority_drop: 71
rear_lateral_authority_drop -> drive_authority_drop: 63
mass_cg_shift -> brake_authority_drop: 63
drive_authority_drop -> rear_lateral_authority_drop: 63
delay_noise_fault -> steering_fault: 63
```

## Scientific Signal

The timing repair also removes the reset-hidden signal:

```text
accepted_rows: 0
wrong_history_action_critical_rows: 0
reset_only_rows: 0
reset_history_action_critical_rows: 0
history_insensitive_rejected: 554
```

Interpretation:

```text
Shorter continuation and safer source windows fix normal-history viability, but
single cross-fault hidden-state swaps remain behaviorally too compatible.
```

This supports the M1234/M1235 diagnosis: more single hidden-swap tuning is not
the right next move.

## Claim Boundary

Supported:

```text
M1236 repairs normal-history survivability under the current hidden-fault source
config.
The run produces core artifacts with stable actor checksum and no training.
The repaired source rows are usable as normal-surviving inputs for a later
sequence-level intervention design.
```

Not supported:

```text
wrong-history causal-history proof
reset-hidden causal-history proof
history necessity
recurrent belief
online self-identification
training readiness
promotion
paper-level result
true per-wheel/asymmetric fault physics
```

## Selected Next Route

M1237 should design a sequence-level temporal intervention probe over the
M1236 normal-surviving rows.

The source should be filtered from:

```text
runs/m1236_extreme_fault_timing_repair_smoke/rejected_rows.csv
```

using:

```text
rejection_reason == history_insensitive_too_mild
```

Rationale:

```text
Those rows have normal-history viability but no single hidden-swap signal.
A short command-response sequence intervention can test whether a plausible
wrong or delayed recent history changes behavior more than a single hidden
state swap.
```

Do not train, run PPO, promote, or claim self-identification before the
sequence-level result exists and is audited.

## Decision

```text
extreme_fault_timing_repair_pass_route_to_sequence_intervention_design
```
