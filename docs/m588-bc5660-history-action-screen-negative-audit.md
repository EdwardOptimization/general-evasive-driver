# M588 BC5660 History Action-Screen Negative Audit

## Purpose

M588 audits the negative M587 wrong/delayed-history action screen before any
outcome rollout or training change.

This milestone is audit-only:

```text
no evaluation
no training
no PPO
no behavior cloning
no checkpoint promotion
```

## M587 Result

M587 tested BC5660 on source-diverse matched-current pairs from M586:

```text
fresh route: 329 screened pairs
moderate-OOD: 287 screened pairs
```

Action-screen aggregates:

| surface | variant | pairs | mean action distance | above-threshold rows |
| --- | --- | ---: | ---: | ---: |
| fresh | wrong_matched_history | 329 | 0.000552 | 0 |
| fresh | delayed_history | 329 | 0.001658 | 0 |
| fresh | reset_hidden | 329 | 0.015801 | 119 |
| fresh | zero_action_history | 329 | 0.018689 | 189 |
| fresh | zero_current_response | 329 | 0.066799 | 329 |
| OOD | wrong_matched_history | 287 | 0.000764 | 0 |
| OOD | delayed_history | 287 | 0.001218 | 0 |
| OOD | reset_hidden | 287 | 0.014932 | 70 |
| OOD | zero_action_history | 287 | 0.018867 | 166 |
| OOD | zero_current_response | 287 | 0.070125 | 287 |

The pre-registered M587 admission rule required at least one surface to have
`wrong_matched_history` or `delayed_history` above-threshold count `>= 16` and
mean action distance `>= 0.02`.

Result:

```text
admission failed
persistent outcome rollout blocked
```

## Why This Is A Real Negative

The screen was not dead:

- `zero_current_response` is above threshold on every screened row on both
  surfaces.
- `zero_action_history` is action-sensitive on many rows on both surfaces.
- `reset_hidden` has some near-threshold action effect.

The specific no-signal result is limited to:

```text
wrong_matched_history
delayed_history
```

Therefore the strongest interpretation is not "the intervention harness failed."
It is:

```text
BC5660 action is dominated by current response, previous-command slots, and
scene context; accumulated hidden state is not materially changing action on
the matched-current surfaces we mined.
```

## Training Objective Audit

The BC optimizer is sequential and recurrent:

- `episode_start_seq` resets the hidden state at episode boundaries;
- each episode is replayed step by step through `model.forward_recurrent`;
- the checkpoint metadata records `actor_encoder = human_view_online_gru` and
  `recurrent_sequence_training = true`.

However, the actual loss is still one-step teacher-action MSE:

```text
student observation + recurrent hidden -> action
target = L2 teacher action at the same transition
loss = mean squared action error
```

There is no auxiliary objective requiring the hidden state to:

- predict future response envelope;
- distinguish delayed/wrong histories;
- encode dynamics capability;
- make different actions for matched current observations with different
  command-response histories.

So it is plausible that the BC branch succeeded at behavior transfer by using
the current 72-value frame and previous-command slots, while the actor head
learned little causal dependence on accumulated hidden state.

## Rejected Next Step

Do not run the pre-registered persistent outcome gate now.

Reason:

```text
M587 explicitly required wrong/delayed action sensitivity before outcome
rollout. That requirement failed on both surfaces.
```

Running the outcome gate anyway would turn the harness into a gate-passing
machine: it would ignore its own admission rule and spend compute on a branch
that the action screen already rejected.

## Next Branch

M589 should audit hidden-use and the BC objective before any training change.

Minimum questions:

1. Does the actor head structurally have a path from online hidden state to
   action under `human_view_online_gru`?
2. Does the trained BC5660 checkpoint show non-trivial hidden-to-action
   sensitivity under controlled hidden perturbations?
3. Does the BC corpus contain situations where current observation is similar
   but teacher action should differ because of history?
4. If not, what objective or corpus would be needed to make hidden history
   useful?

Candidate repair directions for later milestones:

- response-envelope or capability auxiliary targets;
- contrastive matched-current history objective;
- teacher/student preference loss using preferred and rejected recurrent
  hidden states;
- curriculum with longer pre-emergency warmup and hidden-condition variation;
- PPO only after hidden-use evidence is established.

## Decision

```text
bc5660_history_action_screen_negative_admit_hidden_use_objective_audit
```

M588 passes because it records the negative action-screen result, blocks
persistent outcome rollout, and redirects the research loop toward BC hidden-use
and objective audit.

## Next

```text
M589: audit BC hidden use and objective limitations before any repair training.
```
