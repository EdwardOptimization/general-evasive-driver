# M406 Recovery-Aware Exact Projection Probe

M406 tests the M405 projection idea without PPO, promotion, threshold changes,
or actor-input changes. The question is whether a recovery-heavy raw proposal
can be projected back to exact M297/M270/old-key feasibility while retaining
movement toward the M398 old-key normal-margin recovery target.

## Candidate

Base public-gate checkpoint:

```text
runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
```

Recovery-heavy raw checkpoint:

```text
runs/m403_lrec1e10_interpolation/checkpoints/alpha_0_1.pt
```

Projection run:

```text
runs/m406_repair_from_alpha01_s40_seed10137
```

The projection uses `repair_from_raw`, M297/M270/old-key exact no-regression,
the M398 old-key recovery corpus, and the M393 current-family conflict corpus.

## Exact And Recovery Result

The selected checkpoint is:

```text
runs/m406_repair_from_alpha01_s40_seed10137/candidate_checkpoint.pt
```

| Metric | Value |
| --- | ---: |
| exact M297 delta vs M400 base | `-0.000065565` |
| exact M270 delta vs M400 base | `-0.000099480` |
| old-key surrogate delta vs M400 base | `-0.000290871` |
| exact lexicographic pass | `true` |
| old-key recovery loss, base | `0.003873642` |
| old-key recovery loss, candidate | `0.002919361` |

Action movement toward the M398 recovery targets also improves:

| Case | Base distance | Candidate distance | Delta |
| --- | ---: | ---: | ---: |
| `9958|perturbed|39|36|9.500000|-1.200000|0.900000` | `0.107793` | `0.093004` | `-0.014789` |
| `10004|perturbed|31|31|9.500000|-1.000000|0.800000` | `0.107808` | `0.091358` | `-0.016450` |

This means the projection does not collapse to the base. It is exact-feasible
and moves toward the intended local recovery action.

## Closed-Loop Replay Result

M267/M264 first replay fails:

```text
runs/m406_a01proj_m267_m264_first_replay
```

| Metric | Value |
| --- | ---: |
| normal success rate | `1.000000` |
| wrong-history success rate | `0.941176` |
| retained success drops | `1 / 17` |
| success-drop delta | `-16` |
| gate pass | `false` |

Cumulative old-key compact replay also fails:

```text
runs/m406_a01proj_old_key_replay_gate
```

| Metric | Value |
| --- | ---: |
| accepted regressions | `7` |
| normal-success regressions | `1` |
| candidate gap p10 | `-0.000947750` |
| candidate gap min | `-0.016869781` |
| overall pass | `false` |

So the candidate is exact-feasible but not replay-feasible.

## Conservative Variant

A more conservative variant increases current-family conflict and action-anchor
pressure:

```text
runs/m406_repair_from_alpha01_conservative_s40_seed10138
```

It does not produce an exact-feasible candidate. Best-feasible selection returns
step `0`, which is still the raw alpha `0.1` checkpoint:

| Metric | Value |
| --- | ---: |
| exact M297 delta vs base | `+0.000061750` |
| exact M270 delta vs base | `+0.000037313` |
| exact lexicographic pass | `false` |

This suggests the M406 failure is not just a weak current-family-conflict
coefficient. Stronger anchoring can block exact restoration, while the
exact-feasible projection still fails closed-loop replay.

## Classification

Primary blocker:

```text
exact_feasible_replay_infeasible
```

Harness failure labels:

```text
objective_overfit
proof_washout
protected_key_window_failure
```

M406 rejects the projection candidate. Exact corpus objectives are not
sufficient as replay proof proxies in this region: they allow a candidate that
makes the current-family wrong-history branch safe and creates old-key accepted
regressions.

## Decision

Do not promote and do not run PPO. The next step should audit the failed replay
rows before adding another scalar residual:

```text
m407-m406-projection-replay-failure-row-audit
```
