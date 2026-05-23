# M432 Selective 10004 Guard Design

M432 designs the next no-PPO guard profile after M431. It does not train,
promote a checkpoint, lower thresholds, or change actor inputs.

## Problem

M431 showed that M430 restored proof by over-anchoring the M429 branch-split
guard:

- M427 recovery retained vs M406: `0.174354`;
- M430 recovery retained vs M406: `0.061702`;
- dominant M427 branch-split violation: `10004` wrong-history;
- `10004` wrong-history gradient relation to recovery: cosine `-0.904241`.

The current M429 guard treats `10004` wrong-history as a tiny-radius
full-trajectory hard anchor:

```text
source_index: 7
case: 10004|perturbed|31|31|9.5|-1.0|0.8
branch: wrong_history
rows: 37
radius: 0.0002
```

This is too stiff. It prevents the wrong-history branch from becoming safe, but
it also removes the recovery direction that made M427 useful.

## Design

Keep these guards unchanged for the first selective probe:

- all existing M426 base hard guards;
- `10023` wrong-history;
- both `9872` normal-branch guards.

Only modify `10004` wrong-history.

Export a small profile family from the M429 anchor:

| Profile | `10004` rows | `10004` radius | Purpose |
| --- | ---: | ---: | --- |
| `r0005` | all `37` | `0.0005` | minimal relaxation |
| `r0010` | all `37` | `0.0010` | medium relaxation |
| `r0015` | all `37` | `0.0015` | approach useful recovery range |
| `r0020` | all `37` | `0.0020` | loose but still below M427 max distance `0.003843` |
| `tail_r0005` | final third only | `0.0005` | test whether terminal wrong-branch protection is enough |
| `tail_r0010` | final third only | `0.0010` | terminal-only medium relaxation |

Do not remove `10004` protection entirely. Every profile must still contain at
least one `10004` wrong-history guard segment so the old-key compact replay can
decide whether the relaxation is too loose.

## Probe Rule

M433 should only export anchors and no-update smokes. M434 should run the
actual no-PPO projection probe.

For M434, use the same projection recipe as M430 except replacing the anchor:

```text
base checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
raw checkpoint:  runs/m403_lrec1e10_interpolation/checkpoints/alpha_0_1.pt
project recovery gradient: enabled
PPO: disabled
promotion: disabled
```

Gate order:

1. exact M297/M270/old-key no-regression;
2. M267/M264 first replay `17 / 17`;
3. old-key compact replay `40 / 40`;
4. M183/M170 first replay `17 / 17`;
5. recovery retained vs M406.

Primary utility target:

```text
recovery retained vs M406 >= 0.20
```

Minimum useful comparison:

```text
recovery retained vs M406 > M427 0.174354
```

If no profile beats M427 while preserving proof, the next design should move
from action-distance anchors to a terminal-margin or rejected-branch preference
residual for `10004`, not to PPO.

## Decision

Admit implementation-only milestone:

```text
m433-selective-10004-anchor-export
```

M433 should implement/export the six profile anchors, write source metadata,
and run no-update exact repair smokes to verify each anchor loads without
regressing exact objectives at the base checkpoint.
