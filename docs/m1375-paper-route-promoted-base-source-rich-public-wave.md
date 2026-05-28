# M1375 Paper-Route Promoted-Base Source-Rich Public Wave

## Purpose

M1375 runs the larger no-training source-rich public wave admitted by M1374.

Question:

```text
Do the sparse M1373 wrong-history positives repeat under broader fresh public
coverage?
```

M1375 does not train, run PPO, promote, use private holdout, change actor inputs,
mutate the checkpoint, relax source-positive thresholds, or make high-fidelity
per-wheel physics claims.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.extreme_dynamics_scenario_corpus \
  --checkpoint runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt \
  --config configs/m991_capability_step_fault_source_wave.json \
  --pairing-mode cross_fault \
  --seed-start 137500 \
  --seed-count 256 \
  --device auto \
  --run-dir runs/m1375_promoted_base_source_rich_public_wave
```

## Result

```text
result_class: cross_fault_wrong_sparse
scenario_count: 3328
snapshot_count: 16257
matched_pair_count: 4096
unmatched_rows: 1
accepted_rows: 3
reset_only_rows: 1281
rejected_rows: 2812
normal_failed_rejected: 936
history_insensitive_rejected: 1876
history_action_critical_rows: 1284
wrong_history_action_critical_rows: 3
reset_history_action_critical_rows: 1281
unique_accepted_fault_families: 2
unique_accepted_wrong_fault_families: 2
unique_accepted_severities: 1
unique_accepted_seeds: 2
actor_parameters_changed: false
training_started: false
ppo_used: false
promoted: false
extreme_source_positive: false
wrong_history_source_positive: false
```

The structural gate passes:

```text
summary.json exists
scenario_count > 0
snapshot_count > 0
matched_pair_count > 0
actor_parameters_changed == false
training_started == false
ppo_used == false
promoted == false
pairing_mode == cross_fault
model_fidelity_limits.md exists
```

The source-positive thresholds do not pass:

```text
required accepted_rows >= 40: observed 3
required unique_accepted_fault_families >= 4: observed 2
required unique_accepted_seeds >= 24: observed 2
```

## Accepted Rows

M1375 finds three accepted wrong-history rows:

```text
row 1:
  seed: 137533
  step: 36
  preferred: delay_noise_fault / severe
  wrong: steering_fault / severe
  normal_margin: 0.9733760628
  wrong_margin: 0.9473292371
  history_margin_gap: 0.0260468256
  action_l2_gap: 0.1725613922
  success_drop: false

row 2:
  seed: 137543
  step: 28
  preferred: steering_fault / severe
  wrong: front_lateral_authority_drop / severe
  normal_margin: 2.0645906223
  wrong_margin: 2.0439157091
  history_margin_gap: 0.0206749132
  action_l2_gap: 0.1506249607
  success_drop: false

row 3:
  seed: 137543
  step: 32
  preferred: steering_fault / severe
  wrong: front_lateral_authority_drop / severe
  normal_margin: 1.6701955776
  wrong_margin: 1.6447004278
  history_margin_gap: 0.0254951498
  action_l2_gap: 0.3242269754
  success_drop: false
```

Accepted-row interpretation:

```text
accepted rows are nonzero but sparse;
accepted rows cover two seeds only;
accepted rows cover two preferred/wrong fault families and one severity;
accepted rows are margin/action critical, not collision success-drop rows;
accepted rows are not source-diverse proof and not training-ready.
```

## Reset-Only Signal

M1375 confirms broad reset-hidden sensitivity:

```text
reset_only_rows: 1281
reset_history_action_critical_rows: 1281
reset-positive fault-family pair groups: 12 / 15
```

Largest reset-positive groups:

```text
rear_lateral_authority_drop->drive_authority_drop: 173
brake_authority_drop->global_mu_drop: 167
mass_cg_shift->brake_authority_drop: 159
global_mu_drop->brake_authority_drop: 150
drive_authority_drop->rear_lateral_authority_drop: 147
global_mu_drop->front_lateral_authority_drop: 107
combined_fault->front_lateral_authority_drop: 101
combined_fault->brake_authority_drop: 90
delay_noise_fault->steering_fault: 83
front_lateral_authority_drop->global_mu_drop: 66
```

This is consistent with M1373: recurrent state disruption matters broadly, but
single hidden-state wrong-history swaps rarely produce strong outcome-sensitive
wrong capability beliefs under the current cross-fault pairing.

## Comparison To M1373

```text
M1373:
  seed_count: 64
  matched_pair_count: 768
  accepted_rows: 2
  reset_only_rows: 174
  unique_accepted_seeds: 1

