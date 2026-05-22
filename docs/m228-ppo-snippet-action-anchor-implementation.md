# M228 PPO Snippet Action Anchor Implementation

M228 implements the infrastructure requested by M227: PPO can now anchor action
means on boundary outcome snippets, not only on rollout states.

No PPO smoke is run in M228. Actor inputs are unchanged.

## Motivation

M226 failed because the guarded PPO recipe used:

```text
outcome_intervention_aux_coef
baseline_action_anchor_coef
```

The action anchor was collected from rollout states. It did not directly protect
the M223/M183 proof-surface snippet states.

M224/M225 were stable because their supervised actor update used:

```text
snippet_action_anchor_coef
snippet_action_anchor_preferred_only = true
```

M228 adds the same mechanism to PPO.

## Implementation

New `PPOConfig` fields:

```text
snippet_action_anchor_coef
snippet_action_anchor_checkpoint
snippet_action_anchor_snapshot_npz
snippet_action_anchor_batch_size
snippet_action_anchor_preferred_only
```

The loss path loads an outcome snippet corpus and an anchor checkpoint, evaluates
the anchor checkpoint on:

```text
observation
preferred_hidden
```

and penalizes PPO action-mean drift on those exact proof-surface states. By
default it is preferred-only, matching M216/M224/M225.

Shared helper functions were added to `intervention_objectives.py`:

```text
build_snippet_action_anchor
snippet_action_anchor_loss
```

PPO training metrics now include:

```text
snippet_action_anchor_loss_mean
```

when the loss is enabled.

## Tests

Focused tests added:

```text
test_train_requires_snippet_action_anchor_checkpoint
test_train_logs_snippet_action_anchor_loss
```

These verify that PPO rejects an enabled snippet anchor without an anchor
checkpoint and logs the snippet anchor loss during a tiny recurrent PPO update.

## M229 Config

Pre-registered config:

```text
configs/ppo_m229_snippet_anchor_from_m224_smoke.json
```

It starts from M224 and adds:

```text
baseline_action_anchor_coef = 100
snippet_action_anchor_coef = 100
snippet_action_anchor_preferred_only = true
snippet_action_anchor_snapshot_npz = runs/m223_m219_boundary_outcome_corpus_seed10060/boundary_outcome_corpus.npz
```

## Decision

M228 is infrastructure-complete. It does not promote a driver checkpoint.

Next milestone:

```text
m229-snippet-anchored-ppo-smoke-from-m224
```

M229 should run exactly one PPO smoke from M224 and gate fixed M223 objective,
old/current/new replay surfaces, behavior seeds, and protected key before any
repeat or longer PPO continuation.
