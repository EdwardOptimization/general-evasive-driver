# M1258 Paper-Route Richer-Fault Capability Source Design

## Summary

M1258 designs the next source branch after M1257 closed the local
capability-separable source-construction branch.

Decision:

```text
richer_fault_capability_source_design_admit_bounded_v4_proxy_fault_smoke
```

The next evidence variable is source family / fault richness, not another
timing, proposal-budget, or relocation tweak.

The first bounded smoke should reuse the existing v4 low-margin proxy-fault
configuration:

```text
configs/extreme_fault_distribution_v4_low_margin_refresh_scenarios.json
```

This is design-only. No training, PPO, checkpoint promotion, private holdout,
actor-input expansion, threshold relaxation, self-identification claim,
paper-level claim, or high-fidelity physical fault claim occurs in M1258.

## Why This Branch

M1257 synthesized M1241-M1256 as:

```text
capability_separable_source_family_gap
```

The local source branch tried:

```text
first-action lattice
short-sequence lattice
viability-band relocation
fine relocation
condition-wise trajectory proposals
targeted margin restoration
denser event timing/source state
```

All produced:

```text
accepted_separable_pairs: 0
```

The clean next variable is therefore not more local search around the same
source family. It is a broader source family with richer hidden capability
changes.

## Source Config

M1259 should use:

```text
configs/extreme_fault_distribution_v4_low_margin_refresh_scenarios.json
```

This config includes richer current-model fault/proxy families such as:

```text
global_mu_drop:
  mu_drop_extreme_preexisting
  ice_patch_emergency_entry
  wet_to_ice_mid_maneuver

front_lateral_authority_drop:
  front_corner_grip_collapse_proxy
  front_blowout_grip_proxy_pre_emergency
  front_corner_suspension_proxy

rear_lateral_authority_drop:
  rear_corner_grip_collapse_proxy
  rear_corner_suspension_proxy

brake_authority_drop:
  brake_fade_extreme_pre_emergency
  single_wheel_brake_loss_proxy

drive_authority_drop:
  halfshaft_torque_loss_proxy
  drive_cut_mid_maneuver

steering_fault:
  steering_authority_collapse
  steering_stuck_mid_maneuver_proxy

delay_noise_fault:
  actuator_sensor_delay_extreme
  sensor_delay_authority_proxy

mass_cg_shift:
  payload_front_heavy_extreme
  payload_rear_heavy_extreme
  high_inertia_roof_load

combined_fault:
  rear_blowout_drive_grip_proxy_emergency
  stuck_caliper_brake_pull_proxy
  low_mu_brake_loss_proxy
  rear_drive_oversteer_loss_proxy
  brake_pull_steer_delay_proxy
  split_mu_front_authority_proxy
  split_mu_rear_oversteer_proxy
  blowout_low_mu_brake_proxy
  loaded_vehicle_brake_fade_extreme
```

## Claim Boundary

The v4 config explicitly separates:

```text
current_model_fault:
  directly represented by current VehicleParams changes

current_model_proxy:
  capability-loss proxy in the current single-track model; useful for stress
  and self-ID mining but not a true asymmetric wheel-level physical claim

future_four_wheel_or_high_fidelity:
  requires four-wheel/contact-patch dynamics, per-wheel actuation/sensing, or a
  higher-fidelity engine before physical claims are allowed
```

Therefore M1259 may mine proxy faults such as:

```text
front_blowout_grip_proxy_pre_emergency
stuck_caliper_brake_pull_proxy
single_wheel_brake_loss_proxy
halfshaft_torque_loss_proxy
split_mu_front_authority_proxy
```

But it must not claim true:

```text
single-wheel blowout physics
single-corner grip collapse physics
left-right split-mu physics
stuck-caliper yaw moment physics
single-wheel brake pressure loss
asymmetric half-shaft torque loss
open/locked differential failure
per-wheel ABS failure
suspension/toe damage
tire pressure/temperature/delamination dynamics
```

Those remain future high-fidelity or four-wheel simulator work.

## M1259 Bounded Smoke

M1259 should reuse the existing capability-separable constructor and keep the
accepted-source thresholds unchanged:

```text
min_best_action_l2: 0.12
min_cross_regret_margin: 0.02
own-branch best margins must be >= 0.0
```

Proposed command:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.capability_separable_source_constructor \
  --checkpoint runs/m1212_corrected_profile_repeat/profile_runs/L3_online_gru/seed_111602/checkpoint.pt \
  --config configs/extreme_fault_distribution_v4_low_margin_refresh_scenarios.json \
  --pairing-mode cross_fault \
  --seed-start 78048 \
  --seed-count 4 \
  --max-pairs 12 \
  --max-pairs-per-seed 4 \
  --max-pairs-per-family-pair 4 \
  --candidate-mode trajectory_proposal \
  --sequence-length 4 \
  --proposal-count-per-condition 24 \
  --proposal-seed 125900 \
  --proposal-steer-scale 0.45 \
  --proposal-brake-scale 0.45 \
  --proposal-throttle-scale 0.25 \
  --source-window-mode viability_band_relocation \
  --target-min-best-margin 0.002 \
  --target-max-best-margin 0.08 \
  --max-relocation-candidates 12 \
  --fine-relocation \
  --fine-parent-count 1 \
  --max-continuation-steps 18 \
  --min-best-action-l2 0.12 \
  --min-cross-regret-margin 0.02 \
  --device auto \
  --run-dir runs/m1259_richer_fault_capability_source_smoke
```

Runtime bounds:

```text
seed_count: 4
max_pairs: 12
max_pairs_per_seed: 4
max_pairs_per_family_pair: 4
proposal_count_per_condition: 24
sequence_length: 4
max_relocation_candidates: 12
max_continuation_steps: 18
```

M1259 should not use private holdout. The v4 config is public diagnostic/source
mining material in this route.

## Acceptance

M1259 passes as infrastructure if:

```text
summary.json exists
trajectory_proposals > 0
trajectory_proposal_rollouts > 0
matched_pair_count > 0
unique_matched_fault_family_pairs is reported
accepted_separable_pairs is reported
model_fidelity_limits.md exists
actor_parameters_changed == false
labels_enter_actor_input == false
training_started == false
ppo_used == false
promoted == false
private_holdout_used == false
actor_input_contract_changed == false
```

M1259 is source-positive only if accepted rows meet the unchanged criteria:

```text
best_A_success == true
best_B_success == true
margin_A_best_A >= 0.0
margin_B_best_B >= 0.0
best_action_l2 >= 0.12
cross_regret_A >= 0.02
cross_regret_B >= 0.02
```

Accepted rows remain diagnostic until a separate source-diversity audit.

## Failure Handling

If M1259 produces zero accepted rows but richer action-divergent near-misses:

```text
write a richer-fault source result audit before any repair
```

If M1259 produces accepted rows:

```text
do not train immediately;
audit source diversity, fault-family dominance, seed dominance, and proxy class
balance first
```

If the constructor cannot safely consume the v4 config:

```text
write an implementation-only compatibility milestone
```

If the result depends on true per-wheel/asymmetric claims:

```text
route to high-fidelity simulator selection/design instead of claiming success
```

## Decision

Admit:

```text
m1259-paper-route-richer-fault-capability-source-smoke
```
