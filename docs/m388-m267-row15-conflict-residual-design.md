# M388 M267 Row15 Conflict Residual Design

M388 designs the next repair objective after M387. It does not train, run PPO,
promote a checkpoint, lower thresholds, or change the actor input/output
contract.

## Problem

M386 is a valid public-gate base, but M387 shows it is only a micro promotion.
The accepted alpha is `0.00075`; alpha `0.001` already flips M267/M264 row
`15`:

| Alpha | Wrong-history margin | Wrong-history success |
| ---: | ---: | --- |
| 0.00000 | -0.000015570 | false |
| 0.00075 | -0.000001064 | false |
| 0.00100 | +0.000003801 | true |

The M384 local-action recovery residual is trying to improve old-key normal
branch margin. That direction is useful for the cumulative old-key gate, but
it also nudges current-family wrong-history trajectories into success. The
active blocker is therefore a cross-surface conflict:

```text
old-key normal-margin recovery
vs
current-family wrong-history failure retention
```

Continuing PPO, increasing old-key recovery weight, or adding another old-key
branch-weight overlay would optimize the wrong control variable.

## Design Choice

Implement a training-only current-family conflict corpus and residual that
protects wrong-history boundary rows discovered by replay.

The first corpus should focus on M267/M264 rows that become safe under the M385
recovery direction:

```text
row 15: fails first at alpha 0.001
row 6: fails by alpha 0.005 / 0.010
```

The corpus should be exportable from replay artifacts, not from hidden or
oracle actor inputs.

## Corpus Schema

Add a compact NPZ format, tentatively:

```text
observation
preferred_hidden
rejected_hidden
preferred_anchor_action
rejected_boundary_action
weight
row_id
source_surface
boundary_margin
```

Semantics:

- `preferred_hidden` is the correct-history recurrent hidden state.
- `rejected_hidden` is the wrong-history recurrent hidden state.
- `preferred_anchor_action` anchors the normal branch to the current public
  base action, preventing normal-branch regression.
- `rejected_boundary_action` anchors the wrong-history branch to the current
  public base action or a replay-confirmed collision-preserving local action.
- `boundary_margin` records the wrong-history terminal margin under the base
  for weighting and diagnostics only; it is not an actor input.

The initial implementation can use current-base wrong-history actions as the
rejected boundary action. If that is insufficient, a later export can search
local wrong-history actions that keep the row safely on the collision side,
mirroring the M384 local-action recovery search but applied to the rejected
branch.

## Residual

Add an optional exact-repair term:

```text
L_conflict =
  lambda_preferred_anchor * || pi(o, h_pref) - a_pref_base ||^2
+ lambda_rejected_boundary * || pi(o, h_wrong) - a_wrong_boundary ||^2
```

The rejected branch should receive stronger weight on rows with small negative
wrong-history margin, because those rows are closest to becoming falsely safe.
A simple first weighting rule is:

```text
weight = base_weight * clip(margin_floor / max(abs(boundary_margin), eps), 1, max_weight)
```

For row15, this should produce a high weight because the base wrong-history
margin is only about `-1.6e-5`.

This residual is a guardrail, not a replacement for replay. Exact loss is still
only a proposal filter; M267/M264 first replay remains authoritative.

## Composition With Old-Key Recovery

The next repair probe should use both terms:

```text
old-key recovery residual:
  protects cumulative old-key normal branch margins

current-family conflict residual:
  prevents wrong-history boundary rows from becoming safe
```

The intended gate order is:

1. exact M297/M270 no-regression;
2. conflict residual finite and decreasing or bounded;
3. M267/M264 first replay, with row15 retained;
4. cumulative old-key replay;
5. source-diverse protected gate;
6. M183/M170 first replay;
7. full public gate only after proof gates pass.

The order intentionally checks M267/M264 before old-key when testing this
specific conflict, because row15 is the active constraint.

## Implementation Plan

M389 should implement the corpus exporter and loader:

- export row15 and row6 snapshots from existing M267/M264 replay artifacts;
- write a compact NPZ and CSV diagnostics;
- add loader validation for finite shapes, weights, and action bounds;
- add a no-update exact-repair smoke proving the optional residual is wired;
- do not run PPO.

M390 should run a no-PPO repair probe from the M386 base:

- start from the M385 rejected recovery endpoint or the alpha `0.001` boundary;
- use old-key recovery plus conflict residual;
- select a bounded alpha only if exact objectives, M267/M264, and cumulative
  old-key replay all pass.

## Acceptance Rules

The design is acceptable only if:

- no actor input or output changes;
- no threshold relaxation;
- M267/M264 row15 remains an explicit required proof row;
- cumulative old-key replay remains an outer gate;
- PPO remains blocked until a no-PPO repair direction passes both surfaces.

## Decision

Admit:

```text
m389-m267-row15-conflict-corpus-implementation
```

Decision:

```text
admit_m389_m267_row15_conflict_corpus_implementation
```
