# M572 Fresh Route/Generalization Eval

## Purpose

M572 runs the M571 pre-registered fresh route/generalization gate for selected
scaled BC checkpoint `BC5660`.

This is a fresh non-public route evaluation:

```text
no public frozen-source rows
no training
no PPO
no behavior cloning
no checkpoint promotion
```

## Command

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

## Artifacts

```text
runs/m572_fresh_route_generalization_eval/summary.json
runs/m572_fresh_route_generalization_eval/policy_summary.csv
runs/m572_fresh_route_generalization_eval/episodes.csv
```

The run wrote `768` episode rows plus one CSV header row:

```text
3 policies * 256 episodes = 768 rows
seed_list = 19560..19815
uses_public_frozen_source_rows = false
```

## Aggregate Result

| Policy | Episodes | Success | Collision | Return | Margin Mean | Margin Min |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `l0_s3540` | 256 | 0.050781 | 0.867188 | 21.420736 | -0.044399 | -0.350451 |
| `l2_s3540` | 256 | 0.621094 | 0.378906 | 61.198967 | 1.049135 | -0.317969 |
| `l3_bc5660` | 256 | 0.625000 | 0.375000 | 61.374800 | 1.064947 | -0.309220 |

BC5660 remains L2-competitive and is slightly better than L2 on the three
pre-registered obstacle metrics.

## Gate Deltas

| Comparison | Success Delta | Collision Delta | Margin Delta |
| --- | ---: | ---: | ---: |
| BC5660 - L0 | +0.574219 | -0.492188 | +1.109346 |
| BC5660 - L2 | +0.003906 | -0.003906 | +0.015813 |

Route-screen v2 decision:

```text
would_admit_public_eval = true
selected_candidate_label = l3_bc5660
l2_competitive = true
recommendation = admit_public_eval_l2_competitive
```

## Pass/Fail Check

M572 satisfies every pre-registered condition:

```text
episodes = 256
seed_list = 19560..19815
uses_public_frozen_source_rows = false
P0 actor contract unchanged
BC5660 passes L0 success/margin/collision gate
BC5660 is L2-competitive on success/margin/collision
no promotion performed
```

## Interpretation

M572 strengthens the scaled BC branch beyond public frozen-source diagnostics.
The selected L3 online-GRU student does not just reproduce M570 public-surface
repair; it also matches or slightly exceeds the L2 finite-window reference on a
larger fresh route seed range.

This still does not prove OOD robustness or paper-grade generalization. It
does, however, justify moving to a moderate-OOD route profile design rather than
returning to public frozen-source rows or PPO.

## Decision

```text
fresh_route_generalization_pass_admit_m573_ood_design
```

## Next

```text
M573: design moderate-OOD route/generalization configs and gates.
```
