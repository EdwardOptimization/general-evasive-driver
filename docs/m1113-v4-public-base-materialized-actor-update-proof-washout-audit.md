# M1113 V4 Public Base Materialized Actor Update Proof Washout Audit

## Purpose

M1113 audits the M1112 full-public-gate failure before any new actor update,
replay, PPO, promotion, private holdout, or backup-candidate retry.

The audit reads existing M1112 artifacts only.

## M1112 Failure Recap

M1112 rejected `m1110_110901`:

```text
M1107 exact recheck: pass
actor-input contract: pass
allowed changed-parameter surface: pass
old public replay: fail, 3 / 6 surfaces pass
M1061 family-intersection: fail, 0 / 3 gates pass
source-diverse replay: fail, 0 / 3 gates pass
fresh/OOD: pass
behavior: pass
```

The failed candidate should not be promoted and should not be used as a PPO
base.

## Row-Level Failure Mode

Across the failed replay gates, the lost success-drop rows have a consistent
shape:

```text
normal_lost: 0
wrong_history_safe: all lost rows
```

Old public replay lost rows:

| Surface | Lost success drops | Normal lost | Wrong-history safe |
| --- | ---: | ---: | ---: |
| `m183_m168` | 1 | 0 | 1 |
| `m223_m219` | 1 | 0 | 1 |
| `m267_m264` | 6 | 0 | 6 |

Family-intersection lost rows:

| Surface | Lost success drops | Normal lost | Wrong-history safe |
| --- | ---: | ---: | ---: |
| `short61049` | 8 | 0 | 8 |
| `short61050` | 10 | 0 | 10 |
| `short61051` | 10 | 0 | 10 |

Source-diverse lost rows:

| Surface | Lost success drops | Normal lost | Wrong-history safe |
| --- | ---: | ---: | ---: |
| `current_m333_surface` | 3 | 0 | 3 |
| `m317_continuity_surface` | 4 | 0 | 4 |
| `m314_continuity_surface` | 4 | 0 | 4 |

Total failed gate-row events:

```text
lost_success_drop_events: 47
normal_lost_events: 0
wrong_history_safe_events: 47
```

## Margin Direction

The failed rows are near boundary. The candidate moves wrong-history margins
from slightly negative to slightly positive.

Examples:

| Surface | Base wrong-history margin mean | Candidate wrong-history margin mean |
| --- | ---: | ---: |
| `m267_m264` lost rows | -0.001571 | +0.001103 |
| `current_m333_surface` lost rows | -0.001664 | +0.000949 |
| `m314_continuity_surface` lost rows | -0.001741 | +0.000890 |
| `m317_continuity_surface` lost rows | -0.001742 | +0.000889 |

This is exactly the proof-washout pattern: normal-history rollouts remain
successful, while wrong-history rollouts no longer fail.

## Target And Pair Pattern

Old public and source-diverse failures are dominated by
`future_braking_deceleration` rows. Family-intersection failures also include
`future_lateral_accel_response` and one `future_yaw_response` row per short-PPO
source family.

Repeated failed physical pairs include:

```text
9530:15:9550:18
9537:24:9561:24
9530:21:9550:21
105422:24:105440:27
105426:15:105427:15
105422:27:105434:39
```

The failure is not a single-row artifact; it appears across old public,
family-intersection, and source-diverse surfaces.

## Interpretation

M1110's materialized objective successfully moved the allowed action surface and
kept aggregate behavior intact, but it optimized the wrong-history branch in the
wrong direction for proof retention.

The M1107 objective plus rollout action anchor plus snippet action anchor is
therefore insufficient. It improves exact one-step objective metrics but does
not preserve closed-loop rejected-history trajectory failure.

This repeats the older M279-M286 lesson in the current materialized branch:

```text
first-action/objective improvement can repair the preferred branch
while accidentally making the rejected branch safe.
```

## Rejected Alternatives

Do not route to:

```text
backup M1110 candidate retry
larger M1107 objective weight
longer actor update
PPO continuation
promotion
private holdout
threshold weakening
```

Those would optimize around the failed proof gate instead of fixing the missing
closed-loop rejected-history constraint.

## Next Repair Direction

The next branch should design a failed wrong-history trajectory-retention
surface using the M1112 failed rows.

The repair target should preserve:

```text
normal-history success
wrong-history failure on failed rows
wrong-history trajectory/action behavior from the base
exact M1107 objective no-regression if possible
allowed actor-coupling parameter surface
```

The first next step should be design-only. It should not export a corpus yet and
should not run another actor update.

## Decision

```text
materialized_actor_update_proof_washout_audit_route_to_failed_wrong_history_retention_design
```

Next milestone:

```text
m1114-v4-public-base-materialized-failed-wrong-history-retention-design
```
