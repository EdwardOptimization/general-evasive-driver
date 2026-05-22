# M286 Rejected-Trajectory Anchor Balance Sweep

M286 tests whether the M284 rejected-history trajectory direction can be made
usable by lowering the rejected trajectory anchor pressure.

No PPO or actor-input change was performed.

## Setup

Base checkpoint:

```text
runs/m272_m264_to_m271_interpolation_boundary/checkpoints/alpha_0_01025.pt
```

Objective corpus:

```text
runs/m270_source_balanced_multi_surface_anchor/outcome_intervention_snippets.npz
```

Normal retention and recovery anchor base:

```text
runs/m279_combined_retention_recovery_anchor/combined_trajectory_anchor.npz
```

Current-family rejected-history corpus:

```text
runs/m267_m264_boundary_outcome_corpus_seed10070/boundary_outcome_corpus.csv
```

M286 exported three lower-pressure anchor variants:

| Variant | Rejected repeat | Combined rows |
| --- | ---: | ---: |
| repeat1 | 1 | 2559 |
| repeat2 | 2 | 3228 |
| repeat4 | 4 | 4566 |

M284 used rejected repeat 16 and produced 12594 combined rows.

## Raw Updates

All three raw updates improve the exact M270 objective and preserve M267/M264,
but all raw updates still fail M183/M170. The repeat2 variant is the least bad
raw candidate: it loses one M183/M170 row instead of collapsing the old surface.

| Candidate | Exact M270 loss | M183/M170 pass | M183/M170 normal success | M183/M170 drops | M267/M264 pass | M267/M264 drops |
| --- | ---: | --- | ---: | ---: | --- | ---: |
| M272 base | 0.681375623 | true | 1.000000 | 17 | true | 17 |
| repeat1 raw | 0.676669121 | false | 0.176471 | 3 | true | 17 |
| repeat2 raw | 0.676238179 | false | 0.941176 | 16 | true | 17 |
| repeat4 raw | 0.676554501 | false | 0.176471 | 3 | true | 17 |

The repeat2 raw failure is only row 10:

```text
row_id = 10
physical_pair_key = 9530:24:9540:27
normal_margin = -0.000204235
wrong_history_margin = -0.006872328
```

## Repeat2 Interpolation

Because repeat2 was the best balanced raw direction, M286 interpolated from
M272 toward repeat2.

| Alpha | Exact M270 loss | M183/M170 pass | M183/M170 drops | M267/M264 pass | M267/M264 drops |
| ---: | ---: | --- | ---: | --- | ---: |
| 0.0000 | 0.681375623 | true | 17 | true | 17 |
| 0.0100 | 0.681325078 | true | 17 | true | 17 |
| 0.0500 | 0.681122780 | true | 17 | true | 17 |
| 0.1000 | 0.680869579 | true | 17 | true | 17 |
| 0.2000 | 0.680361807 | true | 17 | true | 17 |
| 0.5000 | 0.678828239 | true | 17 | true | 17 |
| 1.0000 | 0.676238179 | false | 16 | true | 17 |

Selected candidate:

```text
policy = m286r2_a500
checkpoint = runs/m286_rejected_trajectory_anchor_balance_sweep/repeat2_interpolation/checkpoints/alpha_0_5.pt
```

Objective improvement:

```text
0.6813756227493286 -> 0.678828239440918
delta = -0.0025473833084106445
```

This is materially larger than M285's micro-alpha improvement:

```text
M285 delta = -0.00000095367431640625
```

## Full Public Gates

The selected `m286r2_a500` candidate passes the full public replay stack.

| Surface | Rows | Success drops retained | Normal success | Normal margin delta | Margin gap delta | Pass |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| M183/M168 | 16 | 16 / 16 | 1.000000 | -0.000083259 | +0.000089712 | true |
| M183/M170 | 17 | 17 / 17 | 1.000000 | -0.000073506 | +0.000088169 | true |
| M193/M189 | 14 | 14 / 14 | 1.000000 | -0.000042298 | +0.000040690 | true |
| M212/M204 | 17 | 17 / 17 | 1.000000 | -0.000061715 | +0.000041951 | true |
| M223/M219 | 17 | 17 / 17 | 1.000000 | -0.000061722 | +0.000041943 | true |
| M267/M264 | 17 | 17 / 17 | 1.000000 | -0.000061616 | +0.000041908 | true |

The old protected-key diagnostic also passes and remains discriminative:

```text
runs/m286_rejected_trajectory_anchor_balance_sweep/full_gates/critical_key_seed9944
guard_validated = true
```

Behavior is retained on both public behavior seeds:

| Seed | Policy | Success | Termination | Mean clearance margin |
| ---: | --- | ---: | ---: | ---: |
| 9505 | m272_base | 0.8625 | 0.1375 | 1.835337 |
| 9505 | m286r2_a500 | 0.8625 | 0.1375 | 1.835325 |
| 9505 | m286r2_a500_reset | 0.8500 | 0.1500 | 1.834224 |
| 9505 | m286r2_a500_zero_all | 0.8000 | 0.2000 | 1.853284 |
| 9506 | m272_base | 0.8625 | 0.1375 | 1.852854 |
| 9506 | m286r2_a500 | 0.8625 | 0.1375 | 1.852842 |
| 9506 | m286r2_a500_reset | 0.8500 | 0.1500 | 1.850504 |
| 9506 | m286r2_a500_zero_all | 0.8000 | 0.2000 | 1.871191 |

## Interpretation

M286 resolves the M285/M284 balance problem at the public-gate level. The
problem was not the rejected-history trajectory idea itself. The repeat16
combined anchor from M283 was too dominant. Repeat2 gives a usable direction:
raw repeat2 still crosses one M183/M170 row, but a 0.5 interpolation keeps all
registered public proof and behavior gates while giving a material exact M270
objective improvement.

This is still not enough to unblock PPO. The recipe needs a fresh-seed repeat
before any PPO continuation, because the selected candidate comes from one
optimizer seed and one interpolation.

## Decision

Promote `m286r2_a500` as the current public-gate base:

```text
runs/m286_rejected_trajectory_anchor_balance_sweep/repeat2_interpolation/checkpoints/alpha_0_5.pt
```

Decision:

```text
promote_m286r2_a500_public_gate_base
```

Next step:

```text
m287-balanced-rejected-trajectory-repeat
```

M287 should repeat the repeat2 balanced recipe on a fresh optimizer seed before
any PPO continuation.
