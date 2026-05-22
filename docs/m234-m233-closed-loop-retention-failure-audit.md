# M234 M233 Closed-Loop Retention Failure Audit

M234 audits why M233 failed after adding the protected key to the combined
snippet/action-anchor corpus. No PPO is run in this milestone.

Actor inputs are unchanged.

## M233 Failure Summary

M233 retained broad behavior but failed proof retention:

| Gate | Result |
| --- | --- |
| fixed M232 objective | worse than M224 and M229 |
| fixed M223 objective | essentially equal to M224, worse than M229 |
| M183 M168 replay | pass |
| M183 M170 replay | fail, `16 / 17` drops retained |
| M193 M189 replay | pass |
| M212 M204 replay | pass |
| M223 M219 replay | pass |
| behavior seeds 9505/9506 | pass |
| protected key 9944 | fail |

The failure taxonomy is:

```text
proof_washout
protected_key_window_failure
promotion_gate_failure
```

## First-Action Anchor Audit

M233 did not fail because the M232 snippet action anchor was absent. Training
logged:

```text
snippet_action_anchor_loss_mean = 4.320292e-08
```

A direct M224-vs-M233 first-action audit on the M232 combined corpus found:

| Metric | Value |
| --- | ---: |
| rows | 18 |
| action MSE mean | 8.986473e-07 |
| action MSE max | 1.630216e-06 |
| action L2 mean | 0.001632 |
| action L2 max | 0.002211 |
| protected-key action L2 | 0.001771 |

So the first-action anchor is nearly satisfied.

## Failed M183 M170 Row

The failed replay row is:

| Field | Value |
| --- | --- |
| row id | 16 |
| target | future_braking_deceleration |
| physical pair | 9530:6:9550:6 |
| geometry | x=13.878356, y=0.190667, half_width=0.728162 |

M224 barely completes the row:

| Policy | Normal success | Normal margin | Terminal reason |
| --- | --- | ---: | --- |
| m224_10063 | true | 0.000106 | obstacle_completed |
| m233_5220 | false | -0.000169 | collision |

The margin moved by only:

```text
-0.000275
```

The first normal action also changed only slightly:

| Metric | Value |
| --- | ---: |
| M224-vs-M233 first-action L2 | 0.002343 |
| steer delta | 0.001397 |
| throttle delta | -0.001304 |
| brake delta | -0.001355 |

This row is so close to the boundary that a tiny closed-loop policy change is
enough to flip the terminal outcome.

## Protected Key

M231 added the protected key to the anchor corpus:

```text
9944|perturbed|28|28
```

M233 still fails the guard:

| Policy | Accepted | Normal margin | Wrong-history margin | Gap |
| --- | ---: | ---: | ---: | ---: |
| m224_10063 | 1 / 1 | 0.186385 | 0.086925 | 0.099460 |
| m229_5219 | 0 / 1 | 0.205200 | 0.106179 | 0.099021 |
| m233_5220 | 0 / 1 | 0.204645 | 0.104993 | 0.099652 |

M233 improves the protected-key normal margin slightly relative to M229 but
still leaves the near-boundary window:

```text
0.204645 > 0.2
```

This is not unsafe behavior on that row; it is a proof-surface failure because
the row no longer remains in the pre-registered near-boundary window.

## Diagnosis

The M233 failure is closed-loop rollout drift, not missing coverage and not a
large first-action mismatch.

What M231/M232 fixed:

```text
The protected key is present in the training-time snippet corpus.
The first action at snippet states remains very close to M224.
```

What remains unfixed:

```text
Near-boundary replay rows require multi-step rollout retention.
Small action or hidden-state changes after the first action can move margins by
enough to break proof windows.
```

This explains why M233 can show near-zero snippet anchor loss but still fail
M183 M170 and the protected key.

## Decision

Do not repeat or lengthen M233.

Current best remains:

```text
runs/m224_m219_actor_coupling_snippet_pref_anchor100_s10_lr5e5_seed10063/optimized_checkpoint.pt
```

The next repair should move from single-decision snippet anchoring to
closed-loop trajectory retention.

## Next Step

Pre-register M235:

```text
m235-closed-loop-trajectory-anchor-surface-export
```

M235 should export a deployable multi-step trajectory anchor surface from M224
for the fragile replay/protected rows before any new PPO. At minimum it should
include:

- the failed M183 M170 row `16`;
- the protected key `9944|perturbed|28|28`;
- preferably the full M183 M170 replay surface and current M223 surface.

The goal is to anchor not just the first action at a decision snapshot, but the
teacher-forced action sequence along the protected rollout.
