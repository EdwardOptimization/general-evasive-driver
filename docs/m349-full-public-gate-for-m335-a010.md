# M349 Full Public Gate For M335 A010

M349 runs the full public promotion gate for the M335 `alpha=0.01` candidate
admitted by M348. No PPO, actor update, or actor-input change was performed in
M349.

## Candidate

Previous public-gate base:

```text
runs/m335_m333_to_repaired_gap_bounded_interpolation/checkpoints/alpha_0_0075.pt
```

Candidate:

```text
runs/m335_m333_to_repaired_gap_bounded_interpolation/checkpoints/alpha_0_01.pt
```

## Exact Objectives

M348 already ran the exact objective comparison against the previous M336 base:

```text
runs/m348_m335_a010_exact_eval_vs_a0075
```

| Objective | Delta vs previous public base | Pass |
| --- | ---: | --- |
| Exact M297 rejected-history preference | -0.000000954 | true |
| Exact M270 source-balanced outcome | -0.000000477 | true |

Both exact objectives pass no-regression.

## Source-Diverse Protected Gate

M348 also ran the source-diverse protected gate:

```text
runs/m348_m335_a010_source_diverse_protected_gate
```

All five source-diverse protected replay gates pass.

| Replay gate | Rows | Candidate drops | Normal margin delta | Margin gap delta | Pass |
| --- | ---: | ---: | ---: | ---: | --- |
| current_m333_surface | 17 | 17 | +0.000005535 | +0.000003428 | true |
| m328_continuity_surface | 17 | 17 | +0.000096173 | +0.000041158 | true |
| m325_continuity_surface | 17 | 17 | +0.000290007 | +0.000126035 | true |
| m317_continuity_surface | 17 | 17 | +0.000484801 | +0.000206280 | true |
| m314_continuity_surface | 17 | 17 | +0.000485323 | +0.000206479 | true |

## Old-Key Neighborhood Gate

M347 is the old-key neighborhood proof source for this alpha:

```text
runs/m347_old_key_alpha_sweep/summary.json
```

`m335_a010` passes with `0` accepted regressions, gap p10 `-0.000006`, and gap
min `-0.000016`. `alpha=0.02` remains the first failing alpha.

## Public Replay Gates

All six public replay gates pass versus `m333_base`.

| Surface | Rows | Success drops retained | Normal margin delta | Margin gap delta | Pass |
| --- | ---: | ---: | ---: | ---: | --- |
| M183/M168 | 16 | 16 / 16 | +0.000006657 | +0.000001107 | true |
| M183/M170 | 17 | 17 / 17 | +0.000006544 | +0.000001179 | true |
| M193/M189 | 14 | 14 / 14 | +0.000005654 | +0.000003567 | true |
| M212/M204 | 17 | 17 / 17 | +0.000005525 | +0.000003425 | true |
| M223/M219 | 17 | 17 / 17 | +0.000005529 | +0.000003425 | true |
| M267/M264 | 17 | 17 / 17 | +0.000005530 | +0.000003428 | true |

Replay run root:

```text
runs/m349_full_public_gate_for_m335_a010/full_gates
```

## Behavior Retention

Behavior is retained on both public behavior seeds.

| Seed | Policy | Success | Termination | Mean clearance margin | Return |
| ---: | --- | ---: | ---: | ---: | ---: |
| 9505 | m333_base | 0.8625 | 0.1375 | 1.835798 | 65.942123 |
| 9505 | m335_a010 | 0.8625 | 0.1375 | 1.835797 | 65.941794 |
| 9505 | m335_a010_reset | 0.8500 | 0.1500 | 1.834317 | 64.031146 |
| 9505 | m335_a010_zero_all | 0.8000 | 0.2000 | 1.852960 | 61.058123 |
| 9506 | m333_base | 0.8625 | 0.1375 | 1.853285 | 66.218397 |
| 9506 | m335_a010 | 0.8625 | 0.1375 | 1.853283 | 66.218069 |
| 9506 | m335_a010_reset | 0.8500 | 0.1500 | 1.850597 | 64.321026 |
| 9506 | m335_a010_zero_all | 0.8000 | 0.2000 | 1.870843 | 61.320963 |

The candidate keeps public behavior success and termination equal to `m333_base`
while preserving the reset and zero-all ablation ordering.

## Interpretation

M349 promotes the M335 `alpha=0.01` candidate as the new public-gate base. The
promotion is still a conservative interpolation within the M335 repaired
short-PPO family, but it is no longer constrained by the stale singleton `9944`
floor. It passes the distributional old-key neighborhood gate while keeping
source-diverse protected proof, all six public replay surfaces, and behavior
retention.

The next step should not be a naked PPO run. It should first design the next
PPO escalation acceptance stack using the exact objectives, source-diverse
protected gate, old-key neighborhood replay gate, first replay gates, full
public gate, and behavior seeds.

## Decision

Promote:

```text
runs/m335_m333_to_repaired_gap_bounded_interpolation/checkpoints/alpha_0_01.pt
```

Decision:

```text
promote_m335_a010_old_key_neighborhood_public_gate_base
```

Next:

```text
m350-old-key-neighborhood-ppo-escalation-design
```
