# M1032 V4 Public Base Candidate B Temporal Projection First-Replay Failure Audit

## Purpose

M1032 audits the M1031 temporal-safe projection failure before any new repair,
PPO, promotion, private holdout, or actor-input change.

The question is:

```text
Why did M1031 find temporal/exact-safe projected candidates that can pass
M267/M264, but no candidate that also passes M183/M170?
```

## Parent Result

M1031 evaluated `39` projected checkpoints from the three M1029 repair
directions.

```text
temporal_exact_pass_count: 16
temporal_and_exact_pass_count: 16
eligible_candidate_count: 14
first_replay_attempted_candidate_count: 14
first_replay_pass_candidate_found: false
actor_input_change_count: 0
```

M1031 classification:

```text
candidate_b_temporal_safe_projection_proof_washout
```

## Exact Layer Diagnosis

M1031 is not blocked by M997 temporal exact retention after projection:

| Source | Eligible alphas |
| --- | --- |
| raw_conflict_s40 | 0.05, 0.10, 0.15, 0.20, 0.25, 0.30 |
| base_conflict_s40 | 0.10, 0.15, 0.20, 0.25 |
| line_conflict_s40 | 0.10, 0.15, 0.20, 0.25 |

It is also not blocked by M297/M270 exact no-regression:

```text
temporal_and_exact_pass_count: 16
eligible_candidate_count: 14
```

The exact layer can recover useful projected candidates. The failure appears
only after first replay.

## M267/M264 Result

M1031 shows that M267/M264 row15 can be retained.

Examples:

| Candidate | M267/M264 success drops | Row15 retained |
| --- | ---: | --- |
| base_conflict_s40 alpha 0.25 | 17/17 | true |
| line_conflict_s40 alpha 0.25 | 17/17 | true |
| raw_conflict_s40 alpha 0.15 | 17/17 | true |
| raw_conflict_s40 alpha 0.10 | 17/17 | true |
| raw_conflict_s40 alpha 0.05 | 17/17 | true |

This means the M1031 failure is not simply the original M267/M264 row15
wrong-history lift from M1026. Projection plus the M393 row15 conflict direction
can keep row15 rejected-history failing.

## M183/M170 Result

No eligible candidate passes M183/M170.

For most candidates, M183/M170 failure is broad normal-branch regression:

```text
base/line alpha 0.10-0.25:
  normal_successes: 3/17
  wrong_history_successes: 0/17
  failed rows: 1,3,4,5,6,7,8,9,10,11,12,13,14,16
```

The closest miss is raw-start alpha `0.05`:

```text
candidate: m1031_raw_conflict_s40_a0_05
M267/M264: 17/17 success drops, row15 retained
M183/M170: 16/17 success drops
failed row: 16
normal_success: false
wrong_history_success: false
normal_margin: -0.000165
wrong_history_margin: -0.006597
margin_gap: 0.006431
```

Baseline Candidate B on the same M183/M170 row16:

```text
normal_success: true
wrong_history_success: false
normal_margin: 0.001316
wrong_history_margin: -0.005084
margin_gap: 0.006400
```

First-action deltas for row16 are small:

```text
normal first action, Candidate B:
  steer 0.719287, throttle -0.223611, brake -0.010006

normal first action, raw alpha 0.05:
  steer 0.719968, throttle -0.222315, brake -0.011704
```

The terminal margin changes from `+0.001316` to `-0.000165`. This is a
near-boundary normal-branch terminal-margin cliff.

## Failure Classification

M1032 classifies M1031 as:

```text
M183/M170 normal-branch terminal-margin active-set failure
```

It is not:

```text
wrong-history sensitivity loss
```

because `wrong_history_successes` remain `0/17` on the inspected M183/M170
candidates and M183 row16 still has a healthy margin gap. The rejected branch is
not becoming safe; the normal branch is becoming unsafe.

It is not:

```text
pure M997 temporal action-drift failure
```

because M1031 has temporal exact-safe candidates and the closest miss has very
small temporal action drift.

It is partly:

```text
broad normal-branch regression for higher alphas
```

but the closest useful route is the low-alpha raw-start direction, where the
failure reduces to a single low-slack row16 normal branch.

## Route Decision

Do not run longer PPO.

Do not promote any M1031 projected checkpoint.

Do not relax M997 temporal thresholds.

The next milestone should design active-set first-replay retention for the
post-PPO repair/projection path:

```text
M1033: M183/M170 row16 active-set retention design
```

The design should make this row first-class before another repair run:

```text
hard active set:
  M997 temporal exact retention
  M297/M270 exact no-regression
  M267/M264 row15 rejected-history failure
  M183/M170 row16 normal success / terminal-margin retention

candidate utility:
  stay close to the useful M1026/M1029 repair direction
  keep enough M297/M270 improvement to avoid base-equivalent projection
```

The likely implementation route is to export a Candidate-B normal-trajectory
anchor for M183/M170 row16 and use it as a hard active-set retention term before
first replay. A finer low-alpha projection around raw alpha `< 0.05` can be a
diagnostic fallback, but it should not be the primary route unless the retained
movement remains nontrivial.

## Decision

```text
candidate_b_temporal_projection_first_replay_failure_audit_route_to_m183_row16_active_set_retention_design
```

Next milestone:

```text
m1033-v4-public-base-candidate-b-m183-row16-active-set-retention-design
```
