# M564 BC Route-Screen V2 Smoke

## Purpose

M564 evaluates whether the M563 offline behavior-cloning checkpoint transfers
from teacher-action MSE to closed-loop route behavior.

This is a route-screen v2 diagnostic. It does not promote a checkpoint.

## Command

```text
PYTHONPATH=src python -m autodrift.route_screen_v2 \
  --checkpoint-policy L0=runs/m542_matched_l0_variance_seed3540/checkpoint.pt \
  --checkpoint-policy L2=runs/m542_matched_l2_variance_seed3540/checkpoint.pt \
  --checkpoint-policy M563_BC=runs/m563_l3_behavior_cloning_smoke/checkpoint.pt \
  --env-config-policy L0=configs/ppo_m541_matched_l0_variance_4096.json \
  --env-config-policy L2=configs/ppo_m541_matched_l2_variance_4096.json \
  --env-config-policy M563_BC=configs/ppo_m541_matched_l3_variance_4096.json \
  --candidate-label M563_BC \
  --l0-label L0 \
  --l2-label L2 \
  --episodes 64 \
  --seed 17560 \
  --device cpu \
  --run-dir runs/m564_bc_route_screen_v2_smoke
```

Artifacts:

```text
runs/m564_bc_route_screen_v2_smoke/summary.json
runs/m564_bc_route_screen_v2_smoke/policy_summary.csv
runs/m564_bc_route_screen_v2_smoke/episodes.csv
```

The runner reports:

```text
uses_public_frozen_source_rows = false
would_admit_public_eval = true
selected_candidate_label = M563_BC
```

## Result

| policy | success | collision | margin mean | return mean |
| --- | ---: | ---: | ---: | ---: |
| L0 | 0.031250 | 0.875000 | -0.001880 | 19.787836 |
| L2 | 0.656250 | 0.343750 | 0.787116 | 62.527744 |
| M563_BC | 0.656250 | 0.343750 | 0.770803 | 62.557827 |

Candidate deltas:

```text
M563_BC success - L0 = +0.625000
M563_BC collision - L0 = -0.531250
M563_BC margin - L0 = +0.772682
M563_BC success - L2 = +0.000000
M563_BC margin - L2 = -0.016314
```

Gate outcome:

```text
passes_l0_success = true
passes_l0_margin = true
passes_l0_collision_tolerance = true
l2_competitive = true
recommendation = admit_public_eval_l2_competitive
```

## Interpretation

This is the first closed-loop positive result for the L2-to-L3 distillation
branch:

```text
M563_BC matches L2 success and collision on this fresh route-screen seed.
M563_BC is slightly below L2 margin but within route-screen v2 tolerance.
M563_BC is far above L0 on success, collision, and clearance margin.
```

This still is not a promotion. It only admits public frozen-source diagnostics.
The checkpoint was trained on small smoke corpora, so the next result must check
whether the route-screen pass survives public natural surfaces.

## Decision

```text
bc_route_screen_v2_pass_admit_m565_public_surface_eval
```

M564 passes because the M563 BC checkpoint clears route-screen v2 against L0 and
is L2-competitive on fresh selection seed `17560`, without public frozen-source
rows or checkpoint promotion.

## Next

```text
M565: evaluate M563_BC on the four public frozen-source natural surfaces used by M543/M550.
```

M565 remains public diagnostic evidence only. It can admit a larger distillation
corpus or matched repeat, but it cannot promote the checkpoint by itself.
