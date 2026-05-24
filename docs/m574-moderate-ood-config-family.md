# M574 Moderate-OOD Config Family

## Purpose

M574 implements the M573 eval-only moderate-OOD route config family.

This milestone only adds configs and tests:

```text
no route evaluation
no training
no PPO
no behavior cloning
no checkpoint promotion
```

## Added Configs

```text
configs/eval_m574_moderate_ood_l0.json
configs/eval_m574_moderate_ood_l2.json
configs/eval_m574_moderate_ood_l3.json
```

Each config preserves its M541 parent PPO section exactly:

```text
L0 -> configs/ppo_m541_matched_l0_variance_4096.json
L2 -> configs/ppo_m541_matched_l2_variance_4096.json
L3 -> configs/ppo_m541_matched_l3_variance_4096.json
```

The level-specific history contract is unchanged:

| Level | Actor Encoder | History Length | Actor History | Baseline Level |
| --- | --- | ---: | ---: | --- |
| L0 | `mlp` | 1 | 1 | `L0_current_observation` |
| L2 | `temporal_gru` | 4 | 4 | `L2_finite_window` |
| L3 | `human_view_online_gru` | 1 | 1 | `L3_online_gru` |

All three configs keep the P0 no-wheel/no-oracle input contract.

## OOD Env Deltas

The same M573-approved env deltas are applied to all three configs:

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

All other env fields match the M541 parent except the intended per-level
`history_length` difference.

## Tests

Focused validation:

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
  python -m pytest -q tests/test_history_baseline_configs.py

36 passed
```

The added tests verify:

```text
PPO sections equal M541 parents exactly
L0/L2/L3 history contracts are preserved
OOD env deltas match M573 exactly
OOD distributions are shared across levels except history_length
configs load through load_env_config for route-screen v2
```

## Decision

```text
moderate_ood_config_family_pass_admit_m575_eval
```

M574 passes as an infrastructure milestone because the eval-only config family
is implemented and machine-checked without evaluation, training, promotion,
actor-input changes, or unapproved per-level env differences.

## Next

```text
M575: run moderate-OOD route/generalization eval for BC5660 versus L0/L2.
```
