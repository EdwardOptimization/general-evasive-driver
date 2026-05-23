# M331 M330 Old-Key Gap-Floor Failure Audit

M331 audits why M330 was rejected before first replay. No PPO, first replay,
promotion, or actor-input change was performed.

## Question

M330 passed exact M297/M270 and source-diverse protected gates, but failed the
old `9944|perturbed|28|28` margin-gap floor:

```text
required old-key margin_gap >= 0.09
M330 old-key margin_gap = 0.08690063195545505
```

M331 asks whether this is:

```text
true proof erosion on the old key,
a stale / over-strict scalar floor,
or a candidate-specific old-key trajectory artifact.
```

## Audit Artifact

Run dir:

```text
runs/m331_m330_old_key_gap_floor_audit
```

Artifacts:

```text
runs/m331_m330_old_key_gap_floor_audit/summary.json
runs/m331_m330_old_key_gap_floor_audit/old_key_trend.csv
runs/m331_m330_old_key_gap_floor_audit/source_diverse_comparison.csv
```

## Old-Key Trend

| Candidate | Normal margin | Wrong-history margin | Margin gap | Gap vs 0.09 floor |
| --- | ---: | ---: | ---: | ---: |
| M325 repaired | 0.207388 | 0.110406 | 0.096982 | +0.006982 |
| M328 repaired | 0.213944 | 0.121291 | 0.092653 | +0.002653 |
| M330 repaired | 0.219756 | 0.132855 | 0.086901 | -0.003099 |

The M330 movement from M328 changes the old key by:

| Quantity | Delta |
| --- | ---: |
| Normal margin | +0.005812 |
| Wrong-history margin | +0.011565 |
| Margin gap | -0.005752 |

The old-key wrong-history branch becomes safer faster than the normal-history
branch. This is why the margin gap crosses the floor.

## Source-Diverse Comparison

M330 still passes all source-diverse protected gates.

| Milestone | Gates passed | Comment |
| --- | ---: | --- |
| M325 | 2 / 2 | repaired endpoint source-diverse pass |
| M328 | 3 / 3 | promoted M327 source-diverse pass |
| M330 | 4 / 4 | fresh-seed repeat source-diverse pass |

For M330, every source-diverse gate retains all `17 / 17` wrong-history success
drops, and margin-gap deltas are positive:

| Gate | Normal margin delta | Margin gap delta | Pass |
| --- | ---: | ---: | --- |
| current_m328_surface | +0.000202621 | +0.000084419 | true |
| m325_continuity_surface | +0.000396455 | +0.000169297 | true |
| m317_continuity_surface | +0.000591253 | +0.000249539 | true |
| m314_continuity_surface | +0.000591776 | +0.000249740 | true |

This is not broad source-diverse proof washout.

## Classification

M331 classifies the M330 failure as:

```text
old_key_local_gap_erosion_not_source_diverse_washout
```

Using process-v2 taxonomy, the original M330 rejection remains:

```text
protected_key_window_failure
```

The old-key floor should not be lowered inside M331. It caught a monotonic
three-step erosion on the historical key:

```text
0.096982 -> 0.092653 -> 0.086901
```

At the same time, the evidence does not justify discarding the M330 direction:
exact objectives improve and source-diverse gates pass. This makes a
gap-bounded interpolation probe the next safe step.

## Decision

Do not promote M330. Do not run more PPO yet. Do not lower the `0.09` floor in
place.

Admit a no-PPO interpolation probe:

```text
m332-m330-old-key-gap-bounded-interpolation-probe
```

The probe should interpolate from M328 base to M330 repaired, then select the
largest candidate that satisfies:

```text
exact M297/M270 no-regression
source-diverse protected gates pass
old-key margin_gap >= 0.09
M183/M170 and M267/M264 first replay gates pass
```

Decision:

```text
admit_m332_m330_old_key_gap_bounded_interpolation_probe
```
