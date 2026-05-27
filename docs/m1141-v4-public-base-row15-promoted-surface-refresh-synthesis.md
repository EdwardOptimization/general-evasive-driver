# M1141 V4 Public Base Row15 Promoted Surface Refresh Synthesis

## Purpose

M1141 synthesizes the `row15_promoted_base_surface_refresh` branch after the
10-milestone cadence from M1131 through M1140.

This milestone is process-only. It does not run replay, optimize an objective,
train actor weights, run PPO, mine rows, promote a checkpoint, use private
holdout, write an objective NPZ, or change actor inputs.

## Evidence Summary

M1131 designed a fresh source-balanced protected/preference surface refresh for
the current public-gate base:

```text
runs/m1123_row15_unsafe_margin_projection_probe/checkpoints/alpha_0_15.pt
```

M1132 mined and selected a promoted-base surface:

```text
accepted wrong-history rows: 172
physical pairs: 15
left steps: 6
checkpoints: 5
targets: 3
normal-margin buckets: 3
success-drop fraction: 1.0
max physical-pair fraction: 0.116279
control accepted wrong rows: 0
```

M1134 converted that surface into source-preserving family aggregate rows with
no mixed hidden-state objective NPZ.

M1136 replay sanity passed the source-policy gate:

```text
source rows: 172
normal successes: 172
wrong-history successes: 0
success drops: 172
physical pairs: 15
checkpoints: 5
targets: 3
```

M1136 also found cross-family incompatibility:

```text
cross-family replay rows: 860
failed duplicate geometry groups: 34
```

M1137 audited that result and rejected direct mixed-family objective
optimization. It found a broad all-policy intersection, which M1139 then
exported:

```text
kept rows: 148
dropped rows: 24
physical pairs: 13
source labels: 5
targets: 2
left steps: 6
max physical-pair fraction: 0.135135
max source-label fraction: 0.283784
```

M1140 designed a single target-policy materialization for `row15_current`:

```text
target policy checkpoint:
  runs/m1123_row15_unsafe_margin_projection_probe/checkpoints/alpha_0_15.pt
expected rows: 148
minimum physical pairs: 12
minimum source labels: 4
minimum targets: 2
minimum left steps: 6
```

## Supported Claims

The promoted alpha `0.15` public-gate base now has a refreshed public proof
surface that is not just the old active row15 repair set.

The surface supports two levels of use:

```text
source-policy proof surface:
  172 rows, 15 physical pairs, 5 checkpoints, 3 targets

all-policy materialization surface:
  148 rows, 13 physical pairs, 5 source labels, 2 targets
```

The all-policy surface is broad enough to continue into current-base
target-policy materialization. It avoids direct mixed-family objective
optimization by requiring a one-target-policy materialization step.

The supported self-ID claim remains level2 history-encoded reactive proof
surface retention. The evidence is still normal vs wrong-matched-history on
matched-current rows.

## Falsified Or Unsupported Claims

Direct mixed-family objective conversion is unsupported and remains blocked.
M1136 showed `34` failed duplicate geometry groups in cross-family replay.

The branch does not prove objective-corpus quality. No materialized objective
rows have been emitted yet.

The branch does not prove actor improvement, PPO readiness, medium/long PPO
stability, private-holdout generalization, paper-level generalization, or real
vehicle transfer.

The branch does not prove level3 anticipatory self-identification. It has not
added warm-up, active probing, hidden-change temporal windows, or private
history-necessity gates.

## Failure Taxonomy Summary

```text
M1132: none; source-balanced surface refresh passed
M1134: none; family aggregate conversion passed
M1136: none for source-policy gate; cross-family incompatibility reported
M1137: none; audit correctly blocked direct mixed-family objective conversion
M1139: none; all-policy selector passed with 148 rows
M1140: none; materialization design completed
```

The only important negative evidence is not a milestone failure: cross-family
replay incompatibility means objective conversion must proceed through a
single target-policy materialization step.

## Public-Gate Overfit Risk

This surface was mined and selected using public artifacts and the current
public-gate family. It is suitable for public proof-base hardening and
objective development, but not for unbiased paper evidence.

Overfit controls already added:

```text
fresh promoted-base mining rather than old row reuse
source-balanced selection
source-policy replay sanity
cross-family incompatibility audit
all-policy intersection selector
single-target materialization design
cadence synthesis before implementation
```

Remaining risk:

```text
all rows are still public
lateral-accel rows do not survive the all-policy intersection
materialization and objective sanity may still expose target-base sparsity
PPO readiness remains unproven
```

## Next Branch Decision

The branch has done enough preprocessing to close
`row15_promoted_base_surface_refresh` and open target materialization.

```text
synthesis_decision: promote_to_next_branch
closed_branch: row15_promoted_base_surface_refresh
opened_branch: row15_promoted_target_materialization
```

Next milestone:

```text
m1142-v4-public-base-row15-promoted-target-materialization
```

M1142 should run only the already implemented target-policy materializer for
`row15_current`. It should not run replay, optimize an objective, train actor
weights, run PPO, promote, use private holdout, or change actor inputs.

## Decision

```text
row15_promoted_surface_refresh_synthesis_open_target_materialization
```
