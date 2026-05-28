# M1373 Paper-Route Promoted-Base Source-Rich Smoke

## Purpose

M1373 runs the no-training source-rich public smoke admitted by M1372.

Current public-gate base:

```text
runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt
```

This milestone does not train, run PPO, promote a checkpoint, use private
holdout, change actor inputs, mutate the checkpoint, or make high-fidelity
per-wheel physics claims.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.extreme_dynamics_scenario_corpus \
  --checkpoint runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt \
  --config configs/m990_capability_step_fault_scenarios.json \
  --pairing-mode cross_fault \
  --seed-start 137300 \
  --seed-count 64 \
  --device auto \
  --run-dir runs/m1373_promoted_base_source_rich_smoke
```

## Result

```text
result_class: cross_fault_wrong_sparse
scenario_count: 832
snapshot_count: 3289
matched_pair_count: 768
unmatched_rows: 0
accepted_rows: 2
reset_only_rows: 174
rejected_rows: 592
normal_failed_rejected: 184
history_insensitive_rejected: 408
history_action_critical_rows: 176
wrong_history_action_critical_rows: 2
reset_history_action_critical_rows: 174
unique_accepted_fault_families: 2
unique_accepted_wrong_fault_families: 2
unique_accepted_severities: 2
unique_accepted_seeds: 1
actor_parameters_changed: false
training_started: false
ppo_used: false
promoted: false
extreme_source_positive: false
wrong_history_source_positive: false
```

The smoke gate passes structurally:

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
scenario and pair artifacts exist
```

## Accepted Rows

M1373 finds two accepted wrong-history rows. Both are margin/action critical, but
neither is a collision/success-drop row.

```text
row 1:
  seed: 137303
  step: 24
  preferred: brake_authority_drop / severe
  wrong: global_mu_drop / extreme
  normal_margin: 4.1269249841
  wrong_margin: 4.1135868322
  history_margin_gap: 0.0133381519
  action_l2_gap: 0.0968363509
  success_drop: false

row 2:
  seed: 137303
  step: 20
  preferred: mass_cg_shift / moderate
  wrong: brake_authority_drop / severe
  normal_margin: 5.1155444052
  wrong_margin: 5.0896128939
  history_margin_gap: 0.0259315113
  action_l2_gap: 0.2290195376
  success_drop: false
```

Interpretation:

```text
accepted rows are nonzero, but sparse;
accepted rows cover one seed only;
accepted rows do not prove source-diverse cross-fault wrong-history
self-identification;
accepted rows should be retained as diagnostic evidence, not as a training or
promotion trigger.
```

## Reset-Only Signal

The stronger signal is reset-history sensitivity:

```text
reset_only_rows: 174
reset_history_action_critical_rows: 174
reset-positive fault-family pair groups: 11 / 15
```

Largest reset-positive groups:

```text
rear_lateral_authority_drop->drive_authority_drop: 24
brake_authority_drop->global_mu_drop: 22
mass_cg_shift->brake_authority_drop: 21
drive_authority_drop->rear_lateral_authority_drop: 20
global_mu_drop->brake_authority_drop: 18
combined_fault->front_lateral_authority_drop: 16
global_mu_drop->front_lateral_authority_drop: 15
front_lateral_authority_drop->global_mu_drop: 12
```

Reset-only rows remain weaker evidence than wrong-history outcome sensitivity:
they show the recurrent state matters under source-rich faults, but they do not
show that a specific wrong history induces the wrong dynamics belief. M1373
therefore supports source-rich public stress compatibility and reset sensitivity,
not strong cross-fault self-identification.

## Claim Boundary

Generated fault families:

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

Future-only high-fidelity fault families are recorded in
`model_fidelity_limits.md` and are not generated as faithful current-model
physics:

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

M1373 makes no true single-wheel, split-mu, halfshaft, stuck-caliper,
suspension, tire-damage, high-fidelity, or real-vehicle claim.

## Supported Claims

M1373 supports:

```text
1. The promoted M1362 public-gate base can be evaluated through the existing
   capability-step cross-fault public harness.
2. The run produces clean scenario, snapshot, matched-pair, intervention,
   accepted, reset-only, rejected, and model-fidelity artifacts.
3. Checkpoint and actor parameters remain unchanged.
4. The source-rich smoke has nonzero accepted wrong-history diagnostic rows.
5. Reset-hidden sensitivity is broad across many fault-family pair groups.
```

## Unsupported Claims

M1373 does not support:

```text
1. source-diverse cross-fault wrong-history self-identification;
2. source-rich promotion;
3. private-holdout generalization;
4. L0/L1/L2/L3 comparison conclusions;
5. PPO continuation readiness;
6. paper-level simulation evidence;
7. high-fidelity asymmetric wheel or per-wheel fault evidence;
8. level3 anticipatory recurrent-belief self-identification.
```

## Decision

M1373 passes as a source-rich public smoke, but the scientific signal is
classified as sparse wrong-history positives plus broad reset sensitivity.

Decision:

```text
promoted_base_source_rich_smoke_pass_sparse_source_route_to_audit
```

Next:

```text
m1374-paper-route-promoted-base-source-rich-smoke-result-audit
```

M1374 should decide whether to:

```text
route to a larger public source-rich wave;
route to reset/temporal-history intervention design;
route to source-rich evaluator/tooling changes;
or stabilize the source-rich distribution before L0/L1/L2/L3 comparison.
```

Do not train, run PPO, promote, use private holdout, relax thresholds, or claim
high-fidelity fault physics from M1373.

## Artifacts

```text
runs/m1373_promoted_base_source_rich_smoke/summary.json
runs/m1373_promoted_base_source_rich_smoke/scenario_summary.csv
runs/m1373_promoted_base_source_rich_smoke/snapshot_candidates.csv
runs/m1373_promoted_base_source_rich_smoke/matched_hidden_condition_pairs.csv
runs/m1373_promoted_base_source_rich_smoke/matched_cross_fault_pairs.csv
runs/m1373_promoted_base_source_rich_smoke/intervention_rollouts.csv
runs/m1373_promoted_base_source_rich_smoke/accepted_rows.csv
runs/m1373_promoted_base_source_rich_smoke/reset_only_rows.csv
runs/m1373_promoted_base_source_rich_smoke/rejected_rows.csv
runs/m1373_promoted_base_source_rich_smoke/fault_family_summary.csv
runs/m1373_promoted_base_source_rich_smoke/fault_family_pair_summary.csv
runs/m1373_promoted_base_source_rich_smoke/severity_summary.csv
runs/m1373_promoted_base_source_rich_smoke/severity_pair_summary.csv
runs/m1373_promoted_base_source_rich_smoke/cross_fault_pair_summary.csv
runs/m1373_promoted_base_source_rich_smoke/model_fidelity_limits.md
```
