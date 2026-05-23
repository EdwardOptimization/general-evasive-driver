# M311 Full Public Gate For M310 Repaired PPO Proposal

M311 runs the full public promotion gate for the M310 exact-repaired PPO
proposal. Actor inputs are unchanged.

Candidate:

```text
runs/m310_exact_repair_from_raw_s40_seed10095/candidate_checkpoint.pt
```

Current public-gate base:

```text
runs/m306_exact_repair_from_raw_s40_seed10091/candidate_checkpoint.pt
```

## Exact Objectives

M310 already passed exact no-regression versus M307:

| Objective | M307 base | M310 repaired | Delta |
| --- | ---: | ---: | ---: |
| Exact M297 rejected-history preference | 1.189483285 | 1.189360261 | -0.000123024 |
| Exact M270 source-balanced outcome | 0.677865505 | 0.677787662 | -0.000077844 |

## Replay Gates

All six public replay gates pass versus M307.

| Surface | Rows | Success drops retained | Normal success | Normal margin delta | Margin gap delta | Pass |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| M183/M168 | 16 | 16 / 16 | 1.000000 | +0.000210 | +0.000029 | true |
| M183/M170 | 17 | 17 / 17 | 1.000000 | +0.000207 | +0.000030 | true |
| M193/M189 | 14 | 14 / 14 | 1.000000 | +0.000186 | +0.000083 | true |
| M212/M204 | 17 | 17 / 17 | 1.000000 | +0.000183 | +0.000080 | true |
| M223/M219 | 17 | 17 / 17 | 1.000000 | +0.000183 | +0.000080 | true |
| M267/M264 | 17 | 17 / 17 | 1.000000 | +0.000184 | +0.000080 | true |

Replay run root:

```text
runs/m311_full_public_gate_for_m310_repaired/full_gates
```

## Protected Key

Protected key `9944|perturbed|28|28` fails for M310. The guard remains
discriminative because the reference and current public-gate base pass, while
the known failing `m239_a750` still fails.

Run dir:

```text
runs/m311_full_public_gate_for_m310_repaired/full_gates/critical_key_seed9944
```

| Policy | Pass | Accepted cases | Normal margin | Wrong-history margin | Margin gap |
| --- | --- | ---: | ---: | ---: | ---: |
| m263_a005 | true | 1 / 1 | 0.199909 | 0.099300 | 0.100609 |
| m307_base | true | 1 / 1 | 0.198863 | 0.098839 | 0.100023 |
| m310_repaired | false | 0 / 1 | 0.206337 | 0.108747 | 0.097590 |
| m239_a750 | false | 0 / 1 | 0.200336 | 0.099817 | 0.100519 |

The failure is not a broad replay proof washout: all replay surfaces retained
normal-history success and wrong-history failure. The protected key failure is
more consistent with a protected-key window/saturation issue: M310 increases
both normal and wrong-history margins on the protected key and lands outside
the accepted protected-key criterion.

## Behavior Gate

Behavior seeds `9505` and `9506` were not run. Promotion stops at the
protected-key gate, so running behavior would not change the promotion
decision.

## Interpretation

M310 repaired is rejected as a promotable public-gate base. The exact repair
workflow is still useful because it converted a raw PPO proposal that regressed
exact objectives into a candidate that improved exact M297/M270 and retained
six replay surfaces. But the full gate exposed a protected-key regression that
was not represented in the exact repair objective.

The next milestone should audit whether this is:

```text
1. a stale singleton protected-key window issue,
2. a systematic protected-key margin shift caused by exact repair,
3. a missing protected-key term in the exact repair objective.
```

## Decision

Reject:

```text
runs/m310_exact_repair_from_raw_s40_seed10095/candidate_checkpoint.pt
```

Decision:

```text
reject_m310_repaired_protected_key_window_failure
```

Next:

```text
m312-m310-protected-key-window-failure-audit
```
