# M333 Full Public Gate For M332 A045

M333 runs the full public promotion gate for the M332 gap-bounded
interpolation candidate. No PPO, actor update, or actor-input change was
performed in M333.

## Candidate

Current public-gate base:

```text
runs/m327_exact_repair_from_raw_s40_seed10097/candidate_checkpoint.pt
```

Candidate:

```text
runs/m332_m328_to_m330_gap_bounded_interpolation/checkpoints/alpha_0_45.pt
```

## Exact Objectives

Exact objective retention versus M328:

| Objective | Delta |
| --- | ---: |
| Exact M297 rejected-history preference | -0.000056148 |
| Exact M270 source-balanced outcome | -0.000036240 |

Both exact objectives pass no-regression.

Run dir:

```text
runs/m333_full_public_gate_for_m332_a045/exact_eval_vs_m328
```

## Source-Diverse Protected Gate

Run dir:

```text
runs/m333_full_public_gate_for_m332_a045/source_diverse_protected_gate
```

All four source-diverse protected replay gates pass.

| Replay gate | Rows | Baseline drops | Candidate drops | Normal margin delta | Margin gap delta | Pass |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| current_m328_surface | 17 | 17 | 17 | +0.000090638 | +0.000037730 | true |
| m325_continuity_surface | 17 | 17 | 17 | +0.000284472 | +0.000122608 | true |
| m317_continuity_surface | 17 | 17 | 17 | +0.000479270 | +0.000202855 | true |
| m314_continuity_surface | 17 | 17 | 17 | +0.000479794 | +0.000203056 | true |

## Public Replay Gates

All six public replay gates pass versus M328.

| Surface | Rows | Success drops retained | Normal margin delta | Margin gap delta | Pass |
| --- | ---: | ---: | ---: | ---: | --- |
| M183/M168 | 16 | 16 / 16 | +0.000103758 | +0.000011442 | true |
| M183/M170 | 17 | 17 / 17 | +0.000102502 | +0.000012246 | true |
| M193/M189 | 14 | 14 / 14 | +0.000091801 | +0.000039289 | true |
| M212/M204 | 17 | 17 / 17 | +0.000090594 | +0.000037708 | true |
| M223/M219 | 17 | 17 / 17 | +0.000090612 | +0.000037717 | true |
| M267/M264 | 17 | 17 / 17 | +0.000090650 | +0.000037736 | true |

Replay run root:

```text
runs/m333_full_public_gate_for_m332_a045/full_gates
```

## Old 9944 Diagnostic

Old protected key `9944|perturbed|28|28` remains a diagnostic singleton.

| Policy | Pass | Normal margin | Wrong-history margin | Margin gap |
| --- | --- | ---: | ---: | ---: |
| m263_a005 | true | 0.199909 | 0.099300 | 0.100609 |
| m328_base | false | 0.213944 | 0.121291 | 0.092653 |
| m332_a045 | false | 0.216606 | 0.126452 | 0.090155 |
| m239_a750 | false | 0.200336 | 0.099817 | 0.100519 |

The candidate fails the old singleton normal-margin window but retains the
registered M324/M331 gap floor:

```text
margin_gap = 0.0901547923076611
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
| 9505 | m328_base | 0.8625 | 0.1375 | 1.835793 | 65.946706 |
| 9505 | m332_a045 | 0.8625 | 0.1375 | 1.835798 | 65.942123 |
| 9505 | m332_a045_reset | 0.8500 | 0.1500 | 1.834320 | 64.031146 |
| 9505 | m332_a045_zero_all | 0.8000 | 0.2000 | 1.852966 | 61.058165 |
| 9506 | m328_base | 0.8625 | 0.1375 | 1.853285 | 66.222966 |
| 9506 | m332_a045 | 0.8625 | 0.1375 | 1.853285 | 66.218397 |
| 9506 | m332_a045_reset | 0.8500 | 0.1500 | 1.850600 | 64.321025 |
| 9506 | m332_a045_zero_all | 0.8000 | 0.2000 | 1.870849 | 61.321000 |

The candidate keeps public behavior success and termination equal to M328 while
preserving reset and zero-all ablation ordering.

## Interpretation

M333 promotes the M332 alpha `0.45` gap-bounded interpolation candidate as the
new public-gate base.

This is the accepted fresh-seed repeat of the source-diverse protected PPO
proposal path:

```text
M328 public base
  -> M330 fresh-seed PPO proposal and exact repair
  -> M332 old-key gap-bounded interpolation
  -> M333 full public gate promotion
```

The result shows that M330's direction was not a source-diverse proof washout.
The unbounded endpoint eroded the old `9944` gap below the `0.09` floor, but a
bounded trust-region step preserves exact objectives, source-diverse proof, all
public replay surfaces, old-key diagnostic gap, and behavior retention.

The next step should design a short PPO escalation from this new base. It should
not jump directly to medium or long PPO; it should keep exact repair,
source-diverse protected gates, old-key gap floor, and full-gate promotion
discipline.

## Decision

Promote:

```text
runs/m332_m328_to_m330_gap_bounded_interpolation/checkpoints/alpha_0_45.pt
```

Decision:

```text
promote_m332_a045_source_diverse_public_gate_base
```

Next:

```text
m334-short-source-diverse-ppo-escalation-design
```
