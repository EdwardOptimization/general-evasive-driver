# M1172 V4 Public Base Wrong-History Action-Divergence Artifact Audit

## Purpose

M1172 audits existing M1161 outcome artifacts to determine whether there are
enough action-divergent and terminal-margin-sensitive wrong-history rows to
justify a bounded replay diagnostic without new mining.

This milestone reads existing CSVs only. It does not run mining, run replay,
train actor weights, run PPO, promote, use private holdout, convert rows, or
change actor inputs.

## Input

```text
runs/m1161_row15_promoted_margin_slack_outcome_seed116100/outcome_interventions.csv
```

Rows audited:

```text
wrong_matched_history rows: 4585
```

## Threshold Availability

First-step action divergence:

```text
first_action_distance >= 0.15: 1220 rows, 57 physical pairs, 6 checkpoints, 3 targets
first_action_distance >= 0.20: 630 rows, 30 physical pairs, 6 checkpoints, 3 targets
first_action_distance >= 0.25: 304 rows, 15 physical pairs, 6 checkpoints, 3 targets
first_action_distance >= 0.30: 0 rows
```

Trajectory action divergence:

```text
action_trajectory_distance_mean >= 0.06: 1639 rows, 77 physical pairs, 6 checkpoints, 3 targets
action_trajectory_distance_mean >= 0.10: 1076 rows, 51 physical pairs, 6 checkpoints, 3 targets
action_trajectory_distance_mean >= 0.15: 446 rows, 21 physical pairs, 6 checkpoints, 3 targets
action_trajectory_distance_mean >= 0.20: 194 rows, 9 physical pairs, 6 checkpoints, 2 targets
```

Terminal-margin sensitivity:

```text
margin_gap >= 0.0025: 473 rows, 29 physical pairs, 6 checkpoints, 3 targets
margin_gap >= 0.005: 204 rows, 12 physical pairs, 6 checkpoints, 2 targets
margin_gap >= 0.010: 90 rows, 5 physical pairs, 6 checkpoints, 1 target
margin_gap >= 0.020: 36 rows, 2 physical pairs, 6 checkpoints, 1 target
normal_better == true: 36 rows, 2 physical pairs
```

Combined filters:

```text
first_action_distance >= 0.20 and margin_gap >= 0.0025:
  rows: 106
  physical pairs: 6
  targets: 2
  checkpoints: 6
  max pair fraction: 0.226

first_action_distance >= 0.15
and action_trajectory_distance_mean >= 0.06
and margin_gap >= 0.0025:
  rows: 151
  physical pairs: 8
  targets: 2
  checkpoints: 6
  max pair fraction: 0.159
```

## Interpretation

Existing artifacts do contain useful signal. There are enough rows to build a
small action-divergent diagnostic candidate set, and the best combined filter
has all six checkpoints, two targets, and acceptable pair dominance for a
diagnostic.

But the existing artifacts are not ready to become a proof corpus:

```text
hard normal_better rows: only 36
hard normal_better physical pairs: 2
combo physical pairs: 8, below previous 12-pair surface standards
high margin-gap rows collapse toward one target
```

So the correct next step is not conversion and not PPO. It is a candidate
export design that creates a filtered or score-balanced existing-artifact
candidate CSV, then runs a bounded relocation diagnostic from that candidate
set.

## Decision

Route to candidate export design.

The export design should avoid both extremes:

```text
too broad:
  repeats the old 4585-row source set and dilutes action divergence.

too strict:
  keeps only normal_better or very high margin-gap rows and collapses to two
  physical pairs.
```

Recommended starting candidate rule:

```text
first_action_distance >= 0.15
action_trajectory_distance_mean >= 0.06
margin_gap >= 0.0025
then score-balance by physical pair, checkpoint, target, and left step
```

## Guardrail

No mining, replay, actor training, PPO, promotion, private holdout, conversion,
threshold weakening, or actor-input change occurred.

```text
decision: wrong_history_action_divergence_audit_route_to_candidate_export_design
next: m1173-v4-public-base-action-divergent-candidate-export-design
```
