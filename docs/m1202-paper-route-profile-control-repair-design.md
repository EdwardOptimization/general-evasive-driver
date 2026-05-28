# M1202 Paper-Route Profile Control Repair Design

## Summary

M1202 designs the diagnostic-control repairs required before the next
L0/L1/L2/L3 comparison.

Decision:

```text
profile_control_repair_design_admit_runtime_implementation
```

No training or PPO should run until the comparison harness can:

```text
1. enforce reset_hidden_policy during public evaluation;
2. train and evaluate current-tiled L2 controls that keep temporal-GRU capacity but remove older-history information.
```

## Problem From M1201

M1201 found:

```text
l2_observation_stacks_nonidentical: true
l2_older_tiled_action_l2_mean_overall: 0.001374
l2_older_zeroed_action_l2_mean_overall: 0.060810
reset_control_external_eval_semantics_mismatch: true
```

So the current profile comparison cannot yet distinguish:

```text
finite-window history benefit
vs
temporal-GRU encoder/capacity benefit
vs
current-frame substitution
```

It also cannot interpret `L3_reset_control` until evaluation honors the
profile's reset policy.

## Repair 1: Reset-Hidden Evaluation Semantics

Public evaluation must read `controller_profile.reset_hidden_policy` from the
same config/checkpoint lineage used for training.

Required semantics:

| Reset Policy | Actor Type | Eval Behavior |
| --- | --- | --- |
| `episode_persistent` | online recurrent | carry hidden through the episode |
| `every_step_control` | online recurrent | set hidden to `None` before every action |
| `per_decision_window` | temporal finite-window | no online hidden state; no reset action |
| `not_applicable` | feed-forward | no online hidden state |

Implementation options:

```text
Preferred:
  add a small profile-aware evaluation wrapper/policy adapter used by M1199-style runners.

Acceptable:
  extend evaluate.ActorPolicy so it can take reset_hidden_policy directly.

Avoid:
  relying on checkpoint_ablation strings alone, because the profile config already carries the intended reset policy.
```

Focused tests:

```text
L3_online_gru + episode_persistent keeps hidden between two actions.
L3_reset_control + every_step_control resets hidden before each action.
Non-recurrent L0/L1/L2 ignore reset policy.
M1199-style external eval applies both observation masks and reset policy.
```

## Repair 2: Current-Tiled L2 Capacity Control

Add a deployable diagnostic control that preserves:

```text
same observation dimension
same temporal-GRU architecture
same hidden size
same parameter count
same reward/env/randomization
same training budget
```

but removes older-history information by transforming the stacked observation:

```text
frames = obs.reshape(history_length, frame_dim)
frames[1:] = frames[0]
obs = frames.reshape(-1)
```

This should be a profile/runtime observation transform, not a hidden oracle
input and not a reward change.

Suggested profiles:

```text
L2_window_13_current_tiled
L2_window_25_current_tiled
```

The first checks whether the shortest finite-window result is history-driven.
The second checks the strongest representative M1199 L2 profile. Longer tiled
controls can be added later if needed, but starting with 13 and 25 keeps the
repair bounded.

Focused tests:

```text
current-tiled wrapper preserves observation shape.
frame 0 remains unchanged.
all older frames equal frame 0 after transform.
unwrapped L2 observations remain unchanged.
profile metadata records current_tiled_history_control=true.
```

## Corrected Comparison Route

After implementation, do not jump straight to a long run.

Recommended sequence:

```text
M1203: implement reset-policy eval support and current-tiled L2 runtime profiles
M1204: smoke test corrected controls without performance claims
M1205: rerun a small corrected public pilot:
       L1_one_step
       L2_window_13
       L2_window_13_current_tiled
       L2_window_25
       L2_window_25_current_tiled
       L3_online_gru
       L3_reset_control_corrected
```

Only if M1205 shows profile separability should the project return to a longer
L0/L1/L2/L3 comparison.

## Claim Discipline

Allowed after M1202:

```text
diagnostic-control repair design is complete
M1201 metric artifact has a concrete repair route
```

Not allowed:

```text
L2 history necessity
GRU recurrent-belief advantage
self-identification
profile promotion
private-holdout evidence
paper-level architecture ranking
```

## Next Milestone

```text
experiments/manifests/m1203-paper-route-profile-control-repair-implementation.json
```
