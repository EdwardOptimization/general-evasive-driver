# M357 M354 Best-Step Repair Proof Gate

M357 evaluates the M356 best-step repaired M354 candidate on the proof gates
that M354 skipped after its exact M270 failure. It does not run PPO and does
not promote a checkpoint.

## Candidate

Baseline public-gate base:

```text
runs/m351_m349_to_repaired_old_key_neighborhood_interpolation/checkpoints/alpha_0_0075.pt
```

M356 best-step repaired candidate:

```text
runs/m356_m354_repair_best_step_probe/candidate_checkpoint.pt
```

The candidate passes exact M297/M270 no-regression versus M352, but exact
objectives alone are not sufficient for promotion.

## Source-Diverse Protected Gate

Run dir:

```text
runs/m357_m354_best_step_source_diverse_protected_gate
```

Result:

```text
3 / 5 replay gates pass
failure_types = [proof_washout]
```

| Replay gate | Rows | Candidate drops | Gate |
| --- | ---: | ---: | --- |
| current_m333_surface | 17 | 17 | pass |
| m328_continuity_surface | 17 | 17 | pass |
| m325_continuity_surface | 17 | 17 | pass |
| m317_continuity_surface | 17 | 16 | fail |
| m314_continuity_surface | 17 | 16 | fail |

## Old-Key Neighborhood Gate

Targeted replay:

```text
runs/m357_m354_best_step_old_key_targeted_replay
```

Replayable adapter:

```text
runs/m357_m354_best_step_old_key_replay_gate
```

The candidate fails the old-key neighborhood gate:

| Metric | Value |
| --- | ---: |
| compact rows | 40 |
| accepted regressions | 15 |
| normal-success regressions | 3 |
| gap p10 | -0.004098 |
| gap min | -0.050838 |
| overall pass | false |

Failure type:

```text
protected_key_window_failure
```

## First Replay Gates

| Surface | Rows | Success drops retained | Gate |
| --- | ---: | ---: | --- |
| M183/M170 | 17 | 17 / 17 | pass |
| M267/M264 | 17 | 15 / 17 | fail |

The M267/M264 failure is not a normal-history failure. Normal success remains
`17/17`, but wrong-history success increases to `2/17`, reducing success-drop
evidence.

## Interpretation

M357 is negative. M356 fixed exact-repair endpoint selection, but the repaired
M354 candidate is still too large for the proof surfaces. The failure pattern
matches the earlier repaired-endpoint problem:

```text
exact objectives pass,
but source-diverse/old-key/wrong-history proof is washed out.
```

The M356 candidate remains useful as a direction, not as a directly acceptable
checkpoint.

## Decision

Reject direct proof-gate acceptance:

```text
runs/m356_m354_repair_best_step_probe/candidate_checkpoint.pt
```

Decision:

```text
reject_m354_best_step_proof_washout
```

Next:

```text
m358-m354-best-step-bounded-interpolation-probe
```
