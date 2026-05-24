# M573 Moderate-OOD Route/Generalization Design

## Purpose

M573 designs the next evidence layer after BC5660 passed:

```text
M569 route-screen selection
M570 public natural-surface diagnostic
M572 fresh 256-episode route/generalization gate
```

The next question is whether BC5660 remains useful outside the exact training
route distribution. M573 is design-only: it does not create configs, run
evaluation, train, or promote.

## Boundary

Allowed:

```text
eval-only env config copies for L0/L2/L3
fresh OOD seed range
pre-registered pass/fail criteria
diagnostic comparison against L0 and L2
```

Forbidden:

```text
PPO
behavior cloning
checkpoint weight changes
actor input changes
L2 stack leakage into L3 deployment
public frozen-source rows
promotion from a single OOD gate
```

## Config Family For M574

M574 should add eval-only config copies:

```text
configs/eval_m574_moderate_ood_l0.json
configs/eval_m574_moderate_ood_l2.json
configs/eval_m574_moderate_ood_l3.json
```

Each config should preserve its parent history/actor level:

```text
l0: history_length = 1, history_baseline_level = L0_current_observation
l2: history_length = 4, history_baseline_level = L2_finite_window
l3: history_length = 1, history_baseline_level = L3_online_gru
```

Each config must preserve:

```text
obstacle_relative_velocity_mode = zero
action_history_mode = full
road_lookahead_count = 8
obstacle_slots = 4
P0_human_view_no_wheel_no_oracle actor contract
```

The configs are for evaluation only. The `ppo` section may keep parent trainer
fields for loader compatibility, but M574/M575 must not run training.

## Moderate-OOD Env Deltas

M574 should apply the same OOD env deltas to L0/L2/L3 except for the expected
history-length fields.

```text
speed_range:                  [14.5, 20.0]
friction_step.mu_range:       [0.12, 1.00]
randomization.mu_range:       [0.12, 0.72]
mass_scale_range:             [0.80, 1.45]
cg_shift_range:               [-0.20, 0.20]
inertia_scale_range:          [0.75, 1.45]
tire_stiffness_scale_range:   [0.35, 1.50]
drive_scale_range:            [0.50, 1.40]
brake_scale_range:            [0.35, 1.40]
actuator_tau_scale_range:     [1.00, 4.80]
obstacle.distance_range:      [4.0, 26.0]
obstacle.half_width_range:    [0.60, 1.55]
obstacle.max_threshold_score: 0.60
perception_reveal_distance:   5.5
```

Rationale:

- Lower `mu` and wider tire/brake/actuator ranges test hidden dynamics
  generalization.
- Higher speed and wider obstacle geometry stress route timing.
- The reveal distance change makes the emergency phase slightly tighter without
  changing perception input semantics.
- The profile is moderate, not extreme; the goal is a first OOD diagnostic, not
  a maximal failure search.

## M575 OOD Eval Protocol

M575 should run route-screen v2 on fresh OOD route seeds:

```text
episodes = 256
seed_start = 20560
seed_list = 20560..20815
run_dir = runs/m575_moderate_ood_route_generalization_eval
```

Prior route seed starts are forbidden:

```text
15560
16560
17560
18560
19560
```

M575 command shape:

```bash
PYTHONPATH=src python -m autodrift.route_screen_v2 \
  --checkpoint-policy l0_s3540=runs/m542_matched_l0_variance_seed3540/checkpoint.pt \
  --checkpoint-policy l2_s3540=runs/m542_matched_l2_variance_seed3540/checkpoint.pt \
  --checkpoint-policy l3_bc5660=runs/m568_scaled_l3_bc_seed5660/checkpoint.pt \
  --env-config-policy l0_s3540=configs/eval_m574_moderate_ood_l0.json \
  --env-config-policy l2_s3540=configs/eval_m574_moderate_ood_l2.json \
  --env-config-policy l3_bc5660=configs/eval_m574_moderate_ood_l3.json \
  --candidate-label l3_bc5660 \
  --l0-label l0_s3540 \
  --l2-label l2_s3540 \
  --episodes 256 \
  --seed 20560 \
  --device cpu \
  --run-dir runs/m575_moderate_ood_route_generalization_eval
```

## M575 Pass/Fail Rule

M575 is a moderate-OOD diagnostic pass only if:

```text
uses_public_frozen_source_rows = false
seed_list exactly equals 20560..20815
actor contract remains P0_human_view_no_wheel_no_oracle
all three policies use M574 eval-only configs
BC5660 passes the L0 gate:
  success >= L0 success
  margin >= L0 margin
  collision <= L0 collision + 0.02
BC5660 is OOD-L2-competitive:
  success >= L2 success - 0.05
  margin >= L2 margin - 0.10
  collision <= L2 collision + 0.05
no checkpoint promotion is performed
```

The L2 tolerances are wider than M572 because M575 deliberately shifts the
distribution. If BC5660 passes L0 but misses OOD-L2 competitiveness, classify it
as an L2-to-L3 distillation/OOD gap and do not proceed to PPO or promotion
without an audit.

## Decision

```text
moderate_ood_route_design_admit_m574_config_family
```

M573 passes because it fixes the OOD config deltas, seed range, command shape,
and pass/fail criteria before any OOD configs or evaluation are created.

## Next

```text
M574: implement the moderate-OOD eval-only config family and tests.
```
