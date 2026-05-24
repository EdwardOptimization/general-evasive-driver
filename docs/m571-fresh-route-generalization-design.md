# M571 Fresh Route/Generalization Design

## Purpose

M571 defines the next evidence layer for selected scaled BC checkpoint
`BC5660` after the M570 public natural-surface diagnostic pass.

This milestone is design-only:

```text
no training
no PPO
no behavior cloning
no public frozen-source tuning
no checkpoint promotion
```

The goal is to prevent the project from repeatedly optimizing public proof
surfaces. M570 shows that BC5660 repairs the known public L3 regression; M571
asks for fresh route/generalization evidence before any stronger claim.

## Candidate And References

```text
candidate:
  l3_bc5660 = runs/m568_scaled_l3_bc_seed5660/checkpoint.pt

references:
  l0_s3540 = runs/m542_matched_l0_variance_seed3540/checkpoint.pt
  l2_s3540 = runs/m542_matched_l2_variance_seed3540/checkpoint.pt
```

All evaluation must use level-matched env configs:

```text
l0_s3540  -> configs/ppo_m541_matched_l0_variance_4096.json
l2_s3540  -> configs/ppo_m541_matched_l2_variance_4096.json
l3_bc5660 -> configs/ppo_m541_matched_l3_variance_4096.json
```

The actor contract remains:

```text
P0_human_view_no_wheel_no_oracle
```

L2 finite-window stacks remain a reference/teacher capability only and must not
enter the deployed L3 actor.

## M572 Fresh Route Gate

M572 should run one larger route-screen v2 generalization evaluation:

```text
episodes = 256
seed_start = 19560
seed_list = 19560..19815
run_dir = runs/m572_fresh_route_generalization_eval
```

Forbidden seed ranges:

```text
15560..15623  # M556 route-screen family
16560..16623  # M560 route-screen family
17560..17623  # M564 route-screen family
18560..18623  # M569 route-screen family
```

Command:

```bash
PYTHONPATH=src python -m autodrift.route_screen_v2 \
  --checkpoint-policy l0_s3540=runs/m542_matched_l0_variance_seed3540/checkpoint.pt \
  --checkpoint-policy l2_s3540=runs/m542_matched_l2_variance_seed3540/checkpoint.pt \
  --checkpoint-policy l3_bc5660=runs/m568_scaled_l3_bc_seed5660/checkpoint.pt \
  --env-config-policy l0_s3540=configs/ppo_m541_matched_l0_variance_4096.json \
  --env-config-policy l2_s3540=configs/ppo_m541_matched_l2_variance_4096.json \
  --env-config-policy l3_bc5660=configs/ppo_m541_matched_l3_variance_4096.json \
  --candidate-label l3_bc5660 \
  --l0-label l0_s3540 \
  --l2-label l2_s3540 \
  --episodes 256 \
  --seed 19560 \
  --device cpu \
  --run-dir runs/m572_fresh_route_generalization_eval
```

This is not a private paper holdout. It is a fresh non-public route/generalization
gate for engineering direction. If later used repeatedly for repair, it must be
treated as public diagnostic evidence.

## M572 Pass/Fail Rule

M572 is a pass only if all conditions hold:

```text
uses_public_frozen_source_rows = false
seed_list exactly equals 19560..19815
actor contract remains P0_human_view_no_wheel_no_oracle
l3_bc5660 passes the route-screen v2 L0 gate:
  success >= L0 success
  margin >= L0 margin
  collision <= L0 collision + 0.02
l3_bc5660 is L2-competitive:
  success >= L2 success - 0.02
  margin >= L2 margin - 0.05
  collision <= L2 collision + 0.02
no checkpoint promotion is performed
```

M572 fails if BC5660 falls below L0 on success/margin/collision tolerance,
falls outside L2 competitiveness, has metadata/contract drift, or if any public
frozen-source rows are used.

If BC5660 passes L0 but misses L2 competitiveness, classify the result as
`behavior_regression` against the L2 reference and do not proceed to OOD
escalation until the failure is audited.

## OOD Escalation After M572

Only if M572 passes, a later milestone should define moderate OOD route
evaluation configs. The first OOD profile should widen the route distribution
without changing the actor input contract:

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

This OOD profile should be a separate gate, not folded into M572. The M572 task
is to establish fresh same-distribution route generalization first.

## Decision

```text
fresh_route_generalization_design_admit_m572_eval
```

M571 passes as a design milestone because it pre-registers the M572 fresh seed
range, command, pass/fail criteria, and no-promotion boundary before any fresh
route/generalization evaluation is run.

## Next

```text
M572: run the fresh route/generalization evaluation for BC5660 against L0/L2.
```
