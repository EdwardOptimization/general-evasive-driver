# M569 Scaled BC Route-Screen Selection

## Purpose

M569 runs route-screen v2 on the scaled L3 behavior-cloning seed family from
M568.

This milestone is a route-screen gate only. It does not run public
frozen-source diagnostics, PPO, or checkpoint promotion.

## Command

```text
PYTHONPATH=src python -m autodrift.route_screen_v2 \
  --checkpoint-policy L0=runs/m542_matched_l0_variance_seed3540/checkpoint.pt \
  --checkpoint-policy L2=runs/m542_matched_l2_variance_seed3540/checkpoint.pt \
  --checkpoint-policy BC5660=runs/m568_scaled_l3_bc_seed5660/checkpoint.pt \
  --checkpoint-policy BC5661=runs/m568_scaled_l3_bc_seed5661/checkpoint.pt \
  --checkpoint-policy BC5662=runs/m568_scaled_l3_bc_seed5662/checkpoint.pt \
  --env-config-policy L0=configs/ppo_m541_matched_l0_variance_4096.json \
  --env-config-policy L2=configs/ppo_m541_matched_l2_variance_4096.json \
  --env-config-policy BC5660=configs/ppo_m541_matched_l3_variance_4096.json \
  --env-config-policy BC5661=configs/ppo_m541_matched_l3_variance_4096.json \
  --env-config-policy BC5662=configs/ppo_m541_matched_l3_variance_4096.json \
  --candidate-label BC5660 \
  --candidate-label BC5661 \
  --candidate-label BC5662 \
  --l0-label L0 \
  --l2-label L2 \
  --episodes 64 \
  --seed 18560 \
  --device cpu \
  --run-dir runs/m569_scaled_bc_route_screen_selection
```

## Result

The runner reports:

```text
uses_public_frozen_source_rows = false
would_admit_public_eval = true
selected_candidate_label = BC5660
```

| Policy | Success | Collision | Margin Mean | Return Mean |
| --- | ---: | ---: | ---: | ---: |
| L0 | 0.062500 | 0.828125 | 0.011929 | 24.174413 |
| L2 | 0.671875 | 0.328125 | 0.936128 | 66.343841 |
| BC5660 | 0.671875 | 0.328125 | 0.950870 | 66.286370 |
| BC5661 | 0.671875 | 0.328125 | 0.939212 | 66.329780 |
| BC5662 | 0.671875 | 0.328125 | 0.949250 | 66.302692 |

All three scaled BC seeds pass route-screen v2:

```text
passes_l0_success = true
passes_l0_margin = true
passes_l0_collision_tolerance = true
l2_competitive = true
```

The selected checkpoint is `BC5660` because it has the best clearance margin
among candidates:

```text
BC5660 margin - L2 = +0.014743
BC5662 margin - L2 = +0.013123
BC5661 margin - L2 = +0.003085
```

## Interpretation

M569 confirms that the scaled BC family did not lose the M564 closed-loop route
behavior:

```text
all three BC seeds match L2 on success and collision
all three are slightly above L2 on mean clearance margin
all three strongly beat L0 on success, collision, and margin
```

This admits a public diagnostic repeat for the selected scaled checkpoint, but
does not promote it.

## Decision

```text
scaled_bc_route_screen_pass_admit_m570_public_surface_eval
```

M569 passes because at least one scaled BC candidate clears route-screen v2 on
fresh seed `18560`; in fact all three candidates pass. `BC5660` is selected for
public diagnostics.

## Next

```text
M570: evaluate BC5660 on the four public frozen-source natural surfaces.
```
