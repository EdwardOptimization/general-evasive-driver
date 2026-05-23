# M328 Full Public Gate For M327 Source-Diverse Repaired

M328 runs the full public promotion gate for the M327 exact-repaired PPO
proposal under the M324 source-diverse protected policy. No PPO, actor update,
or actor-input change was performed in M328.

## Candidate

Current public-gate base:

```text
runs/m316_exact_repair_from_raw_s40_seed10096/candidate_checkpoint.pt
```

Candidate:

```text
runs/m327_exact_repair_from_raw_s40_seed10097/candidate_checkpoint.pt
```

## Exact Objectives

Exact objective retention versus M325:

| Objective | Delta |
| --- | ---: |
| Exact M297 rejected-history preference | -0.000104308 |
| Exact M270 source-balanced outcome | -0.000066042 |

Both exact objectives pass no-regression.

Run dir:

```text
runs/m328_m327_repaired_exact_eval_vs_m325
```

## Source-Diverse Protected Gate

Run dir:

```text
runs/m328_source_diverse_protected_gate
```

All three source-diverse protected replay gates pass.

| Replay gate | Rows | Baseline drops | Candidate drops | Normal margin delta | Margin gap delta | Pass |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| current_repaired_surface | 17 | 17 | 17 | +0.000193834 | +0.000084878 | true |
| m317_continuity_surface | 17 | 17 | 17 | +0.000388630 | +0.000165122 | true |
| m314_continuity_surface | 17 | 17 | 17 | +0.000389153 | +0.000165322 | true |

## Public Replay Gates

All six public replay gates pass versus M325.

| Surface | Rows | Success drops retained | Normal margin delta | Margin gap delta | Pass |
| --- | ---: | ---: | ---: | ---: | --- |
| M183/M168 | 16 | 16 / 16 | +0.000223834 | +0.000029037 | true |
| M183/M170 | 17 | 17 / 17 | +0.000220939 | +0.000030599 | true |
| M193/M189 | 14 | 14 / 14 | +0.000195348 | +0.000087958 | true |
| M212/M204 | 17 | 17 / 17 | +0.000193739 | +0.000084821 | true |
| M223/M219 | 17 | 17 / 17 | +0.000193786 | +0.000084848 | true |
| M267/M264 | 17 | 17 / 17 | +0.000193843 | +0.000084890 | true |

Replay run root:

```text
runs/m328_full_public_gate_for_m327_repaired/full_gates
```

## Old 9944 Diagnostic

Old protected key `9944|perturbed|28|28` remains a diagnostic singleton.

| Policy | Pass | Normal margin | Wrong-history margin | Margin gap |
| --- | --- | ---: | ---: | ---: |
| m263_a005 | true | 0.199909 | 0.099300 | 0.100609 |
| m325_base | false | 0.207388 | 0.110406 | 0.096982 |
| m327_repaired | false | 0.213944 | 0.121291 | 0.092653 |
| m239_a750 | false | 0.200336 | 0.099817 | 0.100519 |

The candidate fails the old singleton normal-margin window but retains a
positive margin gap:

```text
margin_gap = 0.09265276126719213
M324 diagnostic floor = 0.09
```

Classification:

```text
single_key_window_saturation
```

## Behavior Retention

Behavior is retained on both public behavior seeds.

| Seed | Policy | Success | Termination | Mean clearance margin | Return |
| ---: | --- | ---: | ---: | ---: | ---: |
| 9505 | m325_base | 0.8625 | 0.1375 | 1.835825 | 65.950647 |
| 9505 | m327_repaired | 0.8625 | 0.1375 | 1.835793 | 65.946706 |
| 9505 | m327_repaired_reset | 0.8500 | 0.1500 | 1.834349 | 64.055481 |
| 9505 | m327_repaired_zero_all | 0.8000 | 0.2000 | 1.853026 | 61.016184 |
| 9506 | m325_base | 0.8625 | 0.1375 | 1.853332 | 66.226822 |
| 9506 | m327_repaired | 0.8625 | 0.1375 | 1.853285 | 66.222966 |
| 9506 | m327_repaired_reset | 0.8500 | 0.1500 | 1.850629 | 64.345355 |
| 9506 | m327_repaired_zero_all | 0.8000 | 0.2000 | 1.870914 | 61.278975 |

The candidate keeps public behavior success and termination equal to M325 while
preserving reset and zero-all ablation ordering.

## Interpretation

M328 promotes the M327 exact-repaired PPO proposal as the new public-gate base.

This validates the new acceptance stack:

```text
PPO proposal
  -> exact M297/M270 repair
  -> source-diverse protected gates
  -> old-key singleton-window audit
  -> first replay gates
  -> full public replay and behavior gates
```

The old `9944` key is still useful as a diagnostic, but it no longer forces
micro-alpha clipping when source-diverse protected proof and behavior retention
are intact.

The next step should repeat the smoke PPO process with a fresh seed before
lengthening training.

## Decision

Promote:

```text
runs/m327_exact_repair_from_raw_s40_seed10097/candidate_checkpoint.pt
```

Decision:

```text
promote_m327_source_diverse_repaired_public_gate_base
```

Next:

```text
m329-source-diverse-ppo-fresh-seed-repeat-design
```
