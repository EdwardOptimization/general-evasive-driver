# M240 Interpolation-Guarded PPO Repeat From M224

M240 repeats the M237 trajectory-anchored PPO recipe on a fresh seed, then
requires post-PPO checkpoint interpolation before any candidate can be accepted.
This tests whether the M239 line-search promotion is repeatable.

Actor inputs are unchanged.

## Setup

Initial checkpoint:

```text
runs/m224_m219_actor_coupling_snippet_pref_anchor100_s10_lr5e5_seed10063/optimized_checkpoint.pt
```

Config:

```text
configs/ppo_m240_trajectory_anchor_from_m224_smoke.json
```

Raw PPO checkpoint:

```text
runs/ppo_m240_trajectory_anchor_from_m224_seed5222/checkpoint.pt
```

Interpolation sweep:

```text
runs/m240_m224_to_raw_interpolation
```

## Raw PPO Training

Training metrics:

| Step | Rollout return mean | Reward mean | Episodes | Built-in eval termination | Outcome loss | Baseline anchor loss | Snippet anchor loss | Trajectory anchor loss |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1024 | 69.949 | 0.998 | 10 | 0.2000 | 0.238775 | 0.00000378 | 0.000000031 | 0.000000109 |

The trajectory anchor path was active, and the raw run completed successfully.

## Fixed Objective

M232 combined objective:

| Policy | Alpha | Loss |
| --- | ---: | ---: |
| m224_10063 | 0.00 | 0.246506 |
| m240_a100 | 0.10 | 0.246507 |
| m240_a250 | 0.25 | 0.246509 |
| m240_a500 | 0.50 | 0.246512 |
| m240_a750 | 0.75 | 0.246516 |
| m240_a1000 | 1.00 | 0.246520 |

M223 objective:

| Policy | Alpha | Loss |
| --- | ---: | ---: |
| m224_10063 | 0.00 | 0.209824 |
| m240_a100 | 0.10 | 0.209824 |
| m240_a250 | 0.25 | 0.209823 |
| m240_a500 | 0.50 | 0.209822 |
| m240_a750 | 0.75 | 0.209822 |
| m240_a1000 | 1.00 | 0.209821 |

The repeat is not aligned with the combined M232 objective. It slightly improves
the old M223 objective but regresses the M232 corpus that includes the protected
key. This fails the M240 promotion standard.

## Critical Proof Gates

M183 M170 replay:

| Policy | Alpha | Gate pass | Drops | Row 16 normal margin |
| --- | ---: | --- | ---: | ---: |
| m240_a100 | 0.10 | true | 17 / 17 | 0.000156 |
| m240_a250 | 0.25 | true | 17 / 17 | 0.000232 |
| m240_a500 | 0.50 | true | 17 / 17 | 0.000359 |
| m240_a750 | 0.75 | true | 17 / 17 | 0.000488 |
| m240_a1000 | 1.00 | true | 17 / 17 | 0.000619 |

Protected key `9944|perturbed|28|28`:

| Policy | Alpha | Pass | Normal margin | Wrong-history margin | Margin gap |
| --- | ---: | --- | ---: | ---: | ---: |
| m224_10063 | 0.00 | true | 0.186385 | 0.086925 | 0.099460 |
| m240_a100 | 0.10 | true | 0.188511 | 0.088659 | 0.099852 |
| m240_a250 | 0.25 | true | 0.191734 | 0.091451 | 0.100283 |
| m240_a500 | 0.50 | true | 0.196687 | 0.096233 | 0.100454 |
| m240_a750 | 0.75 | false | 0.201379 | 0.101271 | 0.100108 |
| m240_a1000 | 1.00 | false | 0.205768 | 0.106742 | 0.099025 |

So the retention guard is repeatable: a moderate alpha can preserve the known
proof surfaces.

## Full Proof Retention For Alpha 0.5

`m240_a500` passes the broader replay surfaces:

| Corpus | Rows | Drops | Normal margin delta | Margin gap delta | Gate pass |
| --- | ---: | ---: | ---: | ---: | --- |
| M183 M168 | 16 | 16 / 16 | 0.000317 | 0.000050 | true |
| M183 M170 | 17 | 17 / 17 | 0.000314 | 0.000051 | true |
| M193 M189 | 14 | 14 / 14 | 0.000277 | 0.000102 | true |
| M212 M204 | 17 | 17 / 17 | 0.000276 | 0.000097 | true |
| M223 M219 | 17 | 17 / 17 | 0.000276 | 0.000098 | true |

## Behavior Diagnostic

`m240_a500` retains broad behavior on both public behavior seeds.

| Seed | Policy | Success | Termination | Mean clearance margin |
| ---: | --- | ---: | ---: | ---: |
| 9505 | m224_10063 | 0.8625 | 0.1375 | 1.835461 |
| 9505 | m240_a500 | 0.8625 | 0.1375 | 1.835553 |
| 9505 | m240_a500_reset | 0.8500 | 0.1500 | 1.834097 |
| 9505 | m240_a500_zero_all | 0.8000 | 0.2000 | 1.853317 |
| 9506 | m224_10063 | 0.8625 | 0.1375 | 1.852989 |
| 9506 | m240_a500 | 0.8625 | 0.1375 | 1.853077 |
| 9506 | m240_a500_reset | 0.8500 | 0.1500 | 1.850369 |
| 9506 | m240_a500_zero_all | 0.8000 | 0.2000 | 1.871232 |

## Interpretation

M240 separates two issues:

- The interpolation guard is repeatable for proof retention.
- The PPO update direction is seed-fragile with respect to the combined M232
  objective.

This means M239 is still the current public-gate base, but the M237/M240 recipe
should not be lengthened yet. The next blocker is not proof retention; it is
making the PPO update direction reliably improve the combined proof objective.

Failure taxonomy:

```text
seed_fragility
promotion_gate_failure
```

## Decision

M240 is rejected.

Current public-gate base remains:

```text
runs/m239_m224_to_m237_interpolation/checkpoints/alpha_0_5.pt
```

Next step:

```text
m241-trajectory-ppo-seed-direction-audit
```

M241 should audit why seed 5221 improved the combined objective while seed 5222
regressed it, and decide whether the next repair is a fixed-objective prefilter,
a lower-variance PPO recipe, or a different update objective.
