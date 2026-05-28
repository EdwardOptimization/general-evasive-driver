# M1233 Paper-Route Extreme Fault Source Smoke

## Summary

M1233 runs the bounded no-training smoke admitted by M1232.

Command:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.extreme_dynamics_scenario_corpus \
  --checkpoint runs/m1212_corrected_profile_repeat/profile_runs/L3_online_gru/seed_111602/checkpoint.pt \
  --config configs/m990_capability_step_fault_scenarios.json \
  --pairing-mode cross_fault \
  --seed-start 123300 \
  --seed-count 64 \
  --device auto \
  --run-dir runs/m1233_paper_route_extreme_fault_source_smoke
```

Result:

```text
result_class: cross_fault_reset_only
scenario_count: 832
snapshot_count: 3211
matched_pair_count: 768
unmatched_rows: 0
accepted_rows: 0
reset_only_rows: 58
rejected_rows: 710
normal_failed_rejected: 636
history_insensitive_rejected: 74
wrong_history_action_critical_rows: 0
reset_history_action_critical_rows: 58
actor_parameters_changed: false
training_started: false
ppo_used: false
promoted: false
```

Decision:

```text
extreme_fault_source_smoke_reset_only_route_to_audit
```

M1233 passes the infrastructure smoke but does not produce source-positive
cross-fault wrong-history evidence.

## Smoke Gate

The compatibility/source-shape smoke passes:

```text
summary.json exists
scenario_summary.csv exists
snapshot_candidates.csv exists
matched_cross_fault_pairs.csv exists
intervention_rollouts.csv exists
model_fidelity_limits.md exists
scenario_count > 0
snapshot_count > 0
matched_pair_count > 0
actor_parameters_changed == false
training_started == false
ppo_used == false
promoted == false
```

The run produced broad matched-pair coverage:

```text
matched_cross_fault_pairs: 768
matched fault-family pairs: 15
matched seeds: 17
```

The current-model / proxy fault families were:

```text
brake_authority_drop
combined_fault
delay_noise_fault
drive_authority_drop
front_lateral_authority_drop
global_mu_drop
mass_cg_shift
rear_lateral_authority_drop
steering_fault
```

## Scientific Signal

Wrong-history evidence is negative at this smoke scale:

```text
accepted_rows: 0
wrong_history_action_critical_rows: 0
wrong_history_source_positive: false
```

Reset-hidden evidence is nonzero:

```text
reset_only_rows: 58
reset_history_action_critical_rows: 58
```

Reset-only source shape:

```text
unique reset-only fault-family pairs: 13
unique reset-only preferred families: 9
unique reset-only wrong families: 8
unique reset-only severity pairs: 5
unique reset-only seeds: 2
```

Largest reset-only groups:

```text
combined_fault -> front_lateral_authority_drop: 9
global_mu_drop -> front_lateral_authority_drop: 8
brake_authority_drop -> global_mu_drop: 8
rear_lateral_authority_drop -> drive_authority_drop: 5
front_lateral_authority_drop -> global_mu_drop: 5
drive_authority_drop -> rear_lateral_authority_drop: 5
delay_noise_fault -> steering_fault: 5
```

This is useful diagnostic signal, but it is not enough for self-identification:
reset-hidden disruption can be generic recurrent-state sensitivity, and here it
is also seed-collapsed.

## Rejection Shape

Rejected rows are dominated by normal-branch failure:

```text
normal_failed_rejected: 636
history_insensitive_rejected: 74
```

This matters because many candidate pairs are not viable proof rows: the normal
history branch does not survive the continuation, so wrong-history degradation
cannot be interpreted as causal history evidence.

## Claim Boundary

Supported:

```text
The current paper-route L3 checkpoint is compatible with the hidden
capability-step/fault corpus harness.
The run produces core artifacts and matched cross-fault pairs with actor checksum
unchanged.
The branch exposes reset-hidden sensitivity under fault scenarios.
```

Not supported:

```text
source-diverse cross-fault wrong-history proof
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
extreme_fault_source_smoke_reset_only_route_to_audit
```

M1234 should audit whether the M1233 result is mainly:

```text
normal-branch scenario timing/horizon failure
wrong-history pairing too compatible
reset-only recurrent disruption
seed-collapsed source signal
or a useful route toward sequence-level temporal intervention sources
```

Do not train, run PPO, promote, or scale the source wave before that audit.
