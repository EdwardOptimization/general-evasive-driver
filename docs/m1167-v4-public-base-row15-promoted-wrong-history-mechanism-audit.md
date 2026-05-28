# M1167 V4 Public Base Row15 Promoted Wrong-History Mechanism Audit

## Purpose

M1167 audits why M1166 selected a broad source set but produced only one
accepted wrong-history relocation row.

This milestone reads existing M1161 and M1166 artifacts only. It does not
rerun mining, rerun the outcome gate, run relocation replay, train actor
weights, run PPO, promote, use private holdout, convert a surface, weaken
thresholds, or change actor inputs.

## Accepted Surface Contrast

M1161 accepted wrong-history rows:

```text
rows: 15
physical pairs: 2
targets: future_yaw_response only
checkpoint/target:
  row15_current/future_yaw_response: 10
  row15_previous_alpha015/future_yaw_response: 5
normal margin range: 0.001947 to 0.002483
physical pairs:
  116117:39:116124:15 -> 10 rows
  116117:36:116124:15 -> 5 rows
```

M1166 accepted wrong-history rows:

```text
rows: 1
physical pairs: 1
targets: future_yaw_response only
checkpoint/target:
  row15_current/future_yaw_response: 1
normal margin: 0.002457
physical pair:
  116117:39:116124:15 -> 1 row
```

M1166 did not miss the old sensitive physical pairs during candidate
selection. Both M1161 accepted physical pairs were selected:

```text
116117:39:116124:15 selected: true
116117:36:116124:15 selected: true
```

## M1166 Outcome Categories

Across `4605` wrong-matched-history relocation rows:

```text
normal_success=true,  wrong_history_success=true,  success_drop=false: 3321
normal_success=false, wrong_history_success=false, success_drop=false: 1283
normal_success=true,  wrong_history_success=false, success_drop=true: 1
```

The near-boundary filter also was not empty:

```text
normal_near_boundary=true, accepted=false: 709
normal_near_boundary=true, accepted=true: 1
```

So M1166 is not blocked by source budget or by lack of near-boundary normal
rows. It is blocked because almost all wrong-history variants remain safe when
the normal branch is safe.

## Target-Grid Effect

The difference between the two old sensitive physical pairs exposes a target
margin grid artifact.

Pair `116117:39:116124:15` still has one accepted M1166 row:

```text
relocated obstacle: x=3.810742, y=-2.480522, half_width=1.740214
normal margin: 0.002457
wrong-history margin: -0.000075
success drop: true
```

Pair `116117:36:116124:15` was selected, but the closest comparable M1166
row stayed safe:

```text
relocated obstacle: x=4.532212, y=-2.401324, half_width=1.740214
normal margin: 0.002983
wrong-history margin: 0.000469
success drop: false
```

In M1161 the same pair had accepted rows at a slightly narrower boundary:

```text
relocated obstacle: x=4.532212, y=-2.401324, half_width=1.740714
normal margin: 0.002483
wrong-history margin: -0.000029
success drop: true
```

M1166 removed the `0.0005` target-normal-margin value from the target grid.
That makes M1166 partly a false negative for reproducing M1161's second
accepted pair.

## Broader Mechanism Finding

The target-grid artifact does not explain the whole failure. M1166 sampled
`240` physical pairs and produced only one success drop. The accepted surface
still collapses to the same narrow row15-current yaw-response active set:

```text
success-drop checkpoint/target:
  row15_current/future_yaw_response: 1
all other checkpoint/target groups: 0
```

This means a larger same-shape relocation expansion is not justified yet.
The next diagnostic should first test whether restoring a fine near-boundary
target grid recovers the M1161 accepted rows and whether it reveals any new
physical pairs. If it only recovers the old two pairs, the branch should pivot
away from same-shape relocation expansion.

## Classification

```text
source-budget failure: false
candidate-selection miss: false
target-margin grid artifact: true
wrong-history intervention scarcity beyond grid: true
same-shape large expansion justified now: false
```

Failure types:

```text
scenario_sampling_failure
metric_artifact
```

## Guardrail

No mining, outcome rerun, relocation replay, actor training, PPO, promotion,
private holdout, surface conversion, threshold weakening, or actor-input
change occurred.

## Decision

Route to a tiny target-margin microgrid design before any further expansion.

```text
decision: row15_promoted_wrong_history_mechanism_audit_route_to_target_margin_microgrid_design
next: m1168-v4-public-base-row15-promoted-relocation-target-microgrid-design
```
