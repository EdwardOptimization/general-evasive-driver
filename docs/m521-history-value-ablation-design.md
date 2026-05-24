# M521 History-Value Ablation Design

## Purpose

M521 designs the next evidence line after M520 shows only margin-only,
source-narrow one-shot wrong-history signal on the valid-offset projection
surface.

No ablation is run in M521. No training, PPO, actor-input change, checkpoint
update, or checkpoint promotion is performed.

## Motivation

M487, M497, M518, and M520 point to the same pattern:

```text
wrong-history interventions can move actions;
reset/zero controls can create stronger diagnostic sensitivity;
one-shot wrong-history is often corrected quickly by current feedback;
source-diverse outcome-level wrong-history proof remains weak.
```

This should not be treated as proof that history is useless. It means the
one-shot wrong-history gate is a weak test for a driver-like recurrent policy:
a good closed-loop driver may use current feedback to repair a wrong belief
quickly.

The next evidence should measure history value by comparing history levels
directly instead of trying to force a single wrong-history event row.

## Proposed Levels

Use the current P0 human-view actor contract and compare:

```text
L0: current observation only
    Diagnostic approximation: reset recurrent state at every step and remove
    explicit action-history fields when the harness supports it.

L1: one-step command-response feedback
    Current observation plus previous command/actuator/IMU-like response, but
    no multi-step recurrent memory.

L2: finite command-response window
    A short fixed history window, for example the last 4-8 frames, without an
    unbounded online recurrent state.

L3: online GRU recurrent belief
    The current mainline policy with persistent recurrent state.
```

The first M522 implementation should be diagnostic and non-training: evaluate
the existing M399 L3 checkpoint under deployable ablations before training new
L0/L1/L2 actors. If the diagnostic shows meaningful history value, later
milestones can train matched-capacity L0/L1/L2 baselines.

## Surfaces

M522 should start with public mechanism surfaces already produced by the recent
branch:

```text
M516/M520 projected terminal-boundary surface
M503/M504 natural boundary-pressure matched-current rows
M495/M497 natural belief decision-window rows
M486/M487 critical-window rows
```

The first implementation may use a compact subset, but it must report which
surface each result comes from and avoid mixing projected mechanism proof with
raw natural-scenario claims.

## Metrics

For each level and surface, report:

```text
success_rate
collision_rate
obstacle_completion_rate
min_clearance_margin_mean / p10
termination_reason histogram
first_action_distance_to_L3
action_trajectory_distance_to_L3
reset/zero/wrong-history sensitivity where available
```

For history-value evidence, the primary comparisons are:

```text
L3 vs L0
L3 vs L1
L3 vs L2
```

The expected positive pattern is not necessarily a huge aggregate success gap.
Near-boundary evidence is enough if it is source-diverse and not a replay
artifact:

```text
L3 preserves margins or outcomes where L0/L1 degrade;
L2 recovers part of L3 but not all;
the gap is larger on surfaces designed to require capability belief;
the gap is not caused by privileged or oracle inputs.
```

## Guardrails

Do not:

```text
train a new checkpoint before the diagnostic harness is implemented;
promote a checkpoint from this ablation;
add hidden dynamics or oracle labels to actor inputs;
claim projected mechanism rows prove broad scenario generalization;
tune from private holdouts;
conflate reset/zero-current controls with wrong-history proof.
```

## M522 Implementation Target

M522 should implement a history-value ablation runner that can:

```text
load a checkpoint and selected replay surfaces;
run L3 normal recurrent rollout;
run at least L0 reset-hidden-each-step diagnostic;
optionally run L1/L2 approximations if available without architectural change;
write per-row outcomes and summary tables;
document limitations of diagnostic approximations.
```

If M522 can only support L0 and L3 initially, that is acceptable as an
infrastructure milestone, but it must not overclaim the L1/L2 comparison.

## Decision

```text
admit_m522_history_value_ablation_runner
```

Next blocker:

```text
m522-history-value-ablation-runner
```
