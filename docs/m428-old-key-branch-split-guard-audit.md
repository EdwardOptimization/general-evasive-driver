# M428 Old-Key Branch-Split Guard Audit

M428 audits the old-key failures from M427. It does not run PPO, promote a
checkpoint, lower thresholds, or change actor inputs.

## Summary

M427 is not a dead end. It improves recovery utility and preserves M267/M264,
but the M426 hard-guard set is incomplete for old-key replay.

M427 old-key compact result:

```text
accepted cases: 36 / 40
normal-success cases: 38 / 40
```

The four failures split into three mechanisms:

| Key | Mechanism | Required change |
| --- | --- | --- |
| `10004|perturbed|31|31` | wrong-history branch became safe | split normal recovery from rejected-history guard |
| `10023|perturbed|12|12` | old-key gap erosion | keep as hard guard and report branch-specific loss |
| `9872|perturbed|21|18` | normal-branch collision on two compact cases | add normal-branch hard guard |

## Failure Details

### `10004`

M427 improves the normal branch but also makes wrong-history safe:

| Policy | Normal margin | Wrong-history margin | Accepted |
| --- | ---: | ---: | --- |
| M400 base | `0.000098797` | `-0.000699856` | true |
| M427 projected | `0.001654052` | `0.000953258` | false |

This row was excluded from the M426 hard guard so that normal-history recovery
could move. That was too coarse. The correct structure is branch-split:

```text
10004 normal branch: recovery utility may move it
10004 rejected branch: hard guard must keep wrong-history unsafe
```

### `10023`

M427 keeps normal success, but gap erodes enough to fail the compact gate:

| Policy | Normal margin | Wrong-history margin | Gap |
| --- | ---: | ---: | ---: |
| M400 base | `0.049016728` | `0.046926326` | `0.002090402` |
| M427 projected | `0.048193868` | `0.046255871` | `0.001937996` |

`10023` was already in the hard guard, so the next guard should expose
branch-specific loss reporting rather than only aggregate source loss.

### `9872`

Both compact cases fail by normal-branch collision:

| Target | M400 normal margin | M427 normal margin | M427 wrong-history margin |
| --- | ---: | ---: | ---: |
| `12.0, -1.2, 1.2` | `0.001953651` | `-0.000458062` | `-0.007648332` |
| `12.5, -0.8, 1.3` | `0.001807117` | `-0.000753041` | `-0.008037479` |

This is not wrong-history washout. It is a normal branch cliff that was not in
the M426 hard guard.

## Interpretation

The projected recovery objective is doing useful work:

- exact gates pass;
- M267/M264 remains `17 / 17`;
- recovery retained rises from M423 `mixed_b` `0.133154` to `0.174354`.

But the old-key guard must become branch-aware. A source-level anchor cannot
express “move normal branch toward recovery but keep rejected branch unsafe” on
`10004`.

## Decision

Admit implementation-only milestone:

```text
m429-branch-split-old-key-guard-implementation
```

M429 should export a hard guard with:

- M267 rows `6` and `15`;
- old-key `10023`;
- old-key spillovers `9951` and `9939`;
- `10004` rejected-history branch only;
- `9872` normal-branch rows.

It should not run PPO or promote a checkpoint.
