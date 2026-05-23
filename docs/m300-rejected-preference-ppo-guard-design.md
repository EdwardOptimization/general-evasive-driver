# M300 Rejected-Preference PPO Guard Design

M300 designs the next PPO path after M299 promoted `m298pref_a020` as the
public-gate base. No PPO was run, no actor update was run, and actor inputs are
unchanged.

## Problem

The project now has a better public-gate base:

```text
runs/m298_rejected_preference_objective_only_probe/interpolation/checkpoints/alpha_0_02.pt
```

M299 promoted it because it improves both fixed objectives and passes the full
public-gate stack:

```text
M297 rejected-preference loss delta = -0.0021904706954956055
Exact M270 loss delta = -0.0013321638107299805
```

But this does not remove the main PPO risk. M291 and M294 showed that smoke PPO
can make current-family M267/M264 wrong-history rollouts safe even when broad
behavior looks retained. M298 also showed the same pattern in a sharper form:
the raw preference-objective update improved fixed losses but collapsed replay
normal success to `0 / 17`.

So the next PPO run must not simply restart from M299. It needs a training-time
guard for the exact rejected-history preference failure mode.

## Existing Hooks

`train_ppo.py` already has a recurrent-sequence auxiliary loss pattern for:

```text
outcome_intervention_aux_coef
outcome_intervention_source_losses
snippet_action_anchor_coef
trajectory_action_anchor_coef
baseline_action_anchor_coef
```

M297/M298 added the missing loss primitive:

```text
load_rejected_history_preference_snippets
rejected_history_preference_loss
```

This can be wired into PPO the same way the existing outcome-intervention loss
is wired: load the corpus once before training, apply a sampled auxiliary loss
inside the recurrent sequence update loop, and record a metric.

## Selected Guard

Add a dedicated PPO auxiliary loss:

```text
rejected_history_preference_aux_coef
rejected_history_preference_snapshot_npz
rejected_history_preference_batch_size
rejected_history_preference_preferred_logprob_margin
rejected_history_preference_wrong_logprob_margin
rejected_history_preference_wrong_preference_coef
```

The loss is:

```text
L = weighted_mean(
  softplus(logp_wrong_hidden_preferred_action - logp_correct_hidden_preferred_action + margin_pref)
  + wrong_coef * softplus(logp_wrong_hidden_preferred_action - logp_wrong_hidden_rejected_action + margin_wrong)
)
```

This is different from a trajectory anchor. It does not say "always imitate one
action"; it says:

```text
under correct history, keep the correct-history action likely;
under wrong history, do not also make the correct-history action likely;
under wrong history, keep the rejected-history action more likely than the
correct-history action.
```

That directly targets the observed washout: PPO was raising wrong-history
margins on M267/M264 rows 6, 11, 15, and 16.

## M301 Implementation Plan

M301 should implement only infrastructure and tests, not PPO:

1. Extend `PPOConfig` with the rejected-preference fields.
2. Validate that the loss requires `recurrent_sequence_training`.
3. Load the corpus with `load_rejected_history_preference_snippets`.
4. Add the sampled loss inside the recurrent sequence update loop.
5. Append `rejected_history_preference_loss_mean` to training metrics.
6. Add focused tests for config validation and a tiny loss-wiring path.

The actor observation contract must not change. The saved hidden states in the
preference corpus are training-time intervention data, not actor inputs.

## M302 Smoke Design

Only after M301 passes, run one smoke-scale PPO from M299:

```text
init_checkpoint = runs/m298_rejected_preference_objective_only_probe/interpolation/checkpoints/alpha_0_02.pt
total_steps = 1024
learning_rate <= 1e-6
freeze_log_std = true
actor_encoder = human_view_online_gru
rejected_history_preference_aux_coef = small positive value
```

Keep the existing guard family:

```text
baseline action anchor from M299
M270 outcome intervention loss
M267/M264 rejected-history preference loss
trajectory/replay anchors only if they are already validated
```

## M302 Gate Order

The smoke PPO must be rejected before replay if either exact objective regresses:

```text
1. Exact M297 rejected-preference no-regression versus M299.
2. Exact M270 no-regression versus M299.
3. M183/M170 first replay gate.
4. M267/M264 first replay gate.
5. Interpolation only if exact objectives are non-regressing and direction is useful.
6. Full replay stack.
7. Protected-key guard.
8. Behavior seeds 9505 and 9506.
```

Promotion remains blocked if:

```text
M267/M264 success drops fall below 17 / 17
M183/M170 loses any normal-success row
exact M297 or exact M270 gets worse
protected key fails
behavior seeds regress
safe interpolation collapses to a micro-alpha
```

## Decision

Do not run PPO yet. Implement the training-time rejected-preference auxiliary
loss first.

Decision:

```text
implement_rejected_preference_ppo_aux_loss
```

Next step:

```text
m301-rejected-preference-ppo-aux-loss-implementation
```
