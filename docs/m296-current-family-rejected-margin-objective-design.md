# M296 Current-Family Rejected-Margin Objective Design

M296 designs the next repair mechanism after M295. No PPO was run, no actor
inputs were changed, and no checkpoint is promoted.

## Problem

M291 and M294 fail on the same mechanism: PPO makes some current-family
wrong-history rollouts safe while preserving the old M183/M170 surface.

M294 proves that stronger rejected-history trajectory anchoring has signal, but
it is still the wrong control variable:

```text
M291 raw failed M267/M264 rows: 6, 11, 15, 16
M294 raw failed M267/M264 rows: 6, 15, 16
M294 recovered row:             11
M291 exact M270 delta:          +0.000502706
M294 exact M270 delta:          +0.000615299
```

So the repair needs to target the counterfactual outcome relation directly:

```text
correct history + current observation should support the successful action
wrong history   + same observation should not support that same successful action
wrong history   + same observation should prefer its own rejected-history action
```

This remains a training-time counterfactual objective. The deployable actor
still receives only the human-view observation and recurrent state.

## Why Existing Losses Are Not Enough

The current `outcome_weighted_intervention_loss` is useful but incomplete:

```text
softplus(logp_wrong_hidden(preferred_action)
       - logp_correct_hidden(preferred_action)
       + margin)
```

It discourages the wrong hidden state from assigning high probability to the
correct-history action. It does not tell the wrong hidden state what action it
should prefer instead, and it does not encode the row-level terminal-margin
floor that defines the proof surface.

The current trajectory action anchor has the opposite problem. It tells the
policy to imitate a stored action trajectory, but it does not encode the
paired preference:

```text
this action is acceptable because it is the wrong-history rejected action,
not because all base-policy actions should be copied more strongly
```

M294 shows that simply increasing this action-anchor pressure can locally
recover one row while worsening exact M270 everywhere along interpolation.

## New Corpus Contract

M297 should implement a `RejectedHistoryPreferenceSnippets` corpus. It should
be built from the M267/M264 boundary rows and the current M290 base.

Required NPZ arrays:

```text
observation          float32 [N, 72]
preferred_hidden     float32 [N, hidden_dim]
rejected_hidden      float32 [N, hidden_dim]
preferred_action     float32 [N, 3]
rejected_action      float32 [N, 3]
preferred_score      float32 [N]
rejected_score       float32 [N]
score_delta          float32 [N]
normal_margin        float32 [N]
wrong_history_margin float32 [N]
margin_floor         float32 [N]
weight               float32 [N]
row_id               int64   [N]
group_index          int64   [N]
target_index         int64   [N]
```

The metadata CSV should also keep:

```text
physical_pair_key
target
left_seed
right_seed
left_step
right_step
relocated_obstacle_body_x
relocated_obstacle_body_y
relocated_obstacle_half_width
base_wrong_history_terminal_reason
```

`preferred_action` is the base action under the correct history. `rejected_action`
is the base action under the wrong matched history for the same observation.
The objective does not use hidden vehicle parameters or oracle actor inputs.

## Loss

For each sampled row:

```text
logp_cp = log pi(a_pref | observation, preferred_hidden)
logp_wp = log pi(a_pref | observation, rejected_hidden)
logp_wr = log pi(a_rej  | observation, rejected_hidden)
```

Use a weighted pairwise loss:

```text
L_pref_separation = softplus(logp_wp - logp_cp + m_pref)
L_wrong_preference = softplus(logp_wp - logp_wr + m_wrong)

L = mean_w(
      L_pref_separation
    + lambda_wrong * L_wrong_preference
)
```

Optional conservative term for later, disabled in the first sanity check unless
needed:

```text
L_correct_anchor = -logp_cp
```

This differs from a trajectory action anchor in two ways:

1. It is a pairwise preference on the same observation under two histories.
2. The rejected action is only preferred under the counterfactual wrong-history
   hidden state, not under the deployable correct-history state.

## Weighting

The initial M297 weights should be deterministic and capped:

```text
base_weight = existing M267/M264 outcome weight
failed_row_bonus = 4.0 for rows 6, 15, 16
recovered_row_bonus = 2.0 for row 11
near_zero_bonus = clip(0.001 / max(abs(base_wrong_margin), 1e-6), 1.0, 4.0)
weight = clip(base_weight * failed_or_recovered_bonus * near_zero_bonus, 0.0, 100.0)
```

Rows 6, 15, and 16 get extra weight because M294 still fails them. Row 11 gets
a smaller bonus because M294 shows the mechanism can recover it.

## Sanity Gates

M297 should be an implementation/objective-sanity milestone, not PPO.

Required checks:

```text
loader validates shape, finite values, positive weights
loss is finite on M290, M291 raw, and M294 raw
M290 loss < M291 raw loss on the M267/M264 preference corpus
M290 loss < M294 raw loss on the M267/M264 preference corpus
per-row report shows rows 6, 15, 16 remain worse for M294 than M290
row 11 shows the expected partial repair signal from M291 to M294
```

Promotion remains blocked. Passing M297 should only admit an objective-only
update or a no-training projection probe, not PPO.

## PPO Admission Rule

PPO remains blocked until a later milestone satisfies all of these:

```text
new preference loss passes objective sanity
objective-only update or interpolation improves the new loss
exact M270 does not regress
M183/M170 and M267/M264 replay gates both pass
protected-key and behavior gates pass
```

Only then should a smoke-scale PPO attempt be pre-registered.

## Next Step

M297 should implement the corpus loader, preference loss, exact evaluator, and
tests. It should not run PPO.

```text
m297-current-family-rejected-preference-objective-implementation
```
