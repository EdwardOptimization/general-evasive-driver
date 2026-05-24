# M578 BC Family Fresh Route Repeat Eval

## Purpose

M578 runs the M577 pre-registered fresh same-distribution route repeat for the
scaled BC seed family:

```text
l3_bc5660
l3_bc5661
l3_bc5662
```

This is a family-stability diagnostic:

```text
no public frozen-source rows
no training
no PPO
no behavior cloning
no checkpoint promotion
```

## Artifacts

```text
runs/m578_bc_family_fresh_route_repeat_eval/summary.json
runs/m578_bc_family_fresh_route_repeat_eval/policy_summary.csv
runs/m578_bc_family_fresh_route_repeat_eval/episodes.csv
```

The run wrote:

```text
5 policies * 256 episodes = 1280 rows
seed_list = 21560..21815
uses_public_frozen_source_rows = false
```

## Aggregate Result

| Policy | Episodes | Success | Collision | Return | Margin Mean | Margin Min |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `l0_s3540` | 256 | 0.046875 | 0.835938 | 21.450156 | -0.014865 | -0.344895 |
| `l2_s3540` | 256 | 0.671875 | 0.328125 | 64.025739 | 0.978128 | -0.279142 |
| `l3_bc5660` | 256 | 0.675781 | 0.324219 | 64.228829 | 0.992939 | -0.273033 |
| `l3_bc5661` | 256 | 0.671875 | 0.328125 | 64.014296 | 0.982097 | -0.280793 |
| `l3_bc5662` | 256 | 0.675781 | 0.324219 | 64.237126 | 0.991177 | -0.274170 |

All three BC seeds are L0-safe and L2-competitive. BC5660 and BC5662 slightly
exceed L2 on success, collision, return, and margin. BC5661 matches L2
success/collision and slightly improves margin.

## BC-vs-L2 Deltas

| Candidate | Success Delta | Collision Delta | Margin Delta | Route-Screen L2 Competitive |
| --- | ---: | ---: | ---: | --- |
| `l3_bc5660` | +0.003906 | -0.003906 | +0.014811 | true |
| `l3_bc5661` | +0.000000 | +0.000000 | +0.003969 | true |
| `l3_bc5662` | +0.003906 | -0.003906 | +0.013049 | true |

Route-screen v2 selected `l3_bc5660` because it has the best lexicographic
combination of success, margin, collision, and return.

## Pass/Fail Check

M578 satisfies every pre-registered condition:

```text
episodes = 256
seed_list = 21560..21815
uses_public_frozen_source_rows = false
BC5660 passes L0 and L2 gates
3 of 3 BC seeds pass L0 and L2 gates
BC-vs-L2 collision deltas are computed
no promotion performed
```

## Interpretation

M578 reduces the main concern from M576: BC5660 is not the only scaled BC seed
that works on fresh same-distribution route seeds. The family is stable on this
fresh route block.

This still does not prove moderate-OOD family stability, so the next step is the
pre-registered M579 OOD family repeat.

## Decision

```text
bc_family_fresh_route_repeat_pass_admit_m579_ood_repeat
```

## Next

```text
M579: run BC seed-family moderate-OOD repeat.
```
