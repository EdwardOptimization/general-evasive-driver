# M325 Source-Diverse Policy Full Gate For M316 Repaired

M325 runs the full public gate for the M316 repaired endpoint under the M324
source-diverse protected policy. No PPO, actor update, or actor-input change was
performed.

## Candidate

Current public-gate base:

```text
runs/m316_m314_to_repaired_protected_key_bounded_interpolation/checkpoints/alpha_0_0025.pt
```

Candidate:

```text
runs/m316_exact_repair_from_raw_s40_seed10096/candidate_checkpoint.pt
```

## Exact Objectives

Exact objective retention versus M317:

| Objective | Delta |
| --- | ---: |
| Exact M297 rejected-history preference | -0.000116587 |
| Exact M270 source-balanced outcome | -0.000075817 |

Both exact objectives pass no-regression.

Run dir:

```text
runs/m325_m316_repaired_exact_eval_vs_m317
```

## Source-Diverse Protected Gate

Run dir:

```text
runs/m325_source_diverse_policy_gate
```

The M320 source-diverse protected bundle passes.

| Replay gate | Rows | Baseline | Candidate | Baseline drops | Candidate drops | Normal margin delta | Margin gap delta | Pass |
| --- | ---: | --- | --- | ---: | ---: | ---: | ---: | --- |
| current_vs_repaired | 17 | m317_base | m316_repaired | 17 | 17 | +0.000194793 | +0.000080242 | true |
| previous_vs_repaired | 17 | m314_base | m316_repaired | 17 | 17 | +0.000195316 | +0.000080442 | true |

Aggregate:

| Metric | Value |
| --- | ---: |
| replay gates passed | 2 / 2 |
| overall pass | true |

## Public Replay Gates

All six public replay gates pass versus M317.

| Surface | Rows | Success drops retained | Normal margin delta | Margin gap delta | Pass |
| --- | ---: | ---: | ---: | ---: | --- |
| M183/M168 | 16 | 16 / 16 | +0.000222247 | +0.000028723 | true |
| M183/M170 | 17 | 17 / 17 | +0.000219592 | +0.000030117 | true |
| M193/M189 | 14 | 14 / 14 | +0.000196997 | +0.000083475 | true |
| M212/M204 | 17 | 17 / 17 | +0.000194697 | +0.000080187 | true |
| M223/M219 | 17 | 17 / 17 | +0.000194741 | +0.000080210 | true |
| M267/M264 | 17 | 17 / 17 | +0.000194803 | +0.000080254 | true |

Replay run root:

```text
runs/m325_full_public_gate_for_m316_repaired/full_gates
```

## Old 9944 Diagnostic

Old protected key `9944|perturbed|28|28` is retained as a diagnostic singleton.

| Policy | Pass | Accepted cases | Normal margin | Wrong-history margin | Margin gap |
| --- | --- | ---: | ---: | ---: | ---: |
| m263_a005 | true | 1 / 1 | 0.199909 | 0.099300 | 0.100609 |
| m317_base | true | 1 / 1 | 0.199995 | 0.100123 | 0.099873 |
| m316_repaired | false | 0 / 1 | 0.207388 | 0.110406 | 0.096982 |
| m239_a750 | false | 0 / 1 | 0.200336 | 0.099817 | 0.100519 |

The candidate fails the old normal-margin window, but it retains a positive
wrong-history gap:

```text
margin_gap = 0.09698219356079285
M324 diagnostic floor = 0.09
```

This is classified as:

```text
single_key_window_saturation
```

not broad proof washout.

## Behavior Retention

Behavior is retained on both public behavior seeds.

| Seed | Policy | Success | Termination | Mean clearance margin | Return |
| ---: | --- | ---: | ---: | ---: | ---: |
| 9505 | m317_base | 0.8625 | 0.1375 | 1.835825 | 65.958933 |
| 9505 | m316_repaired | 0.8625 | 0.1375 | 1.835825 | 65.950647 |
| 9505 | m316_repaired_reset | 0.8500 | 0.1500 | 1.834436 | 64.030890 |
| 9505 | m316_repaired_zero_all | 0.8000 | 0.2000 | 1.853180 | 61.013941 |
| 9506 | m317_base | 0.8625 | 0.1375 | 1.853346 | 66.235065 |
| 9506 | m316_repaired | 0.8625 | 0.1375 | 1.853332 | 66.226822 |
| 9506 | m316_repaired_reset | 0.8500 | 0.1500 | 1.850719 | 64.320744 |
| 9506 | m316_repaired_zero_all | 0.8000 | 0.2000 | 1.871081 | 61.276593 |

The candidate keeps public behavior success and termination equal to M317 while
preserving the reset and zero-all ablation ordering.

## Interpretation

M325 promotes the M316 repaired endpoint under the M324 source-diverse protected
policy.

This is the first promotion that explicitly treats old `9944` as a diagnostic
singleton rather than the sole hard protected-surface veto. The promotion is not
based on source-diverse proof alone: exact M297/M270, source-diverse proof, all
six public replay gates, old-key audit, behavior seeds, and input-contract
checks all pass.

This promotion removes the M317 micro-alpha bottleneck. The next PPO proposal
should use M325 as base and apply exact repair plus source-diverse protected
acceptance before any longer training.

## Decision

Promote:

```text
runs/m316_exact_repair_from_raw_s40_seed10096/candidate_checkpoint.pt
```

Decision:

```text
promote_m316_repaired_source_diverse_public_gate_base
```

Next:

```text
m326-source-diverse-protected-ppo-proposal-design
```
