# M575 Moderate-OOD Route/Generalization Eval

## Purpose

M575 runs the M573/M574 pre-registered moderate-OOD route/generalization gate
for selected scaled BC checkpoint `BC5660`.

This is an OOD diagnostic gate:

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
  --env-config-policy l0_s3540=configs/eval_m574_moderate_ood_l0.json \
  --env-config-policy l2_s3540=configs/eval_m574_moderate_ood_l2.json \
  --env-config-policy l3_bc5660=configs/eval_m574_moderate_ood_l3.json \
  --candidate-label l3_bc5660 \
  --l0-label l0_s3540 \
  --l2-label l2_s3540 \
  --episodes 256 \
  --seed 20560 \
  --device cpu \
  --run-dir runs/m575_moderate_ood_route_generalization_eval \
  --collision-tolerance 0.02 \
  --l2-success-tolerance 0.05 \
  --l2-margin-tolerance 0.10
```

## Artifacts

```text
runs/m575_moderate_ood_route_generalization_eval/summary.json
runs/m575_moderate_ood_route_generalization_eval/policy_summary.csv
runs/m575_moderate_ood_route_generalization_eval/episodes.csv
```

The run wrote:

```text
3 policies * 256 episodes = 768 rows
seed_list = 20560..20815
uses_public_frozen_source_rows = false
```

## Aggregate Result

| Policy | Episodes | Success | Collision | Return | Margin Mean | Margin Min |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `l0_s3540` | 256 | 0.046875 | 0.832031 | 21.777546 | 0.030985 | -0.398182 |
| `l2_s3540` | 256 | 0.628906 | 0.371094 | 61.796892 | 1.036858 | -0.317809 |
| `l3_bc5660` | 256 | 0.628906 | 0.371094 | 61.804108 | 1.042773 | -0.312628 |

BC5660 matches L2 success and collision exactly, has slightly higher return and
mean clearance margin, and remains far ahead of L0.

## Gate Deltas

| Comparison | Success Delta | Collision Delta | Margin Delta |
| --- | ---: | ---: | ---: |
| BC5660 - L0 | +0.582031 | -0.460938 | +1.011787 |
| BC5660 - L2 | +0.000000 | +0.000000 | +0.005914 |

Route-screen v2 decision:

```text
would_admit_public_eval = true
selected_candidate_label = l3_bc5660
l2_competitive = true
recommendation = admit_public_eval_l2_competitive
```

Manual M573/M575 collision check:

```text
BC5660 collision - L2 collision = 0.000000 <= 0.05
```

## Pass/Fail Check

M575 satisfies every pre-registered condition:

```text
episodes = 256
seed_list = 20560..20815
uses_public_frozen_source_rows = false
all policies use eval_m574_moderate_ood_* configs
BC5660 passes L0 success/margin/collision gate
BC5660 is OOD-L2-competitive on success/margin/collision
no promotion performed
```

## Interpretation

This is a strong scaled-BC result. BC5660 now matches or slightly exceeds the L2
finite-window reference on:

```text
M570 public natural surfaces
M572 fresh same-distribution route seeds
M575 moderate-OOD route seeds
```

The result still should not be promoted directly:

- it is one selected BC seed, not the full BC seed family;
- it is one OOD seed block, not a repeated OOD distribution;
- it shows L3 can distill L2 behavior well, but does not by itself prove
  self-identification beyond L2-like command-response imitation;
- no recurrent ablation or wrong-history OOD gate has been run for this branch.

## Decision

```text
moderate_ood_route_generalization_pass_admit_m576_audit
```

## Next

```text
M576: audit M570/M572/M575 evidence and design the next escalation.
```
