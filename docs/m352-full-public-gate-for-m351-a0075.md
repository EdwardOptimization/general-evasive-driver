# M352 Full Public Gate For M351 A0075

M352 runs the full public promotion gate for the M351 bounded short-PPO
candidate. No PPO, actor update, or actor-input change was performed in M352.

## Candidate

Previous public-gate base:

```text
runs/m335_m333_to_repaired_gap_bounded_interpolation/checkpoints/alpha_0_01.pt
```

Candidate:

```text
runs/m351_m349_to_repaired_old_key_neighborhood_interpolation/checkpoints/alpha_0_0075.pt
```

## Exact Objectives

M351 already ran the exact objective comparison against the previous M349 base:

```text
runs/m351_a0075_exact_eval_vs_m349
```

| Objective | Delta vs previous public base | Pass |
| --- | ---: | --- |
| Exact M297 rejected-history preference | -0.000002742 | true |
| Exact M270 source-balanced outcome | -0.000001490 | true |

Both exact objectives pass no-regression.

## Source-Diverse Protected Gate

M351 also ran the source-diverse protected gate:

```text
runs/m351_a0075_source_diverse_protected_gate
```

All five source-diverse protected replay gates pass.

| Replay gate | Rows | Candidate drops | Normal margin delta | Margin gap delta | Pass |
| --- | ---: | ---: | ---: | ---: | --- |
| current_m333_surface | 17 | 17 | +0.000010121 | +0.000005954 | true |
| m328_continuity_surface | 17 | 17 | +0.000100758 | +0.000043684 | true |
| m325_continuity_surface | 17 | 17 | +0.000294593 | +0.000128562 | true |
| m317_continuity_surface | 17 | 17 | +0.000489393 | +0.000208808 | true |
| m314_continuity_surface | 17 | 17 | +0.000489915 | +0.000209009 | true |

## Old-Key Neighborhood Gate

M351 is the old-key neighborhood proof source for this alpha:

```text
runs/m351_old_key_neighborhood_alpha_sweep/gates_with_diagnostic/m351_a0075/summary.json
```

`m351_a0075` passes with `0` accepted regressions, gap p10 `-0.000018`, and
gap min `-0.000048`. `alpha=0.01` is the first failing alpha.

## Public Replay Gates

All six public replay gates pass versus `m333_base`.

| Surface | Rows | Success drops retained | Normal margin delta | Margin gap delta | Pass |
| --- | ---: | ---: | ---: | ---: | --- |
| M183/M168 | 16 | 16 / 16 | +0.000012060 | +0.000001951 | true |
| M183/M170 | 17 | 17 / 17 | +0.000011870 | +0.000002073 | true |
| M193/M189 | 14 | 14 / 14 | +0.000010332 | +0.000006181 | true |
| M212/M204 | 17 | 17 / 17 | +0.000010110 | +0.000005948 | true |
| M223/M219 | 17 | 17 / 17 | +0.000010114 | +0.000005946 | true |
| M267/M264 | 17 | 17 / 17 | +0.000010120 | +0.000005951 | true |

Replay run root:

```text
runs/m352_full_public_gate_for_m351_a0075/full_gates
```

## Behavior Retention

Behavior is retained on both public behavior seeds.

| Seed | Policy | Success | Termination | Mean clearance margin | Return |
| ---: | --- | ---: | ---: | ---: | ---: |
| 9505 | m333_base | 0.8625 | 0.1375 | 1.835798 | 65.942123 |
| 9505 | m351_a0075 | 0.8625 | 0.1375 | 1.835795 | 65.941584 |
| 9505 | m351_a0075_reset | 0.8500 | 0.1500 | 1.834315 | 64.031152 |
| 9505 | m351_a0075_zero_all | 0.8000 | 0.2000 | 1.852955 | 61.058115 |
| 9506 | m333_base | 0.8625 | 0.1375 | 1.853285 | 66.218397 |
| 9506 | m351_a0075 | 0.8625 | 0.1375 | 1.853281 | 66.217861 |
| 9506 | m351_a0075_reset | 0.8500 | 0.1500 | 1.850594 | 64.321032 |
| 9506 | m351_a0075_zero_all | 0.8000 | 0.2000 | 1.870837 | 61.320959 |

The candidate keeps public behavior success and termination equal to `m333_base`
while preserving the reset and zero-all ablation ordering.

## Interpretation

M352 promotes the M351 `alpha=0.0075` bounded short-PPO candidate as the new
public-gate base.

The result is conservative. M351's repaired endpoint had much stronger exact
objective improvement, but source-diverse and old-key neighborhood gates
rejected it. The accepted alpha is therefore a proof-safe interpolation, not
the raw repaired endpoint.

The next step should be a fresh-seed repeat design from this base before any
longer PPO escalation.

## Decision

Promote:

```text
runs/m351_m349_to_repaired_old_key_neighborhood_interpolation/checkpoints/alpha_0_0075.pt
```

Decision:

```text
promote_m351_a0075_old_key_neighborhood_public_gate_base
```

Next:

```text
m353-old-key-neighborhood-ppo-fresh-seed-repeat-design
```
