# M539 Matched-History Seed-Fragility Audit

## Purpose

M539 diagnoses the M538 counterexample where the L2 finite-window checkpoint for
training seed `3531` beats the matched L3 online-GRU checkpoint.

This is a public diagnostic audit. It does not train, tune, or promote a
checkpoint.

## Command

The audit joins the M537 outcome rows back to the M538 paired deltas and filters:

```text
comparison = L3_minus_L2
train_seed = 3531
```

Artifacts:

```text
runs/m539_matched_history_seed_fragility_audit/summary.json
runs/m539_matched_history_seed_fragility_audit/seed3531_l3_minus_l2_rows.csv
runs/m539_matched_history_seed_fragility_audit/surface_summary.csv
runs/m539_matched_history_seed_fragility_audit/target_summary.csv
runs/m539_matched_history_seed_fragility_audit/tail_offset_summary.csv
runs/m539_matched_history_seed_fragility_audit/surface_target_summary.csv
runs/m539_matched_history_seed_fragility_audit/event_summary.csv
runs/m539_matched_history_seed_fragility_audit/terminal_pair_summary.csv
runs/m539_matched_history_seed_fragility_audit/first_action_delta_summary.csv
runs/m539_matched_history_seed_fragility_audit/worst_margin_rows.csv
runs/m539_matched_history_seed_fragility_audit/success_regression_rows.csv
```

## Aggregate

| Metric | Value |
| --- | ---: |
| Rows | `2244` |
| Success delta | `-0.013815` |
| Obstacle completion delta | `-0.011586` |
| Collision delta | `+0.013815` |
| Return delta | `+0.034789` |
| Clearance margin delta mean | `-0.143703` |
| Clearance margin delta median | `-0.025797` |
| Margin-negative share | `0.778520` |
| Success regression count | `31` |
| Collision regression count | `31` |
| M526 event rows | `18` |

Positive deltas favor L3 except collision, where positive means L3 collides more
often. The seed-3531 L2 advantage is mainly a margin and collision/success
issue, not a return issue.

## Surface Breakdown

| Surface | Rows | Success Delta | Collision Delta | Return Delta | Margin Delta | Margin-Negative Share |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| M487 late high energy | `561` | `-0.019608` | `+0.019608` | `-0.120106` | `-0.148291` | `0.782531` |
| M487 near threshold | `549` | `-0.007286` | `+0.007286` | `+0.234900` | `-0.085755` | `0.752277` |
| M497 short reveal | `443` | `-0.013544` | `+0.013544` | `-0.621104` | `-0.088189` | `0.693002` |
| M497 warmup capability | `691` | `-0.014472` | `+0.014472` | `+0.422049` | `-0.221609` | `0.850941` |

The counterexample is not surface-local. Every surface favors L2 on success,
collision, and clearance margin.

## Target And Offset Breakdown

| Target | Rows | Success Delta | Margin Delta | Margin-Negative Share |
| --- | ---: | ---: | ---: | ---: |
| future braking deceleration | `970` | `-0.017526` | `-0.113622` | `0.690722` |
| future lateral accel response | `169` | `0.000000` | `-0.071723` | `0.639053` |
| future yaw response | `1105` | `-0.012670` | `-0.181118` | `0.876923` |

| Tail Offset | Rows | Success Delta | Margin Delta | Margin-Negative Share |
| ---: | ---: | ---: | ---: | ---: |
| `0` | `294` | `-0.013605` | `-0.198571` | `0.778912` |
| `2` | `289` | `-0.017301` | `-0.184459` | `0.799308` |
| `4` | `582` | `-0.017182` | `-0.166488` | `0.807560` |
| `8` | `553` | `-0.010850` | `-0.128792` | `0.792043` |
| `12` | `270` | `-0.011111` | `-0.094429` | `0.748148` |
| `16` | `256` | `-0.011719` | `-0.067060` | `0.691406` |

The margin gap is broad across targets and offsets. It is strongest for
`future_yaw_response` and early offsets, but it does not disappear anywhere.

## Event Contribution

| M526 Event? | Rows | Success Delta | Collision Delta | Return Delta | Margin Delta | Margin-Negative Share |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| no | `2226` | `-0.013926` | `+0.013926` | `-0.008286` | `-0.136563` | `0.778527` |
| yes | `18` | `0.000000` | `0.000000` | `+5.361755` | `-1.026661` | `0.777778` |

The success/collision regression is not caused by M526 event rows. The event
rows have large negative margin deltas, but no success delta.

## Terminal And Action Pattern

Terminal-pair summary:

| Terminal Pair | Rows | Success Delta | Return Delta | Margin Delta | Margin-Negative Share |
| --- | ---: | ---: | ---: | ---: | ---: |
| obstacle completed -> obstacle completed | `1887` | `0.000000` | `+0.951348` | `-0.162208` | `0.770005` |
| collision -> collision | `318` | `0.000000` | `-0.165543` | `+0.000097` | `0.801887` |
| obstacle completed -> collision | `31` | `-1.000000` | `-56.628160` | `-0.305856` | `1.000000` |
| continuation limit -> obstacle completed | `5` | `0.000000` | `+12.697626` | `-0.287853` | `1.000000` |
| continuation limit -> continuation limit | `3` | `0.000000` | `+9.166875` | `-1.831409` | `1.000000` |

The 31 success regressions are exactly:

```text
L2 obstacle_completed -> L3 collision
```

First-action deltas are systematic:

| Subset | Rows | Steer Delta Mean | Throttle Delta Mean | Brake Delta Mean |
| --- | ---: | ---: | ---: | ---: |
| all | `2244` | `-0.136033` | `-0.098220` | `-0.242059` |
| margin negative | `1747` | `-0.134616` | `-0.096137` | `-0.244407` |
| success negative | `31` | `-0.125022` | `-0.091169` | `-0.261813` |
| collision regression | `31` | `-0.125022` | `-0.091169` | `-0.261813` |

The seed-3531 L3 policy is shifted downward on the first steer, throttle, and
brake action channels relative to L2. The audit does not interpret this as
physically better or worse by itself, but the shift aligns with the broad margin
loss and the 31 collision regressions.

## Interpretation

M539 localizes the M538 seed fragility:

```text
The seed-3531 L2-over-L3 counterexample is broad, not an event artifact or a
single-surface artifact.
```

It affects all four public surfaces, all tail-offset groups, and most target
groups. The most actionable observation is the systematic first-action shift in
L3 relative to L2. This points to short-training recipe variance or recurrent
training instability more than to a narrow source-row issue.

The correct next step is a matched training-variance design, not promotion:

- keep L2 as a serious finite-window baseline;
- scale L0/L2/L3 with identical budgets and seeds;
- include per-seed paired public diagnostics;
- only after that decide whether L3's recurrent belief is consistently stronger
  than finite-window history.

## Decision

```text
seed3531_l2_counterexample_broad_admit_m540_training_variance_design
```
