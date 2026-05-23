# M498 Natural Belief Wrong-History No-Effect Audit

## Purpose

M498 audits why M497's natural decision-window wrong-history intervention
remains outcome-no-effect despite strong reset/zero-current control sensitivity.

No training, PPO, actor-input change, checkpoint update, or checkpoint
promotion is performed.

## Artifacts

Input artifacts:

```text
runs/m497_natural_belief_decision_window_outcome_summary/combined_tail_outcomes.csv
runs/m497_natural_belief_decision_window_outcome_summary/combined_summary.json
```

Output artifacts:

```text
runs/m498_natural_belief_wrong_history_no_effect_audit/summary.json
runs/m498_natural_belief_wrong_history_no_effect_audit/variant_distance_summary.csv
```

## Outcome Counts

```text
wrong_tail_once rows:          1124
wrong_tail_once proof rows:      15
wrong_tail_once event rows:       0

reset/zero-current rows:       2248
reset/zero-current proof rows:  472
reset/zero-current event rows:   17
```

Wrong-history proof rows are source-diverse enough to diagnose, but not enough
to prove outcome sensitivity:

```text
configs: 2
labels: 2
targets: 2
probe seeds: 3
single-seed share: 0.666667
```

## Action And Trajectory Distances

All rows:

```text
wrong_tail_once:
  first_action_distance_mean:      0.069847
  first_action_distance_p90:       0.124555
  trajectory_distance_mean:        0.055405
  trajectory_distance_p90:         0.107307

reset_tail:
  first_action_distance_mean:      0.909815
  first_action_distance_p90:       1.049982
  trajectory_distance_mean:        1.005724
  trajectory_distance_p90:         1.150739

zero_current_tail:
  first_action_distance_mean:      0.083332
  first_action_distance_p90:       0.155971
  trajectory_distance_mean:        0.451155
  trajectory_distance_p90:         0.618961
```

Ratios:

```text
wrong / reset first-action ratio:       0.076770
wrong / zero-current first-action ratio: 0.838177
wrong / reset trajectory ratio:         0.055089
wrong / zero-current trajectory ratio:  0.122806
```

The key result is the trajectory ratio. Wrong-history can move the first action
about as much as zero-current in some cases, but the closed-loop trajectory
rapidly returns toward normal. Zero-current and reset-hidden continue to
perturb the policy because those ablations persist every step; one-shot
wrong-history is corrected quickly by current response observations.

## Proof-Row Details

Wrong-history proof rows:

```text
rows: 15
by config: warmup_capability 11, short_reveal 4
by label: drift_required 8, unavoidable 7
by target: future_yaw_response 12, future_lateral_accel_response 3
```

Wrong-history proof rows have larger first-action distances:

```text
first_action_distance_mean: 0.179537
first_action_distance_p90:  0.313932
trajectory_distance_mean:   0.069410
trajectory_distance_p90:    0.103684
margin_gap_mean:            0.026729
```

Even there, trajectory distance stays small. This explains why the rows remain
margin-only and do not become collision/success/completion event rows.

Control proof rows:

```text
reset_tail proof rows:        298
zero_current_tail proof rows: 174
```

Control event rows:

```text
reset_tail events:         4
zero_current_tail events: 13
```

## Classification

```text
weak_wrong_history_trajectory_signal
```

Supporting flags:

```text
weak_wrong_history_action_signal: true
wrong_history_source_concentrated: true
wrong_history_margin_only: true
```

## Interpretation

M498 says M497 is not failing because the natural decision-window task is
insensitive. It is failing because the current wrong-history intervention and
pair selector do not create persistent outcome-relevant wrong-history action
trajectories.

The M496 selector used target-z capability divergence, visible similarity, and
near-boundary proxies. Those are useful for candidate mining, but they are not
enough to select rows where wrong-history actually changes the closed-loop
trajectory.

The next selector should be action-sensitive:

```text
1. start from the full M495 matched-current surface;
2. run a cheap action/short-horizon wrong-history probe;
3. rank by wrong-history first-action and short-horizon trajectory distance;
4. keep normal rollout near-boundary;
5. enforce source diversity across seeds, labels, targets, configs, and offsets;
6. only then run an outcome gate.
```

## Decision

```text
audit_wrong_history_weak_or_margin_only_admit_m499_action_sensitive_selector_design
```

M499 should design an action-sensitive natural wrong-history selector over the
full M495 surface. It should not repeat the M496 target-z selector unchanged.

No checkpoint is promoted.