M1375:
  seed_count: 256
  matched_pair_count: 4096
  accepted_rows: 3
  reset_only_rows: 1281
  unique_accepted_seeds: 2
```

Increasing source coverage mostly scales reset-only rows, not wrong-history
accepted rows.

## Claim Boundary

Generated current-model/proxy fault families:

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

Future-only high-fidelity fault families remain metadata only:

```text
true_single_wheel_puncture_or_blowout_with_radius_drag_and_pull
true_single_corner_grip_collapse
true_left_right_split_mu_patch
true_stuck_caliper_or_single_wheel_brake_pull
true_single_wheel_brake_pressure_loss
true_asymmetric_half_shaft_or_cv_joint_torque_loss
open_or_locked_differential_failure
per_wheel_abs_fault
wheel_speed_sensor_drop_bias_or_quantization
steering_rack_asymmetry_or_tie_rod_damage
corner_suspension_damage_or_toe_change
tire_pressure_temperature_wear_or_delamination_dynamics
```

M1375 makes no true single-wheel, split-mu, halfshaft, stuck-caliper,
suspension, tire-damage, high-fidelity, real-vehicle, paper-level, or level3
self-identification claim.

## Supported Claims

M1375 supports:

```text
1. The promoted M1362 public-gate base can run through a larger source-rich
   public wave with clean artifacts.
2. The run preserves actor/checkpoint contract and performs no training or PPO.
3. Larger fresh coverage does not make the current cross-fault wrong-history
   evidence source-positive.
4. Reset-hidden sensitivity is broad and robust under capability-step faults.
```

## Unsupported Claims

M1375 does not support:

```text
1. source-diverse cross-fault wrong-history self-identification;
2. objective training from accepted wrong-history rows;
3. promotion;
4. private-holdout generalization;
5. L0/L1/L2/L3 comparison conclusions;
6. PPO continuation readiness;
7. paper-level simulation evidence;
8. high-fidelity asymmetric wheel or per-wheel fault evidence;
9. level3 anticipatory recurrent-belief self-identification.
```

## Decision

M1375 passes as a structural no-training public source-rich wave. It fails the
pre-registered source-positive interpretation thresholds and should be audited
before any next route.

Decision:

```text
promoted_base_source_rich_public_wave_pass_sparse_source_route_to_audit
```

Next:

```text
m1376-paper-route-promoted-base-source-rich-public-wave-result-audit
```

M1376 should decide whether the next branch should be:

```text
temporal/sequence intervention design;
retargeted source/fault-pair redesign;
capability-step evaluator extension;
or source-rich distribution stabilization before L0/L1/L2/L3 comparison.
```

Do not train, run PPO, promote, use private holdout, or relax source-positive
thresholds based on M1375.

## Artifacts

```text
runs/m1375_promoted_base_source_rich_public_wave/summary.json
runs/m1375_promoted_base_source_rich_public_wave/scenario_summary.csv
runs/m1375_promoted_base_source_rich_public_wave/snapshot_candidates.csv
runs/m1375_promoted_base_source_rich_public_wave/matched_hidden_condition_pairs.csv
runs/m1375_promoted_base_source_rich_public_wave/matched_cross_fault_pairs.csv
runs/m1375_promoted_base_source_rich_public_wave/intervention_rollouts.csv
runs/m1375_promoted_base_source_rich_public_wave/accepted_rows.csv
runs/m1375_promoted_base_source_rich_public_wave/reset_only_rows.csv
runs/m1375_promoted_base_source_rich_public_wave/rejected_rows.csv
runs/m1375_promoted_base_source_rich_public_wave/fault_family_summary.csv
runs/m1375_promoted_base_source_rich_public_wave/fault_family_pair_summary.csv
runs/m1375_promoted_base_source_rich_public_wave/severity_summary.csv
runs/m1375_promoted_base_source_rich_public_wave/severity_pair_summary.csv
runs/m1375_promoted_base_source_rich_public_wave/cross_fault_pair_summary.csv
runs/m1375_promoted_base_source_rich_public_wave/model_fidelity_limits.md
```
