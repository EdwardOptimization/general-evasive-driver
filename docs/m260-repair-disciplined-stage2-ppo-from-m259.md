# M260 Repair-Disciplined Stage2 PPO From M259

M260 runs the first short staged PPO escalation after the positive M258/M259
trajectory-anchored repair smokes. Actor inputs are unchanged. No long PPO was
run.

## Setup

Current public-gate base:

```text
runs/m259_m258_to_projection_interpolation/checkpoints/alpha_0_01.pt
```

Stage2 PPO run:

```text
runs/ppo_m260_stage2_from_m259_seed5227
```

PPO settings:

```text
config = configs/ppo_m248_source_balanced_from_m239_smoke.json
init checkpoint = m259_a010
seed = 5227
total_steps = 4096
device = cuda
```

## Exact Source Gate

Unlike M254/M259 raw PPO, the M260 raw 4096-step checkpoint improves both
sources:

| Policy | M223 source delta | Protected-key source delta |
| --- | ---: | ---: |
| m260_raw | -0.000382 | -0.000002 |

The full raw checkpoint passes exact source, but it does not pass the protected
key after public proof replay. Therefore promotion uses interpolation from
M259 toward raw.

Selected interpolation exact-source deltas:

| Policy | Alpha | M223 source delta | Protected-key source delta |
| --- | ---: | ---: | ---: |
| m260_a010 | 0.01 | -0.000003893900 | -0.000000058303 |
| m260_a025 | 0.025 | -0.000009746757 | -0.000000147292 |
| m260_a050 | 0.05 | -0.000019486752 | -0.000000282310 |
| m260_a100 | 0.10 | -0.000038901174 | -0.000000537003 |

## Protected-Key Boundary

M183/M170 replay passes through full raw, but protected-key promotion does not.
The protected-key boundary is between `alpha=0.05` and `alpha=0.10`.

| Policy | Protected pass | Normal margin | Wrong-history margin | Margin gap |
| --- | --- | ---: | ---: | ---: |
| m259_a010 | true | 0.196134 | 0.095254 | 0.100880 |
| m260_a050 | true | 0.199550 | 0.098920 | 0.100630 |
| m260_a100 | false | 0.202650 | 0.102579 | 0.100071 |
| m239_a750 | false | 0.200336 | 0.099817 | 0.100519 |

`m260_a050` is selected as the largest checked protected-key-safe candidate.

## Replay Gates

All public replay gates pass for `m260_a050` versus M259:

| Corpus | Rows | Success drops retained | Normal margin delta | Margin gap delta | Gate pass |
| --- | ---: | ---: | ---: | ---: | --- |
| M183 M168 | 16 | 16 / 16 | +0.000032728 | +0.000019533 | true |
| M183 M170 | 17 | 17 / 17 | +0.000031320 | +0.000019788 | true |
| M193 M189 | 14 | 14 / 14 | +0.000026390 | +0.000039436 | true |
| M212 M204 | 17 | 17 / 17 | +0.000023848 | +0.000037814 | true |
| M223 M219 | 17 | 17 / 17 | +0.000023871 | +0.000037827 | true |

M183/M170 row16 is retained:

```text
row_id = 16
normal_success = true
wrong_history_success = false
normal_margin = 0.000014337
wrong_history_margin = -0.005907777
margin_gap = 0.005922114
```

## Behavior Retention

Behavior is retained on both public behavior seeds:

| Seed | Policy | Success | Termination | Mean clearance margin | Return |
| ---: | --- | ---: | ---: | ---: | ---: |
| 9505 | m259_a010 | 0.8625 | 0.1375 | 1.835358 | 65.956113 |
| 9505 | m260_a050 | 0.8625 | 0.1375 | 1.835353 | 65.964401 |
| 9505 | m260_a050_reset | 0.8500 | 0.1500 | 1.833996 | 64.059410 |
| 9505 | m260_a050_zero_all | 0.8000 | 0.2000 | 1.853241 | 61.043747 |
| 9506 | m259_a010 | 0.8625 | 0.1375 | 1.852876 | 66.232598 |
| 9506 | m260_a050 | 0.8625 | 0.1375 | 1.852870 | 66.240859 |
| 9506 | m260_a050_reset | 0.8500 | 0.1500 | 1.850266 | 64.349375 |
| 9506 | m260_a050_zero_all | 0.8000 | 0.2000 | 1.871149 | 61.306317 |

## Interpretation

M260 is stronger than the M258/M259 smoke repairs because the 4096-step raw PPO
checkpoint already improves both exact sources. The limiting gate is the
protected-key normal-margin window, not exact source or replay retention.

The safe update is not the full raw checkpoint; it is `alpha=0.05` from M259
toward raw. This supports the staged escalation idea, but requires a repeat
before longer PPO.

## Decision

Promote `m260_a050` as the current public-gate base:

```text
runs/m260_m259_to_raw_interpolation/checkpoints/alpha_0_05.pt
```

Next step:

```text
m261-repair-disciplined-stage2-repeat
```
