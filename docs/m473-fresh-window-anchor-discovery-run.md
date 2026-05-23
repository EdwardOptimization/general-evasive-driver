# M473 Fresh-Window Anchor Discovery Run

## Purpose

M473 runs the fresh-window near-boundary anchor discovery pipeline designed in
M472. The goal is not to prove wrong-history outcome degradation yet. The goal
is to determine whether the M457 late-reveal task family can produce
source-diverse near-boundary wrong-history anchors outside the M467/M471 seed
window.

No training, PPO, actor-input change, outcome proof expansion, or checkpoint
promotion is performed.

## Pipeline

M473 runs the same no-training pipeline on two fresh seed windows:

```text
window A: 10500,10600,10700
window B: 10800,10900,11000
```

Each window runs:

1. Expanded matched-current mining.
2. Wrong-history targeted pair triage.
3. Matched-history action intervention gate.
4. Matched-history continuation outcome gate.
5. Outcome-critical selector.
6. Near-boundary wrong-history selector.

## Window A Results

Artifacts:

```text
runs/m473a_fresh_window_matched_current_seed10500/summary.json
runs/m473a_fresh_window_targeted_pair_triage/summary.json
runs/m473a_fresh_window_action_gate/summary.json
runs/m473a_fresh_window_outcome_gate/summary.json
runs/m473a_fresh_window_outcome_selector/summary.json
runs/m473a_fresh_window_near_boundary_selector/summary.json
```

Matched-current mining:

```text
candidate pairs:              380421
accepted pairs:                 1818
accepted physical pairs:        1645
accepted left steps:              35
accepted obstacle buckets:        42
```

Targeted pair triage:

```text
targeted pairs:                  240
probe seeds:                       3
obstacle labels:                   3
targets:                           3
single seed share:          0.333333
single label share:              0.5
triage_pass:                    True
```

Action/outcome gates:

```text
action intervention rows:        1200
outcome intervention rows:       1440
```

Outcome selector:

```text
candidate rows:                  1200
action-prefilter pass:            430
outcome-critical rows:             81
accepted rows:                     34
compact rows:                      34
selector_pass:                   True
```

Near-boundary selector:

```text
wrong-history rows:               240
near-boundary candidates:          53
proof candidates:                   0
near-boundary no-effect rows:      53
high-slack diagnostics:             3
near-boundary labels: drift_required 27, unavoidable 26
near-boundary seeds: 10500 20, 10600 2, 10700 31
wrong_history_gate_pass:        False
```

## Window B Results

Artifacts:

```text
runs/m473b_fresh_window_matched_current_seed10800/summary.json
runs/m473b_fresh_window_targeted_pair_triage/summary.json
runs/m473b_fresh_window_action_gate/summary.json
runs/m473b_fresh_window_outcome_gate/summary.json
runs/m473b_fresh_window_outcome_selector/summary.json
runs/m473b_fresh_window_near_boundary_selector/summary.json
```

Matched-current mining:

```text
candidate pairs:              381105
accepted pairs:                 1661
accepted physical pairs:        1543
accepted left steps:              30
accepted obstacle buckets:        36
```

Targeted pair triage:

```text
targeted pairs:                  240
probe seeds:                       3
obstacle labels:                   3
targets:                           3
single seed share:          0.333333
single label share:              0.5
triage_pass:                    True
```

Action/outcome gates:

```text
action intervention rows:        1200
outcome intervention rows:       1440
```

Outcome selector:

```text
candidate rows:                  1200
action-prefilter pass:            338
outcome-critical rows:            115
accepted rows:                     38
compact rows:                      38
selector_pass:                   True
```

Near-boundary selector:

```text
wrong-history rows:               240
near-boundary candidates:          51
proof candidates:                   0
near-boundary no-effect rows:      51
high-slack diagnostics:            14
near-boundary labels: drift_required 18, unavoidable 33
near-boundary seeds: 10800 11, 10900 4, 11000 36
wrong_history_gate_pass:        False
```

## Combined Anchor Surface

Combined artifact:

```text
runs/m473_combined_fresh_window_anchor_summary/summary.json
runs/m473_combined_fresh_window_anchor_summary/near_boundary_candidates_combined.csv
```

Combined fresh anchors:

```text
near-boundary candidates:         104
proof candidates:                   0
near-boundary no-effect rows:     104
high-slack diagnostics:            17
probe seeds:                        6
obstacle labels:                    2
targets:                            3
single seed share:           0.346154
single label share:          0.567308
anchor_discovery_pass:          True
```

By seed:

```text
10500: 20
10600:  2
10700: 31
10800: 11
10900:  4
11000: 36
```

By obstacle label:

```text
drift_required: 45
unavoidable:    59
```

By target:

```text
future_braking_deceleration:   39
future_lateral_accel_response: 22
future_yaw_response:           43
```

## Interpretation

M473 passes the anchor-discovery gate. The key improvement over M471 is source
diversity:

```text
M471 adversarial surface:
  rows:              67
  probe seeds:        3
  single seed share:  0.671642

M473 fresh anchor surface:
  rows:             104
  probe seeds:        6
  single seed share:  0.346154
```

However, M473 still finds `0` proof candidates. Every fresh near-boundary
wrong-history row is currently a no-effect anchor, not an outcome degradation
proof row.

Therefore the result is positive for source-diverse anchor discovery, but it is
not yet evidence that wrong history changes closed-loop outcome.

## Decision

```text
fresh_window_anchor_discovery_pass_admit_m474
```

M474 should combine M467 and M473 anchors, combine the same-window and fresh
candidate pools, and rerun adversarial wrong-history search before any outcome
probe.

No checkpoint is promoted.
