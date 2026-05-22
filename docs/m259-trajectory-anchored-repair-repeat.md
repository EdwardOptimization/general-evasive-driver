# M259 Trajectory-Anchored Repair Repeat

M259 repeats the M258 PPO-plus-projection repair path on a fresh PPO seed. This
tests whether the M258 result was a one-seed repair accident. Actor inputs are
unchanged and no long PPO was run.

## Setup

Current public-gate base:

```text
runs/m258_m253_to_projection_interpolation/checkpoints/alpha_0_01.pt
```

Fresh PPO smoke:

```text
runs/ppo_m259_repair_repeat_from_m258_seed5226
```

PPO settings:

```text
config = configs/ppo_m248_source_balanced_from_m239_smoke.json
init checkpoint = m258_a010
seed = 5226
total_steps = 1024
device = cuda
```

Post-PPO projection repair:

```text
runs/m259_trajectory_anchored_projection_seed10069
```

Projection settings:

```text
steps = 40
learning_rate = 5e-5
batch_size = 1
train_scope = actor_coupling
protected snippet = runs/m231_protected_key_snippet_surface/protected_key_snippets.npz
snippet anchor checkpoint = M258
snippet anchor coef = 1.0
trajectory anchor = runs/m235_closed_loop_trajectory_anchor_surface/trajectory_anchor.npz
trajectory anchor coef = 100.0
trajectory anchor batch size = 32
```

## Raw PPO Exact Source Gate

The raw PPO checkpoint repeats the same source conflict seen in M254:

| Policy | M223 source delta | Protected-key source delta |
| --- | ---: | ---: |
| m259_raw | -0.000105 | +0.000005 |

Raw PPO is therefore rejected before proof gates.

## Projection Repair

The trajectory-anchored projection repairs the protected source while retaining
the M223 improvement:

| Policy | M223 source delta | Protected-key source delta |
| --- | ---: | ---: |
| m259_raw | -0.000105 | +0.000005 |
| m259_proj | -0.000269 | -0.000257 |

Projection objective summary:

| Metric | Before | After |
| --- | ---: | ---: |
| protected snippet loss | 0.035643168 | 0.035380840 |
| snippet anchor MSE | 0.000000019 | 0.000000713 |
| trajectory anchor MSE | 0.000000890 | 0.000000739 |

Interpolation from M258 toward the projected checkpoint keeps both source
deltas negative for every tested alpha:

| Policy | Alpha | M223 source delta | Protected-key source delta |
| --- | ---: | ---: | ---: |
| m259_a0_00001 | 0.00001 | -0.000000008671 | -0.000000006137 |
| m259_a0_000025 | 0.000025 | -0.000000019697 | -0.000000006137 |
| m259_a0_00005 | 0.00005 | -0.000000031988 | -0.000000012274 |
| m259_a0_0001 | 0.0001 | -0.000000042119 | -0.000000030686 |
| m259_a0_00025 | 0.00025 | -0.000000074924 | -0.000000064440 |
| m259_a0_0005 | 0.0005 | -0.000000139919 | -0.000000128881 |
| m259_a001 | 0.001 | -0.000000272179 | -0.000000251624 |
| m259_a0_0025 | 0.0025 | -0.000000656779 | -0.000000622923 |
| m259_a005 | 0.005 | -0.000001309599 | -0.000001248915 |
| m259_a010 | 0.01 | -0.000002624788 | -0.000002507036 |

`m259_a010` is the largest tested exact-gated alpha and advances to public
proof gates.

## Replay Gates

All public replay gates pass versus M258:

| Corpus | Rows | Success drops retained | Normal margin delta | Margin gap delta | Gate pass |
| --- | ---: | ---: | ---: | ---: | --- |
| M183 M168 | 16 | 16 / 16 | +0.000009142 | +0.000001224 | true |
| M183 M170 | 17 | 17 / 17 | +0.000009192 | +0.000001252 | true |
| M193 M189 | 14 | 14 / 14 | +0.000008757 | +0.000001858 | true |
| M212 M204 | 17 | 17 / 17 | +0.000008583 | +0.000001712 | true |
| M223 M219 | 17 | 17 / 17 | +0.000008586 | +0.000001716 | true |

The M256 row16 failure surface is retained:

```text
row_id = 16
normal_success = true
wrong_history_success = false
normal_margin = 0.000004459
wrong_history_margin = -0.005915997
margin_gap = 0.005920456
```

## Protected Key

Protected key `9944|perturbed|28|28` passes, and the known failing control
`m239_a750` still fails:

| Policy | Pass | Normal margin | Wrong-history margin | Margin gap |
| --- | --- | ---: | ---: | ---: |
| m224_10063 | true | 0.186385 | 0.086925 | 0.099460 |
| m258_a010 | true | 0.195973 | 0.095118 | 0.100855 |
| m259_a010 | true | 0.196134 | 0.095254 | 0.100880 |
| m239_a750 | false | 0.200336 | 0.099817 | 0.100519 |

## Behavior Retention

Behavior is retained on both public behavior seeds:

| Seed | Policy | Success | Termination | Mean clearance margin |
| ---: | --- | ---: | ---: | ---: |
| 9505 | m258_a010 | 0.8625 | 0.1375 | 1.835355 |
| 9505 | m259_a010 | 0.8625 | 0.1375 | 1.835358 |
| 9505 | m259_a010_reset | 0.8500 | 0.1500 | 1.834012 |
| 9505 | m259_a010_zero_all | 0.8000 | 0.2000 | 1.853257 |
| 9506 | m258_a010 | 0.8625 | 0.1375 | 1.852874 |
| 9506 | m259_a010 | 0.8625 | 0.1375 | 1.852876 |
| 9506 | m259_a010_reset | 0.8500 | 0.1500 | 1.850282 |
| 9506 | m259_a010_zero_all | 0.8000 | 0.2000 | 1.871167 |

## Interpretation

M259 is the first fresh-seed repeat showing that the M258 repair discipline is
not just a lucky fix of M254 seed `5225`. The repeated pattern is:

```text
raw PPO improves M223 source but regresses protected-key source;
trajectory-anchored post-PPO projection repairs protected-key source;
small interpolation preserves exact sources and public proof gates.
```

This supports moving from smoke repair into a staged PPO escalation, but not a
long run yet.

## Decision

Promote `m259_a010` as the current public-gate base:

```text
runs/m259_m258_to_projection_interpolation/checkpoints/alpha_0_01.pt
```

Next step:

```text
m260-repair-disciplined-stage2-ppo-from-m259
```
