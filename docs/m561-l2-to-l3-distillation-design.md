# M561 L2-To-L3 Distillation Design

## Purpose

M561 designs a pivot after repeated L3 route-screen failures.

M542-M560 show:

```text
L2 finite-window policy is consistently strong.
From-scratch L3 online-GRU PPO remains contact-prone.
PPO-stability changes and collision/margin reward shaping do not clear route-screen v2.
```

The next hypothesis is that L3 needs supervised grounding from the strong L2
behavior before PPO continuation.

This milestone is design-only. It does not train or promote a checkpoint.

## Core Boundary

L2 may be a training-time teacher. L3 remains the deployable driver.

Allowed:

```text
teacher: L2 finite-window P0 observations for target generation
student: L3 online-GRU P0 current-frame observations + recurrent hidden
target: deterministic L2 action mean
```

Forbidden:

```text
do not feed the 4-frame L2 stack into the deployed L3 actor
do not add mu / hidden dynamics / oracle labels
do not use public frozen-source rows for corpus, selection, or training
do not skip route-screen v2 before public diagnostics
```

Teacher information is training-only. The checkpoint metadata must still declare:

```text
P0_human_view_no_wheel_no_oracle
L3_online_gru
env history_length = 1
```

## Why Distillation

M560 reward shaping produced:

```text
51/51 candidates pass L0 binary success
0/51 pass L0 margin
0/51 pass L0 collision tolerance
```

The failure is not lack of any obstacle completion. It is unsafe contact-prone
behavior. L2 already has a much safer behavior prior on the same task family:

```text
M560 L2 success = 0.671875
M560 L2 collision = 0.328125
M560 L2 margin = 1.031682
```

So the next controlled question is:

```text
Can online-GRU L3 imitate the strong finite-window L2 driver from current-frame
sequences, then retain or improve that behavior under route-screen v2?
```

## Data Plan

M562 should implement an L2-teacher corpus exporter.

For each training seed:

1. Roll out the L2 teacher under the L2 level-matched env config.
2. Record the per-step canonical 72-value current frame.
3. Record previous physical commands as observed by the P0 frame.
4. Query the L2 teacher deterministic action mean from the 4-frame stack.
5. Store terminal outcome, collision flag, obstacle completion, clearance
   margin, obstacle label, and hidden-condition buckets for weighting and audit.

The student sequence should be:

```text
obs_seq[t] = current 72-value P0 frame
target_action[t] = L2 deterministic action mean at the same time step
done_seq[t] = episode done mask for recurrent hidden reset
```

The L2 4-frame stack can be stored for audit, but it must not be part of the L3
student input tensor.

## Exposure Bias Boundary

A pure teacher-forced corpus can make L3 imitate L2 under L2's action history,
but deployment hidden state depends on L3's own actions. Therefore the sequence
should be staged:

### Stage A: Teacher-Forced BC

Train L3 offline on L2 rollouts:

```text
minimize MSE(action_mean_L3(obs_seq, hidden_seq), action_mean_L2)
```

This proves the L3 architecture can represent L2-like behavior from recurrent
current-frame input.

### Stage B: Student-Rollout DAgger-Style Corpus

Roll out the current L3 student on non-public training seeds. At each step,
maintain a shadow 4-frame P0 stack only for querying the L2 teacher. Append:

```text
student_current_obs_seq
student_hidden_reset_mask
L2_teacher_action_for_same current visual/ego history
student outcome diagnostics
```

This reduces the mismatch between teacher-forced history and L3 deployment
history.

### Stage C: Guarded PPO Continuation

Only after route-screen v2 shows a distilled checkpoint clears L0 should PPO
continuation be considered. PPO must remain route-screen gated and should start
from a distilled checkpoint, not from the failed M555/M559 from-scratch policy.

## Seed Discipline

Do not use M556 seed `15560` or M560 seed `16560` as training targets for the
next selection claim.

Suggested split:

```text
distillation train seeds: 18000-18127
distillation validation seeds: 18128-18191
next route-screen selection seed: 17560
```

M556/M560 seed blocks may be reported as known diagnostics after selection, but
they must not determine the checkpoint chosen for public diagnostics.

## Pass/Fail Criteria

M562 corpus exporter passes if:

```text
records L2 teacher targets
records L3 72-value student observations
records done masks and terminal diagnostics
does not include public frozen-source rows
tests verify student_obs_dim = 72 and teacher stack is training-only
```

The later BC optimizer should pass only if:

```text
teacher-action MSE improves on train and validation seeds
student checkpoint metadata remains P0 L3
route-screen v2 seed 17560 clears L0 before any public diagnostic
```

If offline imitation improves MSE but route-screen still fails margin/collision,
the conclusion should be:

```text
L2 action imitation alone is insufficient; need closed-loop DAgger or abandon
this L3 recurrent recipe family.
```

## Next Milestones

```text
M562: implement L2 teacher corpus exporter and tests; no student training
M563: implement offline L3 behavior cloning optimizer; no PPO
M564: train BC smoke and evaluate route-screen v2 seed 17560
```

## Decision

```text
l2_to_l3_distillation_design_admit_m562_teacher_corpus_exporter
```
