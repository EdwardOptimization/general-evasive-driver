# M589 BC Hidden-Use Objective Audit

## Purpose

M589 audits why the scaled L3 behavior-cloned driver transfers L2 route
behavior but does not show meaningful delayed-history or wrong-history
action sensitivity in M587.

This milestone is audit-only:

```text
no evaluation
no training
no PPO
no behavior cloning
no checkpoint promotion
```

## Evidence Reviewed

M587 screened BC5660 on the M586 matched-current pair surfaces:

| surface | variant | pairs | mean action distance | above-threshold rows |
| --- | --- | ---: | ---: | ---: |
| fresh | wrong_matched_history | 329 | 0.000552 | 0 |
| fresh | delayed_history | 329 | 0.001658 | 0 |
| fresh | zero_action_history | 329 | 0.018689 | 189 |
| fresh | zero_current_response | 329 | 0.066799 | 329 |
| OOD | wrong_matched_history | 287 | 0.000764 | 0 |
| OOD | delayed_history | 287 | 0.001218 | 0 |
| OOD | zero_action_history | 287 | 0.018867 | 166 |
| OOD | zero_current_response | 287 | 0.070125 | 287 |

This is a clean diagnostic split:

```text
current-response and previous-command controls are live
wrong/delayed recurrent history is not action-sensitive on these surfaces
```

## Structural Hidden Path

The L3 actor architecture does have a structural path from recurrent hidden
state to action under `human_view_online_gru`.

In `ActorCritic`:

```text
response_obs -> response_encoder
previous_hidden + response_encoded -> online_gru_cell -> next_hidden
context_obs -> context_encoder
[next_hidden, context_encoded, next_hidden * context_encoded]
  -> response_context_fusion
  -> actor_mean
```

So the negative M587 result is not explained by a missing network path. The
actor can, in principle, use accumulated command-response history.

## BC Objective

The L3 BC optimizer is recurrent and sequence-trained. It resets hidden state
at episode boundaries and replays each episode step by step:

```text
hidden = initial_hidden()
for transition in episode:
    action = tanh(actor(obs_t, hidden_t).mean)
    hidden_{t+1} = GRU(obs_t_response, hidden_t)
```

However, the optimized loss is one-step teacher-action MSE:

```text
loss_t = mean((student_action_t - teacher_action_t)^2)
```

There is no objective that requires hidden state to:

- predict future response envelope;
- estimate braking, yaw, or lateral authority;
- preserve different actions under matched-current but different histories;
- make wrong-history hidden states produce rejected actions;
- make delayed-history hidden states produce degraded or delayed actions.

Therefore low BC MSE is compatible with a mostly current-frame policy. The
student can copy L2 route behavior through the 72-value current frame, previous
command slots, actuator state, and scene geometry without forming a causal
belief state in the online GRU.

## Corpus Audit

The scaled BC corpora contain:

```text
student_obs_seq       (72-value P0 L3 frames)
teacher_action_seq    (3-value L2 teacher action)
done_seq
episode_start_seq
episode_id_seq
step_seq
seed_seq
```

They deliberately do not store `teacher_obs_stack_seq`, which preserves the P0
student input contract.

The gap is not input leakage. The gap is that the corpus is supervised as
independent teacher-action targets along source episodes. It does not present
a matched-current contrast such as:

```text
same current observation and scene
different command-response history
teacher or outcome says the preferred action should differ
```

Without that contrast, the optimizer has no direct pressure to make hidden
state action-relevant.

## Interpretation

M589 supports this claim:

```text
BC5660 is a deployable P0 L3 online-GRU actor and the network can structurally
route recurrent hidden state into the action head.
```

M589 does not support this claim:

```text
BC5660 has learned accumulated hidden-state self-identification from the
scaled BC objective.
```

The best current diagnosis is:

```text
scaled L2-to-L3 BC transferred useful route behavior, but the objective mostly
trained one-step action imitation and did not force hidden-to-action causality.
```

This matches the M582-M588 evidence:

- route and OOD behavior are L2-competitive;
- zero-current response strongly degrades behavior;
- wrong/delayed recurrent history does not change action on matched-current
  surfaces.

## Next Probe

Before repair training, the next milestone should directly measure hidden-use
sensitivity:

```text
M590: hidden-action sensitivity probe design
```

The probe should separate three questions:

1. Does the trained actor head ignore hidden features entirely?
2. Are real rollout hidden states collapsed or too similar to affect action?
3. Are M586/M587 wrong-history pairs too weak even though out-of-distribution
   hidden perturbations affect action?

Required M590 metrics:

- fusion-layer weight norms by chunk:
  `next_hidden`, `context`, and `next_hidden * context`;
- action response to normal, reset, zero, delayed, wrong, shuffled, scaled, and
  random hidden states;
- hidden-distance versus action-distance correlation on M586 rows;
- comparison across BC5660, BC5661, and BC5662;
- no deployable actor input changes and no promotion.

Interpretation rules should be pre-registered:

| result | interpretation |
| --- | --- |
| real wrong/delayed hidden has no effect but random hidden affects action | real BC hidden states are collapsed or action-equivalent |
| random hidden also has no effect | actor head effectively ignores hidden path |
| random and wrong hidden both affect action | M587 pair surface may be too weak |
| only zero-current and zero-action affect action | BC branch is current-frame dominant |

## Decision

```text
bc_hidden_use_objective_audit_admit_sensitivity_probe
```

M589 passes because it identifies a structural hidden-to-action path, a
one-step BC objective bottleneck, and a concrete no-oracle hidden-action
sensitivity probe before any repair training.

## Next

```text
M590: design the BC hidden-action sensitivity probe.
```
