# M337 Old-Key Gap-Floor Bottleneck Audit

M337 audits whether the fixed old-key `9944|perturbed|28|28` margin-gap floor
has become the active PPO-continuation bottleneck. No PPO, actor update, or
actor-input change was performed.

## Audit Artifacts

Run dir:

```text
runs/m337_old_key_gap_floor_bottleneck_audit
```

Additional endpoint source-diverse diagnostic:

```text
runs/m337_m335_repaired_endpoint_source_diverse_gate
```

## Old-Key Gap Trend

Old-key `9944` trend:

| Label | Status | Normal margin | Wrong-history margin | Margin gap | Gap floor pass |
| --- | --- | ---: | ---: | ---: | --- |
| m325_repaired | promoted | 0.207388 | 0.110406 | 0.096982 | true |
| m328_repaired | promoted | 0.213944 | 0.121291 | 0.092653 | true |
| m333_a045 | promoted_base | 0.216606 | 0.126452 | 0.090155 | true |
| m335_endpoint | rejected_endpoint | 0.235477 | 0.170117 | 0.065360 | false |
| m335_a0075 | promoted_bounded | 0.216783 | 0.126762 | 0.090021 | true |

The old-key gap is monotonically squeezed across promoted bases and collapses
at the M335 repaired endpoint:

```text
0.096982 -> 0.092653 -> 0.090155 -> 0.065360
```

The bounded M335 promotion only passes because alpha `0.0075` keeps the gap just
above the floor:

```text
0.090021 >= 0.09
```

## Source-Diverse Comparison

Source-diverse protected gates do not show broad washout.

| Family | Status | Passed | Min success drops | Min normal margin delta | Min gap delta |
| --- | --- | ---: | ---: | ---: | ---: |
| m333_a045_selected | selected_bounded | 4 / 4 | 17 | +0.000090638 | +0.000037730 |
| m335_endpoint | rejected_endpoint | 5 / 5 | 17 | +0.000594418 | +0.000361224 |
| m335_a0075_selected | promoted_bounded | 5 / 5 | 17 | +0.000004170 | +0.000002575 |

The critical fact is that the M335 repaired endpoint, which fails the singleton
old-key gap floor, still passes `5/5` source-diverse protected gates. That rules
out broad source-diverse proof washout as the immediate blocker.

## Classification

Failure taxonomy:

```text
protected_key_window_failure
```

More specific classification:

```text
single_old_key_gap_floor_bottleneck_not_source_diverse_washout
```

This is not evidence that the actor lost wrong-history sensitivity globally.
It is evidence that the fixed singleton `9944` scalar floor has become the
active trust-region limiter for PPO continuation.

## Interpretation

The current acceptance stack is conservative enough to protect proof rows, but
the fixed old-key gap floor is now clipping useful PPO directions to micro-alpha
updates. Continuing PPO without changing the gate or objective would likely
repeat the same pattern:

```text
raw PPO / exact repair improves full-corpus objectives
source-diverse proof remains intact
old 9944 gap floor collapses
only tiny interpolation alpha can promote
```

The next step should be no-PPO design work. The project needs either:

```text
source-diverse old-key/gap distribution gate,
or an old-key gap-retention objective,
or a principled replacement for the fixed singleton 0.09 floor.
```

Do not lower the floor ad hoc. If the floor is changed, it should be replaced by
a pre-registered distributional gate with source diversity.

## Decision

Admit:

```text
m338-old-key-gap-distribution-refresh-design
```

Decision:

```text
admit_old_key_gap_distribution_refresh_design
```
