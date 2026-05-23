# M433 Selective 10004 Anchor Export

M433 implements and runs the M432 selective `10004` wrong-history anchor
export. It does not run PPO, promote a checkpoint, lower thresholds, or change
actor inputs.

## Code Changes

New module:

```text
src/autodrift/selective_10004_anchor.py
```

It exports profile anchors from the M429 branch-split hard guard:

- identifies the unique `10004|perturbed|31|31|9.5|-1.0|0.8` wrong-history
  source;
- updates only that source's radius or tail rows;
- leaves M426 base guards, `10023`, and `9872` rows unchanged;
- preserves at least one `10004` wrong-history guard in every profile;
- writes per-profile `selective_anchor.npz` and `selective_sources.csv`.

Tests:

```text
tests/test_selective_10004_anchor.py
```

Focused result:

```text
2 passed
```

## Export

Run directory:

```text
runs/m433_selective_10004_anchor_export
```

Profiles:

| Profile | Rows | `10004` rows | `10004` radius | Tail only |
| --- | ---: | ---: | ---: | --- |
| `r0005` | `357` | `37` | `0.0005` | false |
| `r0010` | `357` | `37` | `0.0010` | false |
| `r0015` | `357` | `37` | `0.0015` | false |
| `r0020` | `357` | `37` | `0.0020` | false |
| `tail_r0005` | `333` | `13` | `0.0005` | true |
| `tail_r0010` | `333` | `13` | `0.0010` | true |

All-row profiles keep the full 37-row `10004` wrong-history trajectory and only
change its radius. Tail profiles keep the final third of the `10004`
wrong-history trajectory and leave all other sources intact.

## No-Update Smokes

Each profile was loaded by `exact_post_ppo_repair` with `steps=0`, base and raw
both set to the current public-gate base:

```text
runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
```

All six no-update smokes pass:

| Profile | Exact pass | M297 delta | M270 delta | old-key delta | Anchor loss |
| --- | --- | ---: | ---: | ---: | ---: |
| `r0005` | true | `0.0` | `0.0` | `0.0` | `0.0` |
| `r0010` | true | `0.0` | `0.0` | `0.0` | `0.0` |
| `r0015` | true | `0.0` | `0.0` | `0.0` | `0.0` |
| `r0020` | true | `0.0` | `0.0` | `0.0` | `0.0` |
| `tail_r0005` | true | `0.0` | `0.0` | `0.0` | `0.0` |
| `tail_r0010` | true | `0.0` | `0.0` | `0.0` | `0.0` |

## Decision

Admit no-PPO projection probe:

```text
m434-selective-10004-projection-probe
```

M434 should run the M430 projected-recovery recipe across all six anchors,
then gate candidates in the same order:

1. exact M297/M270/old-key no-regression;
2. M267/M264 first replay `17 / 17`;
3. old-key compact replay `40 / 40`;
4. M183/M170 first replay `17 / 17`;
5. recovery retained vs M406.

No M434 candidate should be promoted directly. The purpose is to identify
whether a selective `10004` guard can beat M427's `0.174354` recovery retention
without reopening the proof failures fixed by M430.
