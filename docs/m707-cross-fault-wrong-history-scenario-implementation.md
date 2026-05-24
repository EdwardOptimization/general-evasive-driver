# M707 Cross-Fault Wrong-History Scenario Implementation

## Purpose

M707 implements the M706 no-training cross-fault pairing diagnostic.

The question was whether the project had simply not mined enough extreme
hidden-condition cases. M707 therefore expands from nominal-vs-fault history
pairs to directed cross-fault history pairs:

```text
preferred current state: fault family A
wrong history:           incompatible fault family B
```

This milestone does not train or mutate the actor:

```text
no objective update
no PPO
no checkpoint promotion
no actor-input change
hidden fault labels remain logging and pairing metadata only
```

## Implementation

M707 adds:

```text
configs/cross_fault_hidden_condition_scenarios.json
src/autodrift/extreme_dynamics_scenario_corpus.py --pairing-mode cross_fault
matched_cross_fault_pairs.csv
fault_family_pair_summary.csv
severity_pair_summary.csv
cross_fault_pair_summary.csv
reset_only_rows.csv
```

The new config covers current single-track model capability faults:

```text
global_mu_drop
front_lateral_authority_drop
rear_lateral_authority_drop
brake_authority_drop
drive_authority_drop
steering_fault
mass_cg_shift
delay_noise_fault
combined_fault
```

It also records future high-fidelity/four-wheel-only cases without pretending
that the current model can physically generate them:

```text
single_wheel_grip_collapse
single_wheel_puncture_or_blowout
left_right_split_mu
stuck_caliper_or_single_wheel_brake_pull
true_asymmetric_half_shaft_torque_loss
wheel_speed_sensor_drop_or_bias
steering_pull_from_asymmetric_front_damage
```

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.extreme_dynamics_scenario_corpus \
  --checkpoint runs/m568_scaled_l3_bc_seed5660/checkpoint.pt \
  --config configs/cross_fault_hidden_condition_scenarios.json \
  --pairing-mode cross_fault \
  --seed-start 41000 \
  --seed-count 512 \
  --device cpu \
  --run-dir runs/m707_cross_fault_wrong_history_scenario
```

## Result

Summary:

```text
scenario_count:                      9728
snapshot_count:                     33026
matched_pair_count:                  2048
unmatched_rows:                       307
accepted_rows:                          0
reset_only_rows:                       15
rejected_rows:                       2033
normal_failed_rejected:               640
history_insensitive_rejected:        1393
wrong_history_action_critical_rows:     0
reset_history_action_critical_rows:    15
result_class: cross_fault_reset_only
actor_parameters_changed: false
training_started: false
ppo_used: false
promoted: false
```

The full run writes:

```text
runs/m707_cross_fault_wrong_history_scenario/summary.json
runs/m707_cross_fault_wrong_history_scenario/matched_cross_fault_pairs.csv
runs/m707_cross_fault_wrong_history_scenario/fault_family_pair_summary.csv
runs/m707_cross_fault_wrong_history_scenario/accepted_rows.csv
runs/m707_cross_fault_wrong_history_scenario/reset_only_rows.csv
runs/m707_cross_fault_wrong_history_scenario/rejected_rows.csv
```

## Fault-Pair Signal

Reset-only rows are concentrated in front-authority versus steering/combined
fault contrasts:

```text
front_lateral_authority_drop -> steering_fault:
  rows: 194
  reset_only_rows: 11
  wrong_history_action_critical_rows: 0

front_lateral_authority_drop -> combined_fault:
  rows: 48
  reset_only_rows: 2
  wrong_history_action_critical_rows: 0

steering_fault -> front_lateral_authority_drop:
  rows: 203
  reset_only_rows: 1
  wrong_history_action_critical_rows: 0

combined_fault -> front_lateral_authority_drop:
  rows: 56
  reset_only_rows: 1
  wrong_history_action_critical_rows: 0
```

Mean wrong-history margin gaps remain near zero across the high-row pair
groups, while reset-hidden gaps are nonzero only on a small subset. This
supports the narrow claim that the actor has some recurrent-state dependence
under front/steering extreme faults, but it does not support a wrong-history
self-identification source corpus.

## Interpretation

M707 makes the scenario-coverage hypothesis more concrete:

```text
not enough mining within ordinary scenarios:
  supported by M701/M698/M695 negative source results

not enough extreme hidden-condition coverage:
  weakened by M704 and M707
```

M704 and M707 both find reset-sensitive rows, so hidden/recurrent state can
matter. But both also find zero wrong-history-critical rows. Therefore the
current blocker is not just the absence of extreme fault labels or severity
coverage inside the current single-track model.

The more likely blocker is one of:

```text
1. wrong histories are not incompatible enough at the fused actor/action level;
2. current matched states are already sufficient for the deployed actor;
3. reset-hidden is a disruption effect, not a clean capability-belief effect;
4. the current single-track model cannot represent key asymmetric failure modes;
5. the actor was not trained to preserve fault-specific history beliefs under
   cross-fault history injection.
```

## Decision

M707 passes as an implementation milestone:

```text
cross-fault artifacts written
wrong-history and reset-history rows separated
reset-only rows not counted as source-positive
actor checksum unchanged
no training, no PPO, no promotion
```

But M707 does not admit source export, objective design, actor update, PPO, or
promotion:

```text
wrong_history_source_positive: false
result_class: cross_fault_reset_only
```

Next blocker:

```text
m708-cross-fault-wrong-history-scenario-audit
```
