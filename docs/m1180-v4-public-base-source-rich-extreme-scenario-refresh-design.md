# M1180 V4 Public Base Source-Rich Extreme Scenario Refresh Design

## Purpose

M1180 designs the new `source_rich_extreme_scenario_surface_refresh` branch
opened by M1179.

This milestone is design-only. It does not run mining, run replay, train actor
weights, run PPO, promote, use private holdout, convert failed rows, or change
actor inputs.

## Why This Branch

M1171-M1179 showed that replaying and rescoring the M1161 outcome table is not
enough:

```text
M1175 selected 240 action-divergent candidates across 17 physical pairs.
M1177 materialized 78 raw accepted wrong-history rows.
M1177 balanced surface still had only 2 physical pairs and 1 target.
M1178 confirmed those pairs exactly match the old M1169 active set.
M1175 source_obstacle_bucket was x=nan|y=nan for all selected rows.
```

So the next branch must generate source-rich data instead of continuing
artifact-only expansion.

## Prior Route Lessons

M824-M831 already explored extreme hidden-dynamics data routes. Useful lessons:

1. Extreme/fault scenario generation is the right evidence direction when
   same-corpus gates stall.
2. Source rows must record fault family, fidelity class, onset bucket, warm-up
   mode, and target obstacle geometry.
3. Current-model faults, proxy faults, and future-only wheel-level faults must
   stay separate.
4. Broad source generation alone is not enough; near-boundary filtering must
   happen before wrong-history pairing.
5. Matched action-divergent pairs without boundary pressure can produce action
   changes but tiny margin changes.

The current branch should reuse these lessons under the current public-gate
base:

```text
runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt
```

not the older M568+M761 route unless explicitly justified.

## Fault Fidelity Boundary

The current simulator is still not a four-wheel vehicle model. It can support
or proxy these current-model axes:

```text
current_model_fault:
  global_mu_drop
  front_lateral_authority_drop
  rear_lateral_authority_drop
  brake_authority_drop
  steering_fault
  mass_cg_shift

current_model_proxy:
  drive_authority_drop
  delay_noise_fault
  combined_fault
```

These must be logged as future-only until the simulator is extended:

```text
single_wheel_grip_collapse
single_wheel_puncture_or_blowout
left_right_split_mu
stuck_caliper_or_single_wheel_brake_pull
true_asymmetric_half_shaft_torque_loss
wheel_speed_sensor_drop_or_bias
steering_pull_from_asymmetric_front_damage
```

Future-only faults can motivate the roadmap, but they cannot be counted as
current-model evidence.

## Required Source Schema

Any new source-rich route must emit rows with at least:

```text
source_id
seed
step
checkpoint_label
fault_name
fault_family
fidelity_class
fault_activation_step
fault_onset_bucket
severity
warmup_mode
warmup_steps
source_obstacle_body_x
source_obstacle_body_y
source_obstacle_half_width
target_obstacle_body_x
target_obstacle_body_y
target_obstacle_half_width
ego_vx_norm
ego_vy_norm
ego_yaw_rate_norm
normal_success
normal_collision
normal_margin
normal_action_prefix
candidate_source_axis
boundary_axis
```

Wrong-history or paired rows must additionally emit:

```text
left_source_id
right_source_id
left_fault_family
right_fault_family
left_fidelity_class
right_fidelity_class
ego_response_distance
obstacle_geometry_distance
first_action_l2
action_prefix_l2_mean
normal_margin_gap_abs
wrong_history_margin_gap
wrong_history_success_drop
```

## Candidate Generation Rule

The new route should be boundary-first:

1. Generate source snapshots across fault family, onset, severity, warm-up mode,
   and obstacle geometry.
2. Retarget obstacle timing, lateral offset, and half width until normal
   history is near boundary.
3. Only then match different hidden-dynamics histories by visible ego/scene
   distance.
4. Require action divergence before wrong-history replay.
5. Evaluate wrong-history, reset-hidden, zero-command, command-shift, and
   response-delay interventions separately.
6. Balance accepted rows by seed, source group, fault family pair, warm-up mode,
   onset bucket, obstacle geometry bucket, and boundary axis.

## Evidence Gates

The first no-training run should not be asked to prove driver performance. It
should ask whether source-rich data solves the current proof-surface shortage.

Suggested pass gates:

```text
source rows >= 64
candidate plans >= 512
normal near-boundary rows >= 80
wrong-history accepted rows >= 80
accepted fault-family pairs >= 8
accepted seeds >= 8
accepted warm-up modes >= 2
accepted onset buckets >= 3
accepted obstacle geometry buckets >= 8
max seed dominance <= 0.25
max fault-pair dominance <= 0.35
wrong-history success-drop fraction >= 0.80
current_model_fault rows reported separately from proxy rows
future_only rows excluded from evidence gates
```

If these gates fail, the failure should be classified as source generation,
boundary retargeting, wrong-history pairing, or simulator-fidelity limitation.

## Compatibility Issue To Resolve First

Existing v4 extreme route tooling was built around an older behavior generator:

```text
M568 actor + M761 residual head
```

Several source-rich tools require:

```text
--checkpoint
--residual-head
--alpha
```

The current public-gate base is a checkpoint without a required residual-head
wrapper. Therefore the next milestone should be a compatibility audit, not an
immediate run.

The audit should answer:

```text
Can existing source-rich tooling run current public base with alpha=0 safely?
Is a true identity/no-residual head needed?
Which modules already emit the required source geometry and fault metadata?
Which route is smallest: reuse existing v4 route, or implement a current-base
no-residual source-rich sampler?
```

## Guardrail

No mining, replay, actor training, PPO, promotion, private holdout, row
conversion, threshold weakening, or actor-input change occurred.

## Decision

```text
decision: source_rich_extreme_scenario_refresh_design_admit_compatibility_audit
next: m1181-v4-public-base-source-rich-route-compatibility-audit
```
