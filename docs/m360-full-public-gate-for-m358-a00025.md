# M360 Full Public Gate For M358 A00025

M360 runs the full public promotion gate for the M358 micro-alpha candidate.
No PPO, actor update, or actor-input change was performed in M360.

## Candidate

Previous public-gate base:

```text
runs/m351_m349_to_repaired_old_key_neighborhood_interpolation/checkpoints/alpha_0_0075.pt
```

Candidate:

```text
runs/m358_m352_to_m354_best_step_micro_interpolation/checkpoints/alpha_0_00025.pt
```

## Exact Objectives

M358 already ran the exact objective comparison against the previous M352 base:

```text
runs/m358_m354_best_step_alpha00025_exact_eval
```

| Objective | Delta vs previous public base | Pass |
| --- | ---: | --- |
| Exact M297 rejected-history preference | -0.000000119 | true |
| Exact M270 source-balanced outcome | -0.000000060 | true |

## Old-Key Neighborhood Gate

M358 is the old-key neighborhood proof source for this alpha:

```text
runs/m358_m354_best_step_old_key_micro_a00025_gate
```

`alpha=0.00025` passes with `0` accepted regressions, gap p10
`-0.000001`, and gap min `-0.000002`. `alpha=0.0005` is the first failing
tested alpha.

## Source-Diverse Protected Gate

M359 ran the source-diverse protected gate:

```text
runs/m359_m354_best_step_micro_alpha_source_diverse_protected_gate
```

All five source-diverse protected replay gates pass.

| Replay gate | Rows | Candidate drops | Normal margin delta | Margin gap delta | Pass |
| --- | ---: | ---: | ---: | ---: | --- |
| current_m333_surface | 17 | 17 | +0.000010289 | +0.000006042 | true |
| m328_continuity_surface | 17 | 17 | +0.000100927 | +0.000043772 | true |
| m325_continuity_surface | 17 | 17 | +0.000294761 | +0.000128649 | true |
| m317_continuity_surface | 17 | 17 | +0.000489557 | +0.000208894 | true |
| m314_continuity_surface | 17 | 17 | +0.000490081 | +0.000209094 | true |

## Public Replay Gates

All six public replay gates pass versus `m333_base`.

| Surface | Rows | Success drops retained | Normal margin delta | Margin gap delta | Pass |
| --- | ---: | ---: | ---: | ---: | --- |
| M183/M168 | 16 | 16 / 16 | +0.000012257 | +0.000001984 | true |
| M183/M170 | 17 | 17 / 17 | +0.000012063 | +0.000002101 | true |
| M193/M189 | 14 | 14 / 14 | +0.000010504 | +0.000006276 | true |
| M212/M204 | 17 | 17 / 17 | +0.000010276 | +0.000006033 | true |
| M223/M219 | 17 | 17 / 17 | +0.000010280 | +0.000006034 | true |
| M267/M264 | 17 | 17 / 17 | +0.000010287 | +0.000006039 | true |

Replay run roots:

```text
runs/m360_full_public_gate_for_m358_a00025/full_gates
runs/m359_m354_best_step_micro_alpha_m183_m170_first_replay
runs/m359_m354_best_step_micro_alpha_m267_m264_first_replay
```

## Behavior Retention

Behavior is retained on both public behavior seeds.

| Seed | Policy | Success | Termination | Mean clearance margin | Return |
| ---: | --- | ---: | ---: | ---: | ---: |
| 9505 | m333_base | 0.8625 | 0.1375 | 1.835798 | 65.942123 |
| 9505 | m358_a00025 | 0.8625 | 0.1375 | 1.835795 | 65.941575 |
| 9505 | m358_a00025_reset | 0.8500 | 0.1500 | 1.834314 | 64.031152 |
| 9505 | m358_a00025_zero_all | 0.8000 | 0.2000 | 1.852955 | 61.058115 |
| 9506 | m333_base | 0.8625 | 0.1375 | 1.853285 | 66.218397 |
| 9506 | m358_a00025 | 0.8625 | 0.1375 | 1.853281 | 66.217853 |
| 9506 | m358_a00025_reset | 0.8500 | 0.1500 | 1.850594 | 64.321032 |
| 9506 | m358_a00025_zero_all | 0.8000 | 0.2000 | 1.870837 | 61.320958 |

The candidate keeps public behavior success and termination equal to
`m333_base`, and preserves the reset and zero-all ablation ordering.

## Interpretation

M360 promotes the M358 `alpha=0.00025` candidate as the new public-gate base.

This is a conservative promotion. It preserves the proof and behavior gates,
but the accepted movement from M352 is extremely small:

```text
accepted alpha = 0.00025
first failing old-key alpha = 0.0005
```

The result should not be treated as meaningful driver improvement. It is a
proof-safe micro-step that keeps the M354 branch alive while exposing that the
current repair direction is almost completely clipped by old-key proof.

## Decision

Promote:

```text
runs/m358_m352_to_m354_best_step_micro_interpolation/checkpoints/alpha_0_00025.pt
```

Decision:

```text
promote_m358_a00025_old_key_neighborhood_public_gate_base
```

Next:

```text
m361-micro-alpha-utility-audit
```
