# M577 BC Family Generalization Repeat Design

## Purpose

M577 designs the next escalation after M576 audited positive BC5660 evidence.

The question is now:

```text
Is the scaled L2-to-L3 BC result stable across BC optimizer seeds,
or did route/public/OOD evidence select one lucky student?
```

M577 is design-only:

```text
no evaluation
no training
no PPO
no behavior cloning
no checkpoint promotion
```

## Policies

References:

```text
l0_s3540 = runs/m542_matched_l0_variance_seed3540/checkpoint.pt
l2_s3540 = runs/m542_matched_l2_variance_seed3540/checkpoint.pt
```

Candidates:

```text
l3_bc5660 = runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
l3_bc5661 = runs/m568_scaled_l3_bc_seed5661/checkpoint.pt
l3_bc5662 = runs/m568_scaled_l3_bc_seed5662/checkpoint.pt
```

All candidates keep:

```text
P0_human_view_no_wheel_no_oracle
L3_online_gru
ppo_used = false
promoted = false
```

## M578 Fresh Route Repeat

M578 should run a same-distribution fresh route repeat with all three BC seeds:

```text
episodes = 256
seed_start = 21560
seed_list = 21560..21815
run_dir = runs/m578_bc_family_fresh_route_repeat_eval
```

Command:

```bash
PYTHONPATH=src python -m autodrift.route_screen_v2 \
  --checkpoint-policy l0_s3540=runs/m542_matched_l0_variance_seed3540/checkpoint.pt \
  --checkpoint-policy l2_s3540=runs/m542_matched_l2_variance_seed3540/checkpoint.pt \
  --checkpoint-policy l3_bc5660=runs/m568_scaled_l3_bc_seed5660/checkpoint.pt \
  --checkpoint-policy l3_bc5661=runs/m568_scaled_l3_bc_seed5661/checkpoint.pt \
  --checkpoint-policy l3_bc5662=runs/m568_scaled_l3_bc_seed5662/checkpoint.pt \
  --env-config-policy l0_s3540=configs/ppo_m541_matched_l0_variance_4096.json \
  --env-config-policy l2_s3540=configs/ppo_m541_matched_l2_variance_4096.json \
  --env-config-policy l3_bc5660=configs/ppo_m541_matched_l3_variance_4096.json \
  --env-config-policy l3_bc5661=configs/ppo_m541_matched_l3_variance_4096.json \
  --env-config-policy l3_bc5662=configs/ppo_m541_matched_l3_variance_4096.json \
  --candidate-label l3_bc5660 \
  --candidate-label l3_bc5661 \
  --candidate-label l3_bc5662 \
  --l0-label l0_s3540 \
  --l2-label l2_s3540 \
  --episodes 256 \
  --seed 21560 \
  --device cpu \
  --run-dir runs/m578_bc_family_fresh_route_repeat_eval
```

M578 pass rule:

```text
uses_public_frozen_source_rows = false
seed_list exactly equals 21560..21815
all three candidates use M541 L3 env config
BC5660 remains L0-safe and L2-competitive
at least 2 of 3 BC seeds are L0-safe and L2-competitive
no candidate has actor-contract or metadata drift
no checkpoint promotion is performed
```

Same-distribution L2-competitive tolerances:

```text
success >= L2 success - 0.02
margin >= L2 margin - 0.05
collision <= L2 collision + 0.02
```

`route_screen_v2` checks L2 success/margin and the L0 collision tolerance. The
M578 documentation must additionally compute the BC-vs-L2 collision deltas for
all candidates.

## M579 Moderate-OOD Repeat

M579 should run only if M578 passes. It should use the M574 eval-only OOD
configs with fresh OOD route seeds:

```text
episodes = 256
seed_start = 22560
seed_list = 22560..22815
run_dir = runs/m579_bc_family_moderate_ood_repeat_eval
```

OOD command shape:

```bash
PYTHONPATH=src python -m autodrift.route_screen_v2 \
  --checkpoint-policy l0_s3540=runs/m542_matched_l0_variance_seed3540/checkpoint.pt \
  --checkpoint-policy l2_s3540=runs/m542_matched_l2_variance_seed3540/checkpoint.pt \
  --checkpoint-policy l3_bc5660=runs/m568_scaled_l3_bc_seed5660/checkpoint.pt \
  --checkpoint-policy l3_bc5661=runs/m568_scaled_l3_bc_seed5661/checkpoint.pt \
  --checkpoint-policy l3_bc5662=runs/m568_scaled_l3_bc_seed5662/checkpoint.pt \
  --env-config-policy l0_s3540=configs/eval_m574_moderate_ood_l0.json \
  --env-config-policy l2_s3540=configs/eval_m574_moderate_ood_l2.json \
  --env-config-policy l3_bc5660=configs/eval_m574_moderate_ood_l3.json \
  --env-config-policy l3_bc5661=configs/eval_m574_moderate_ood_l3.json \
  --env-config-policy l3_bc5662=configs/eval_m574_moderate_ood_l3.json \
  --candidate-label l3_bc5660 \
  --candidate-label l3_bc5661 \
  --candidate-label l3_bc5662 \
  --l0-label l0_s3540 \
  --l2-label l2_s3540 \
  --episodes 256 \
  --seed 22560 \
  --device cpu \
  --run-dir runs/m579_bc_family_moderate_ood_repeat_eval \
  --collision-tolerance 0.02 \
  --l2-success-tolerance 0.05 \
  --l2-margin-tolerance 0.10
```

M579 OOD pass rule:

```text
BC5660 remains L0-safe and OOD-L2-competitive
at least 2 of 3 BC seeds are L0-safe and OOD-L2-competitive
collision <= L2 collision + 0.05 is checked manually for each candidate
no promotion is performed
```

## Interpretation Rules

If all three BC seeds pass, the BC branch has strong seed-family evidence and
the next step should be recurrent-dependence ablations.

If exactly two pass and BC5660 passes, continue but document seed sensitivity
before any promotion decision.

If only BC5660 passes, classify the result as `seed_fragility`; promotion and
PPO remain blocked.

If BC5660 fails, classify the result as `behavior_regression`; audit before
running OOD or PPO.

## Decision

```text
bc_family_repeat_design_admit_m578_fresh_route_repeat
```

M577 passes because it pre-registers BC seed-family repeat commands, seed
blocks, pass/fail thresholds, and no-promotion boundaries before evaluation.

## Next

```text
M578: run the BC seed-family fresh route repeat.
```
