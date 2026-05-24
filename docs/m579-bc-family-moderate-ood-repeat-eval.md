# M579 BC Family Moderate-OOD Repeat Eval

## Purpose

M579 runs the M577 pre-registered moderate-OOD repeat for the scaled BC seed
family:

```text
l3_bc5660
l3_bc5661
l3_bc5662
```

This is an OOD family-stability diagnostic:

```text
no public frozen-source rows
no training
no PPO
no behavior cloning
no checkpoint promotion
```

## Artifacts

```text
runs/m579_bc_family_moderate_ood_repeat_eval/summary.json
runs/m579_bc_family_moderate_ood_repeat_eval/policy_summary.csv
runs/m579_bc_family_moderate_ood_repeat_eval/episodes.csv
```

The run wrote:

```text
5 policies * 256 episodes = 1280 rows
seed_list = 22560..22815
uses_public_frozen_source_rows = false
```

## Aggregate Result

| Policy | Episodes | Success | Collision | Return | Margin Mean | Margin Min |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `l0_s3540` | 256 | 0.062500 | 0.824219 | 21.366824 | 0.016726 | -0.409955 |
| `l2_s3540` | 256 | 0.574219 | 0.425781 | 57.422399 | 0.913270 | -0.362754 |
| `l3_bc5660` | 256 | 0.582031 | 0.417969 | 57.743462 | 0.921253 | -0.360175 |
| `l3_bc5661` | 256 | 0.574219 | 0.425781 | 57.403122 | 0.914780 | -0.362735 |
| `l3_bc5662` | 256 | 0.582031 | 0.417969 | 57.754128 | 0.920871 | -0.360740 |

All three BC seeds are L0-safe and OOD-L2-competitive. BC5660 and BC5662
slightly exceed L2 on success, collision, return, and margin. BC5661 matches L2
success/collision and slightly improves mean margin.

## BC-vs-L2 Deltas

| Candidate | Success Delta | Collision Delta | Margin Delta | OOD-L2 Competitive |
| --- | ---: | ---: | ---: | --- |
| `l3_bc5660` | +0.007812 | -0.007812 | +0.007984 | true |
| `l3_bc5661` | +0.000000 | +0.000000 | +0.001511 | true |
| `l3_bc5662` | +0.007812 | -0.007812 | +0.007601 | true |

Manual M577/M579 collision check:

```text
all BC collision deltas <= L2 collision + 0.05
```

## Pass/Fail Check

M579 satisfies every pre-registered condition:

```text
episodes = 256
seed_list = 22560..22815
uses_public_frozen_source_rows = false
BC5660 passes L0 and OOD-L2 gates
3 of 3 BC seeds pass L0 and OOD-L2 gates
BC-vs-L2 collision deltas are computed
no promotion performed
```

## Interpretation

M579 substantially strengthens the scaled BC branch:

```text
BC5660 is not a lucky single seed.
All three scaled BC seeds pass fresh route and moderate-OOD repeat gates.
L3 online-GRU students can match the L2 finite-window teacher on these route
generalization diagnostics without L2 stack leakage.
```

This still does not justify immediate promotion. The next evidence gap is
mechanistic: whether the recurrent L3 branch actually uses its hidden
command-response state in deployment-like rollouts.

## Decision

```text
bc_family_ood_repeat_pass_admit_m580_audit
```

## Next

```text
M580: audit BC family generalization evidence and choose recurrent-dependence
ablation/proof gates.
```
