# M1171 V4 Public Base Stronger Wrong-History Construction Design

## Purpose

M1171 designs the first step of the new
`stronger_wrong_history_construction` branch opened by M1170.

This milestone is design-only. It does not run mining, run replay, train actor
weights, run PPO, promote, use private holdout, convert failed rows, weaken
thresholds, or change actor inputs.

## Branch Blocker

The previous branch showed that same-shape matched-history relocation is
exhausted:

```text
M1161 source budget: 4585 matched-current pairs across 242 physical pairs
M1161 accepted wrong-history surface: 15 rows across 2 physical pairs
M1169 microgrid accepted surface: 6 rows across the same 2 physical pairs
new physical pairs beyond M1161 after microgrid: 0
```

The failure mode is:

```text
normal branch succeeds;
wrong-history branch also succeeds too often.
```

So the next construction must make wrong histories more behaviorally
meaningful. Merely selecting more source-balanced matched-current pairs is not
enough.

## Evidence From Existing M1161 Outcome Artifacts

A quick existing-artifact summary shows why ordinary wrong-matched history is
weak compared with explicit ablations:

```text
wrong_matched_history:
  first_action_distance_mean: 0.096101
  first_action_distance_p90: 0.227336
  margin_gap_p90: 0.002677

reset_hidden:
  first_action_distance_mean: 0.652387
  first_action_distance_p90: 1.007947
  margin_gap_p90: 0.051562

zero_current_response:
  first_action_distance_mean: 0.130191
  margin_gap_p90: 0.018090
```

This supports the new branch hypothesis: the wrong histories currently being
used are often too close to the normal branch in action space and terminal
margin space.

## New Construction Axes

The next wrong-history construction should rank candidate wrong histories by:

```text
action divergence:
  first-step action distance and short trajectory action distance.

terminal-margin sensitivity:
  normal margin - wrong-history margin after continuation.

source diversity:
  physical pair, left step, target, checkpoint, obstacle geometry bucket.

current-frame match guard:
  keep current observation comparable enough that the intervention still tests
  hidden/history dependence rather than obvious scene mismatch.

contract guard:
  no hidden params, wheel/slip signals, labels, TTC, path refs, or oracle inputs
  may enter the actor.
```

The ranking should explicitly avoid this previous failure:

```text
matched current geometry is good,
but wrong-history action and terminal effects are near-identical to normal.
```

## Proposed Score

For an existing outcome row or future candidate, compute:

```text
score =
  z(first_action_distance)
  + z(action_trajectory_distance_mean)
  + z(max(margin_gap, 0))
  + 0.5 * z(target_z_delta)
  - scene_mismatch_penalty
  - source_dominance_penalty
```

The exact weights are not yet training objectives. They are a diagnostic
ranking for candidate construction.

## Next Audit

Before any new mining or replay, M1172 should audit existing M1161 outcome
artifacts and answer:

```text
Are there enough wrong_matched_history rows with high action divergence and
positive terminal-margin sensitivity to build a stronger candidate set from
existing artifacts?
```

Suggested thresholds to report:

```text
first_action_distance >= 0.15, 0.20, 0.25
action_trajectory_distance_mean >= 0.06, 0.10
margin_gap >= 0.0025, 0.005, 0.01
normal_better == true
source diversity by physical pair, checkpoint, target, and left step
```

If enough candidates exist, route to a bounded existing-artifact replay design.
If not, route to a new mining design that relaxes nearest-current matching and
actively searches for action-divergent wrong histories.

## Guardrail

No mining, replay, actor training, PPO, promotion, private holdout, conversion,
threshold weakening, or actor-input change occurred.

## Decision

```text
decision: stronger_wrong_history_construction_design_admit_action_divergence_audit
next: m1172-v4-public-base-wrong-history-action-divergence-artifact-audit
```
