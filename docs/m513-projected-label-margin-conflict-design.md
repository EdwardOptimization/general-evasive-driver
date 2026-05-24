# M513 Projected Label-Margin Conflict Design

## Purpose

M513 designs the next audit after M512 shows that label-targeted projection
finds multiple projected labels, but all low-margin terminal-boundary rows are
still `unavoidable`.

No outcome gate, training, PPO, actor-input change, checkpoint update, or
checkpoint promotion is performed.

## M512 Failure Mode

M512 does not fail because projected labels are impossible:

```text
unavoidable:    33088
drift_required:  2102
aeb_feasible:     777
```

It fails because projected label diversity and terminal-boundary low margin do
not overlap:

```text
normal_margin <= 4.0:
  only unavoidable rows

drift_required min normal margin: 7.450602
aeb_feasible   min normal margin: 7.458511
```

This suggests a structural conflict between the current scenario labels and the
terminal-boundary proof surface. In the current M502 geometry, once the
projected obstacle is close enough to be terminal-boundary sensitive, the
classifier calls it `unavoidable`.

## Design Choice

M514 should be an audit, not another selector tweak.

It should answer:

```text
Is there any reasonable projected geometry family where:
  projected label != unavoidable
  and normal_min_clearance_margin <= 2.0
  and one-shot wrong-history action signal is nonzero?
```

The audit should run broader projection grids, but it must not admit an outcome
gate. It should report feasibility of the intersection:

```text
projected label family
normal margin bucket
projection magnitude bucket
half-width delta bucket
action trajectory distance bucket
source seed/config/target coverage
```

## Candidate Grid

M514 should expand only as an audit:

```text
body_x_absolute:
  3, 4, 5, 6, 8, 10, 12, 14, 16, 18

body_y_from_source:
  source_y - 2.0
  source_y - 1.5
  source_y - 1.0
  source_y - 0.5
  source_y + 0.0
  source_y + 0.5
  source_y + 1.0
  source_y + 1.5
  source_y + 2.0

half_width_scale:
  0.5, 0.75, 1.0, 1.25, 1.5
```

Projection magnitudes above the M512 primary cap can be analyzed, but they must
be reported as diagnostic and cannot be used as proof admission.

## Decision Rules

If M514 finds source-diverse low-margin non-`unavoidable` rows within reasonable
projection caps, then M515 should build a selector around that family.

If M514 confirms that low-margin rows are structurally `unavoidable` under the
current classifier, then the workflow should stop using scenario-label
diversity as a terminal-boundary proof admission criterion. The replacement
must be pre-registered before use, for example:

```text
proof gate:
  source seed diversity
  config diversity
  target diversity
  projected geometry bucket diversity
  margin bucket diversity
  action/margin sensitivity

scenario-distribution gate:
  separate broad label diversity evaluation
```

This would not be a post-hoc relaxation of M512. It would be a documented split
between mechanism proof rows and broad scenario-distribution evidence.

## Decision

```text
admit_m514_projected_label_margin_conflict_audit
```

Next blocker:

```text
m514-projected-label-margin-conflict-audit
```
