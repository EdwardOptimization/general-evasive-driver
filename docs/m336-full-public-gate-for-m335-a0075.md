# M336 Full Public Gate For M335 A0075

M336 runs the full public promotion gate for the M335 bounded short-PPO
candidate. No PPO, actor update, or actor-input change was performed in M336.

## Candidate

Current public-gate base:

```text
runs/m332_m328_to_m330_gap_bounded_interpolation/checkpoints/alpha_0_45.pt
```

Candidate:

```text
runs/m335_m333_to_repaired_gap_bounded_interpolation/checkpoints/alpha_0_0075.pt
```

## Exact Objectives

Exact objective retention versus M333:

| Objective | Delta |
| --- | ---: |
| Exact M297 rejected-history preference | -0.000002623 |
| Exact M270 source-balanced outcome | -0.000001252 |

Both exact objectives pass no-regression.

Run dir:

```text
runs/m336_full_public_gate_for_m335_a0075/exact_eval_vs_m333
```

## Source-Diverse Protected Gate

Run dir:

```text
runs/m336_full_public_gate_for_m335_a0075/source_diverse_protected_gate
```

All five source-diverse protected replay gates pass.

| Replay gate | Rows | Baseline drops | Candidate drops | Normal margin delta | Margin gap delta | Pass |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| current_m333_surface | 17 | 17 | 17 | +0.000004170 | +0.000002575 | true |
| m328_continuity_surface | 17 | 17 | 17 | +0.000094808 | +0.000040305 | true |
| m325_continuity_surface | 17 | 17 | 17 | +0.000288642 | +0.000125182 | true |
| m317_continuity_surface | 17 | 17 | 17 | +0.000483439 | +0.000205426 | true |
| m314_continuity_surface | 17 | 17 | 17 | +0.000483960 | +0.000205622 | true |

## Public Replay Gates

All six public replay gates pass versus M333.

| Surface | Rows | Success drops retained | Normal margin delta | Margin gap delta | Pass |
| --- | ---: | ---: | ---: | ---: | --- |
| M183/M168 | 16 | 16 / 16 | +0.000005014 | +0.000000835 | true |
| M183/M170 | 17 | 17 / 17 | +0.000004931 | +0.000000892 | true |
| M193/M189 | 14 | 14 / 14 | +0.000004256 | +0.000002674 | true |
| M212/M204 | 17 | 17 / 17 | +0.000004164 | +0.000002571 | true |
| M223/M219 | 17 | 17 / 17 | +0.000004164 | +0.000002566 | true |
| M267/M264 | 17 | 17 / 17 | +0.000004169 | +0.000002572 | true |

Replay run root:

```text
runs/m336_full_public_gate_for_m335_a0075/full_gates
```

## Old 9944 Diagnostic

Old protected key `9944|perturbed|28|28` remains a diagnostic singleton.

| Policy | Pass | Normal margin | Wrong-history margin | Margin gap |
| --- | --- | ---: | ---: | ---: |
| m263_a005 | true | 0.199909 | 0.099300 | 0.100609 |
| m333_base | false | 0.216606 | 0.126452 | 0.090155 |
| m335_a0075 | false | 0.216783 | 0.126762 | 0.090021 |
| m239_a750 | false | 0.200336 | 0.099817 | 0.100519 |

The candidate fails the old singleton normal-margin window but retains the
registered M324/M331 gap floor:

```text
margin_gap = 0.09002140115294455
M324/M331 diagnostic floor = 0.09
```

Classification:

```text
single_key_window_saturation_with_gap_floor_retained
```

## Behavior Retention

Behavior is retained on both public behavior seeds.

| Seed | Policy | Success | Termination | Mean clearance margin | Return |
| ---: | --- | ---: | ---: | ---: | ---: |
| 9505 | m333_base | 0.8625 | 0.1375 | 1.835798 | 65.942123 |
| 9505 | m335_a0075 | 0.8625 | 0.1375 | 1.835797 | 65.941876 |
| 9505 | m335_a0075_reset | 0.8500 | 0.1500 | 1.834318 | 64.031146 |
| 9505 | m335_a0075_zero_all | 0.8000 | 0.2000 | 1.852962 | 61.058134 |
| 9506 | m333_base | 0.8625 | 0.1375 | 1.853285 | 66.218397 |
| 9506 | m335_a0075 | 0.8625 | 0.1375 | 1.853283 | 66.218151 |
| 9506 | m335_a0075_reset | 0.8500 | 0.1500 | 1.850598 | 64.321026 |
| 9506 | m335_a0075_zero_all | 0.8000 | 0.2000 | 1.870844 | 61.320973 |

The candidate keeps public behavior success and termination equal to M333 while
preserving reset and zero-all ablation ordering.

## Interpretation

M336 promotes the M335 alpha `0.0075` bounded short-PPO candidate as the new
public-gate base.

The promotion is safe under the current public gate stack:

```text
exact M297/M270 non-regression,
source-diverse protected proof,
old-key gap floor,
six replay surfaces,
behavior seeds.
```

But M336 also confirms that the fixed old-key gap floor has become the limiting
constraint. M335's repaired endpoint had much stronger exact-objective
improvement, but the old-key gap floor clipped the admissible step to
`alpha=0.0075`.

The next step should not be longer PPO. It should audit the old-key floor as a
bottleneck and decide whether to keep the fixed `9944` scalar floor, replace it
with a source-diverse old-key/gap distribution, or add an objective term that
protects old-key gap without forcing micro-alpha continuation.

## Decision

Promote:

```text
runs/m335_m333_to_repaired_gap_bounded_interpolation/checkpoints/alpha_0_0075.pt
```

Decision:

```text
promote_m335_a0075_short_ppo_public_gate_base
```

Next:

```text
m337-old-key-gap-floor-bottleneck-audit
```
