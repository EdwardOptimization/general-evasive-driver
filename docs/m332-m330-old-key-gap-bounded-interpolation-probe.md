# M332 M330 Old-Key Gap-Bounded Interpolation Probe

M332 probes whether the useful M330 exact/source-diverse direction can be
accepted inside an old-key gap-bounded trust region. No PPO, promotion, or
actor-input change was performed.

## Interpolation

Base:

```text
runs/m327_exact_repair_from_raw_s40_seed10097/candidate_checkpoint.pt
```

Target:

```text
runs/m330_exact_repair_from_raw_s40_seed10098/candidate_checkpoint.pt
```

Interpolation run:

```text
runs/m332_m328_to_m330_gap_bounded_interpolation
```

Alpha grid:

```text
0, 0.2, 0.35, 0.45, 0.5, 0.55, 0.6, 0.75, 1.0
```

## Exact Line Search

Run dir:

```text
runs/m332_m328_to_m330_exact_line_search
```

All tested alphas pass exact M297/M270 no-regression. Selected alpha `0.45`
has:

| Objective | Delta vs M328 |
| --- | ---: |
| Exact M297 rejected-history preference | -0.000056148 |
| Exact M270 source-balanced outcome | -0.000036240 |

## Old-Key Gap Sweep

Run dir:

```text
runs/m332_old_key_gap_sweep
```

Old-key `9944|perturbed|28|28` gap around the decision boundary:

| Policy | Alpha | Normal margin | Wrong-history margin | Margin gap |
| --- | ---: | ---: | ---: | ---: |
| m332_a000 | 0.00 | 0.213944 | 0.121291 | 0.092653 |
| m332_a045 | 0.45 | 0.216606 | 0.126452 | 0.090155 |
| m332_a050 | 0.50 | 0.216906 | 0.126982 | 0.089925 |
| m332_a100 | 1.00 | 0.219756 | 0.132855 | 0.086901 |

The largest alpha in the registered grid satisfying the old-key floor is:

```text
alpha = 0.45
margin_gap = 0.0901547923076611
```

## Source-Diverse Protected Gate

Run dir:

```text
runs/m332_a045_source_diverse_protected_gate
```

All four source-diverse protected gates pass at alpha `0.45`.

| Replay gate | Rows | Candidate drops | Normal margin delta | Margin gap delta | Pass |
| --- | ---: | ---: | ---: | ---: | --- |
| current_m328_surface | 17 | 17 | +0.000090638 | +0.000037730 | true |
| m325_continuity_surface | 17 | 17 | +0.000284472 | +0.000122608 | true |
| m317_continuity_surface | 17 | 17 | +0.000479270 | +0.000202855 | true |
| m314_continuity_surface | 17 | 17 | +0.000479794 | +0.000203056 | true |

## First Replay Gates

Both first replay gates pass at alpha `0.45`.

| Surface | Rows | Success drops retained | Normal margin delta | Margin gap delta | Pass |
| --- | ---: | ---: | ---: | ---: | --- |
| M183/M170 | 17 | 17 / 17 | +0.000102502 | +0.000012246 | true |
| M267/M264 | 17 | 17 / 17 | +0.000090650 | +0.000037736 | true |

## Interpretation

M332 is positive. The full M330 repaired candidate violates the old-key gap
floor, but its direction is still useful inside a bounded trust region:

```text
M328 -> M330 repaired at alpha 0.45
```

This alpha retains:

```text
exact M297/M270 improvement,
source-diverse protected proof,
old-key margin gap >= 0.09,
M183/M170 first replay,
M267/M264 first replay.
```

M332 does not promote. It admits a separate full public-gate milestone.

## Decision

Admit:

```text
m333-full-public-gate-for-m332-a045
```

Decision:

```text
admit_m333_full_public_gate_for_m332_a045
```
