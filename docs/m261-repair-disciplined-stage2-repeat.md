# M261 Repair-Disciplined Stage2 Repeat

M261 repeats the M260 4096-step staged PPO escalation on a fresh seed. Actor
inputs are unchanged. No longer PPO was run.

## Setup

Current public-gate base:

```text
runs/m260_m259_to_raw_interpolation/checkpoints/alpha_0_05.pt
```

Fresh stage2 PPO run:

```text
runs/ppo_m261_stage2_repeat_from_m260_seed5228
```

PPO settings:

```text
config = configs/ppo_m248_source_balanced_from_m239_smoke.json
init checkpoint = m260_a050
seed = 5228
total_steps = 4096
device = cuda
```

## Exact Source Gate

The raw repeat improves the M223 source but regresses the protected-key source:

| Policy | M223 source delta | Protected-key source delta |
| --- | ---: | ---: |
| m261_raw | -0.000329 | +0.000007 |

The raw checkpoint is therefore not promotable. Promotion uses interpolation
from M260 toward the raw PPO checkpoint.

Selected interpolation exact-source deltas:

| Policy | Alpha | M223 source delta | Protected-key source delta |
| --- | ---: | ---: | ---: |
| m261_a0_00005 | 0.00005 | -0.000000002279 | +0.000000000000 |
| m261_a0_0001 | 0.00010 | -0.000000031669 | +0.000000000000 |
| m261_a0_0005 | 0.00050 | -0.000000148157 | +0.000000006137 |
| m261_a001 | 0.00100 | -0.000000316006 | +0.000000003069 |
| m261_a0_0025 | 0.00250 | -0.000000829279 | +0.000000018412 |

`m261_a001` is the largest checked candidate that keeps the protected-key source
delta within the `+1e-8` exact-source tolerance while improving M223. The next
alpha, `0.0025`, fails the protected-source tolerance.

## Protected Key

`m261_a001` passes the protected key, but the safe margin remains close to the
normal-margin boundary:

| Policy | Protected pass | Normal margin | Wrong-history margin | Margin gap |
| --- | --- | ---: | ---: | ---: |
| m260_a050 | true | 0.199550 | 0.098920 | 0.100630 |
| m261_a001 | true | 0.199615 | 0.098992 | 0.100624 |
| m239_a750 | false | 0.200336 | 0.099817 | 0.100519 |

## Replay Gates

All public replay gates pass for `m261_a001` versus M260:

| Corpus | Rows | Success drops retained | Normal margin delta | Margin gap delta | Gate pass |
| --- | ---: | ---: | ---: | ---: | --- |
| M183 M168 | 16 | 16 / 16 | +0.000000912 | +0.000000407 | true |
| M183 M170 | 17 | 17 / 17 | +0.000000887 | +0.000000412 | true |
| M193 M189 | 14 | 14 / 14 | +0.000000769 | +0.000000816 | true |
| M212 M204 | 17 | 17 / 17 | +0.000000716 | +0.000000778 | true |
| M223 M219 | 17 | 17 / 17 | +0.000000717 | +0.000000782 | true |

M183/M170 row16 is retained:

```text
row_id = 16
normal_success = true
wrong_history_success = false
normal_margin = 0.000024
wrong_history_margin = -0.005923
margin_gap = 0.005947
```

## Behavior Retention

Behavior is retained on both public behavior seeds:

| Seed | Policy | Success | Termination | Mean clearance margin | Return |
| ---: | --- | ---: | ---: | ---: | ---: |
| 9505 | m260_a050 | 0.8625 | 0.1375 | 1.835353 | 65.964401 |
| 9505 | m261_a001 | 0.8625 | 0.1375 | 1.835353 | 65.964340 |
| 9505 | m261_a001_reset | 0.8500 | 0.1500 | 1.833996 | 64.059404 |
| 9505 | m261_a001_zero_all | 0.8000 | 0.2000 | 1.853241 | 61.043737 |
| 9506 | m260_a050 | 0.8625 | 0.1375 | 1.852870 | 66.240859 |
| 9506 | m261_a001 | 0.8625 | 0.1375 | 1.852870 | 66.240797 |
| 9506 | m261_a001_reset | 0.8500 | 0.1500 | 1.850265 | 64.349369 |
| 9506 | m261_a001_zero_all | 0.8000 | 0.2000 | 1.871149 | 61.306308 |

## Interpretation

M261 is a positive repeat in the narrow promotion sense: an interpolated
candidate passes exact source, row16, replay, protected-key, behavior, and
validator gates.

However, it is weaker than M260. M260 admitted `alpha=0.05`, while M261 admits
only `alpha=0.001`; raw M261 also reintroduces protected-key source regression.
This is evidence of stage2 seed fragility and protected-source pressure, not a
license to move directly to medium PPO.

## Decision

Promote `m261_a001` as the current public-gate base:

```text
runs/m261_m260_to_raw_interpolation/checkpoints/alpha_0_001.pt
```

Next step:

```text
m262-stage2-repeat-fragility-audit
```
