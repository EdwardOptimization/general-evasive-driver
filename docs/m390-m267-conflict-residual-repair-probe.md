# M390 M267 Conflict Residual Repair Probe

M390 tests the M389 current-family conflict residual in a no-PPO repair probe.
It does not promote a checkpoint, lower thresholds, or change the actor
input/output contract.

## Inputs

Current public-gate base:

```text
runs/m385_recovery_repair_micro_interpolation/checkpoints/alpha_0_00075.pt
```

Conflict corpus:

```text
runs/m389_m267_row15_conflict_corpus/current_family_conflict_corpus.npz
```

Supporting corpora:

```text
runs/m384_old_key_local_recovery_targets/old_key_recovery_corpus.npz
runs/m377_cumulative_gap_tail_v2_old_key_preference_corpus/old_key_preference_corpus.npz
runs/m297_current_family_rejected_preference_objective/rejected_history_preference_corpus.npz
runs/m270_source_balanced_multi_surface_anchor/outcome_intervention_snippets.npz
```

## Repair Proposal

M390 first ran exact repair from the M386 base with:

```text
lambda_current_family_conflict = 1e9
lambda_current_family_conflict_rejected = 4.0
lambda_old_key_recovery = 1000
steps = 80
```

The automatic best-feasible selector stayed at step `0`, because the large
conflict coefficient makes total loss prefer the unchanged base. The training
trace still showed feasible intermediate steps with old-key surrogate
improvement. Step `17` was exported as a candidate:

```text
runs/m390_conflict_repair_step17_lconf1e9_seed10127/candidate_checkpoint.pt
```

Exact metrics for step `17`:

| Metric | Delta vs M386 base |
| --- | ---: |
| exact M297 | -0.000216603 |
| exact M270 | -0.000045002 |
| old-key surrogate | -0.001273155 |
| exact lexicographic pass | true |

But closed-loop M267/M264 rejects the step17 endpoint:

| Candidate | M267/M264 success drops | Gate |
| --- | ---: | --- |
| step17 endpoint | 15 / 17 | fail |

Rows `6` and `15` become wrong-history successes at the endpoint.

## Bounded Interpolation

M390 interpolated from the M386 base to the step17 endpoint.

The active M267/M264 gate is extremely tight:

| Alpha | M267/M264 success drops | Gate |
| ---: | ---: | --- |
| 0.0005 | 17 / 17 | pass |
| 0.0010 | 17 / 17 | pass |
| 0.0025 | 17 / 17 | pass |
| 0.0050 | 17 / 17 | pass |
| 0.0100 | 16 / 17 | fail |

Alpha `0.01` fails on row `15`, whose wrong-history margin crosses to a small
positive value. The selected proof candidate is therefore:

```text
runs/m390_step17_micro_interpolation/checkpoints/alpha_0_005.pt
```

## Exact Evaluation

Run dir:

```text
runs/m390_step17_a005_exact_eval
```

| Metric | Delta / Value |
| --- | ---: |
| exact M297 delta | -0.000001192 |
| exact M270 delta | -0.000000298 |
| old-key surrogate delta | -0.000006199 |
| old-key recovery loss | 0.002263937 |
| current-family conflict loss | 1.732642e-12 |
| exact lexicographic pass | true |

The exact improvement is small, but it is nonzero and remains within the
lexicographic proof constraints.

## Proof Gates

M267/M264 first replay:

```text
runs/m390_step17_micro005_m267_m264_first_replay
```

| Metric | Value |
| --- | ---: |
| gate pass | true |
| success drops retained | 17 / 17 |
| wrong-history success rate | 0 |
| normal margin delta | +0.000000851 |
| margin gap delta | +0.000000011 |

Cumulative old-key replay:

```text
runs/m390_step17_a005_old_key_replay_gate
```

| Metric | Value |
| --- | ---: |
| overall pass | true |
| accepted regressions | 0 |
| normal-success regressions | 0 |
| gap p10 | -0.000001447 |
| gap min | -0.000009425 |

Source-diverse protected gate:

```text
runs/m390_step17_a005_source_diverse_protected_gate
```

| Metric | Value |
| --- | ---: |
| overall pass | true |
| replay gates passed | 5 / 5 |

M183/M170 first replay:

```text
runs/m390_step17_a005_m183_m170_first_replay
```

| Metric | Value |
| --- | ---: |
| gate pass | true |
| success drops retained | 17 / 17 |
| wrong-history success rate | 0 |
| normal margin delta | +0.000000819 |
| margin gap delta | -0.000000129 |

## Interpretation

The conflict residual did not make the full step17 repair endpoint safe. It
still washes out current-family wrong-history proof at ordinary scale. However,
it gives a bounded direction that improves exact old-key objectives while
preserving the active proof surfaces up to alpha `0.005`.

This is still a micro proof-safe movement, not a behavior claim. Because M390
passes exact, M267/M264, cumulative old-key, source-diverse, and M183/M170
proof gates, it admits a full public gate before any promotion.

## Decision

Admit:

```text
m391-full-public-gate-for-m390-a005
```

Decision:

```text
admit_m391_full_public_gate_for_m390_a005
```
