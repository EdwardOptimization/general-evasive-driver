# M291 Row16-Aware Guarded PPO Smoke

M291 runs one 1024-step guarded PPO smoke from the repeated row16-aware
public-gate base `m290x64_a500`.

Actor inputs are unchanged.

## Setup

Initial checkpoint:

```text
runs/m290_row16_aware_balanced_repeat_fresh_seed/interpolation/checkpoints/alpha_0_5.pt
```

Config:

```text
configs/ppo_m291_row16_aware_guarded_smoke.json
```

Raw PPO checkpoint:

```text
runs/ppo_m291_row16_aware_guarded_smoke_seed5231/checkpoint.pt
```

The config anchors behavior to `m290x64_a500`, uses the M270 source-balanced
snippet corpus, and keeps the M289 row16-aware extra64 trajectory anchor.

## Raw PPO

The raw PPO checkpoint is not acceptable. It preserves M183/M170 but loses four
M267/M264 wrong-history success drops, and its exact M270 loss gets worse.

| Candidate | Exact M270 loss | Delta vs M290 | M183/M170 pass | M183/M170 drops | M267/M264 pass | M267/M264 drops |
| --- | ---: | ---: | --- | ---: | --- | ---: |
| m290x64_a500 | 0.679278374 | 0.000000000 | true | 17 | true | 17 |
| m291raw | 0.679781079 | +0.000502706 | true | 17 | false | 13 |

The training smoke is therefore a proof-washout diagnostic, not a promoted PPO
result.

## Interpolation Diagnostic

M291 interpolated from `m290x64_a500` toward raw PPO to locate the public-gate
safe trust region.

| Alpha | Exact M270 loss | M183/M170 pass | M183/M170 drops | M267/M264 pass | M267/M264 drops |
| ---: | ---: | --- | ---: | --- | ---: |
| 0.000 | 0.679278374 | true | 17 | true | 17 |
| 0.001 | 0.679278910 | true | 17 | true | 17 |
| 0.005 | 0.679280877 | true | 17 | true | 17 |
| 0.010 | 0.679283321 | true | 17 | true | 17 |
| 0.050 | 0.679303348 | true | 17 | true | 17 |
| 0.100 | 0.679328442 | true | 17 | true | 17 |
| 0.200 | 0.679378390 | true | 17 | false | 16 |
| 0.500 | 0.679528892 | true | 17 | false | 15 |
| 1.000 | 0.679781079 | true | 17 | false | 13 |

The largest checked public-gate-safe interpolation is:

```text
policy = m291_a100
checkpoint = runs/m291_row16_aware_guarded_ppo_smoke/interpolation/checkpoints/alpha_0_1.pt
```

But it still worsens exact M270:

```text
0.6792783737182617 -> 0.679328441619873
delta = +0.000050067901611328125
```

## Full Public Gates

The diagnostic `m291_a100` checkpoint passes the full public replay stack.

| Surface | Rows | Success drops retained | Normal success | Normal margin delta | Margin gap delta | Pass |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| M183/M168 | 16 | 16 / 16 | 1.000000 | +0.000096362 | +0.000007230 | true |
| M183/M170 | 17 | 17 / 17 | 1.000000 | +0.000096033 | +0.000007385 | true |
| M193/M189 | 14 | 14 / 14 | 1.000000 | +0.000089719 | +0.000017438 | true |
| M212/M204 | 17 | 17 / 17 | 1.000000 | +0.000089166 | +0.000016721 | true |
| M223/M219 | 17 | 17 / 17 | 1.000000 | +0.000089174 | +0.000016726 | true |
| M267/M264 | 17 | 17 / 17 | 1.000000 | +0.000089176 | +0.000016736 | true |

The old protected-key diagnostic passes:

```text
runs/m291_row16_aware_guarded_ppo_smoke/full_gates/critical_key_seed9944
guard_validated = true
```

Behavior is retained on both public behavior seeds:

| Seed | Policy | Success | Termination | Mean clearance margin |
| ---: | --- | ---: | ---: | ---: |
| 9505 | m290x64_a500 | 0.8625 | 0.1375 | 1.836100 |
| 9505 | m291_a100 | 0.8625 | 0.1375 | 1.836144 |
| 9505 | m291_a100_reset | 0.8500 | 0.1500 | 1.834574 |
| 9505 | m291_a100_zero_all | 0.8000 | 0.2000 | 1.853575 |
| 9506 | m290x64_a500 | 0.8625 | 0.1375 | 1.853644 |
| 9506 | m291_a100 | 0.8625 | 0.1375 | 1.853688 |
| 9506 | m291_a100_reset | 0.8500 | 0.1500 | 1.850863 |
| 9506 | m291_a100_zero_all | 0.8000 | 0.2000 | 1.871505 |

## Interpretation

M291 shows that a small trust-region interpolation of PPO can retain public
proof gates, but the PPO direction itself is not useful yet. Raw PPO washes out
M267/M264 wrong-history sensitivity, and the safe interpolation does not improve
the fixed M270 objective or behavior in a material way.

This should not replace M290. The next step is an audit of why the PPO update
pushes current-family wrong-history rows toward safety while the actor-update
recipe preserved them.

## Decision

Archive M291 as a PPO proof-washout diagnostic. Keep `m290x64_a500` as the
current public-gate base.

Failure types:

```text
proof_washout
objective_overfit
```

Decision:

```text
archive_m291_safe_interpolation_diagnostic_keep_m290_base
```

Next step:

```text
m292-m291-ppo-proof-washout-audit
```
