# M1655 Paper-Route Selected Proposal Scope Sensitivity Design

## Summary

M1655 designs a no-checkpoint scope-sensitivity preflight after the M1653
actor_mean-only selected-proposal repair failure.

Decision:

```text
selected_proposal_scope_sensitivity_design_admit_no_checkpoint_implementation
```

The key design finding is that the current contour-aware exact-objective repair
path is feature-frozen: it builds recurrent policy features under `no_grad` and
detaches them before applying `actor_mean`. That is correct for M1640-M1653,
which were explicitly actor_mean-only, but it means simply setting upstream
parameters trainable would not test a wider policy scope. A wider-scope preflight
must explicitly recompute features with gradients enabled.

## Motivation

M1653 showed:

```text
alpha 0.2: no residual reduction
alpha 0.4: no residual reduction
alpha 1.0: 7.257% residual reduction, below the 25% candidate gate
```

This is enough to reject the pre-registered actor_mean-only selected-proposal
repair rule, but not enough to reject proposal repair as a route. The next
question is whether the failure is caused by:

```text
1. too narrow a trainable scope;
2. frozen-feature objective plumbing;
3. the same-line proposal geometry;
4. the fixed public exact-objective active set itself.
```

M1655 only designs the next preflight. It does not run projection, repair,
training, PPO, replay, or checkpoint artifact generation.

## Candidate Scopes

The checkpoint parameter inventory is:

```text
log_std
response_encoder.0.weight
response_encoder.0.bias
context_encoder.0.weight
context_encoder.0.bias
online_gru_cell.weight_ih
online_gru_cell.weight_hh
online_gru_cell.bias_ih
online_gru_cell.bias_hh
response_context_fusion.0.weight
response_context_fusion.0.bias
actor_mean.weight
actor_mean.bias
critic.weight
critic.bias
response_prediction_head.weight
response_prediction_head.bias
```

The scope preflight should compare these deterministic policy scopes:

| Scope | Parameters | Purpose |
| --- | --- | --- |
| `actor_mean` | `actor_mean.*` | M1653 baseline |
| `fusion_actor` | `response_context_fusion.0.*`, `actor_mean.*` | Tests whether final feature mixing is the missing degree of freedom |
| `context_fusion_actor` | `context_encoder.0.*`, `response_context_fusion.0.*`, `actor_mean.*` | Tests scene/context adaptation without changing response encoder or GRU |
| `response_fusion_actor` | `response_encoder.0.*`, `online_gru_cell.*`, `response_context_fusion.0.*`, `actor_mean.*` | Tests response/history feature-path adaptation without changing context encoder |
| `full_policy_actor` | response encoder, context encoder, GRU cell, fusion layer, actor mean | Tests the full deterministic actor path |

The preflight must exclude:

```text
critic.*
response_prediction_head.*
log_std
```

Those parameters are not used by the deterministic exact policy action
`tanh(actor_mean(features))` and should not become hidden repair degrees of
freedom.

## Required Modes

The implementation should run two diagnostic modes:

### Frozen Feature Mode

Reuse the M1640-M1653 feature bundle behavior:

```text
features = model.recurrent_features_tensor(obs, hidden) under no_grad
features = features.detach()
actions = tanh(actor_mean(features))
```

Expected result:

```text
only actor_mean gradients should be nonzero;
all upstream scope gradient norms should be zero or unavailable.
```

This verifies that M1653 was truly actor_mean-only and prevents accidentally
claiming wider-scope evidence from a frozen-feature objective.

### Differentiable Feature Mode

Recompute features with gradients enabled:

```text
features = model.recurrent_features_tensor(obs, hidden) with grad
actions = tanh(actor_mean(features))
```

Then compute the same correct/wrong hidden exact residual. This mode may only
write metrics; it must not save a checkpoint. For each selected proposal and
scope, it should record:

```text
initial exact residual
scope parameter count
scope gradient norm
finite-gradient flag
one-step damped reduction ratio
accepted one-step factor
max parameter delta during temporary in-memory candidate step
restore/checksum guardrails
```

The one-step candidate is allowed only as a temporary in-memory sensitivity
probe. It must restore the model before returning and must not be described as a
repaired checkpoint.

## Acceptance Gates

The implementation should pass if:

```text
selected_candidate_count == 3
scope_count >= 5
frozen_feature_upstream_grad_zero == true
differentiable_feature_scope_measurable_count >= scope_count
primary_alpha_0_2_wider_scope_nonzero_grad_count >= 1
primary_alpha_0_2_wider_scope_reduction_count >= 1
checkpoint_artifact_count == 0
model_restored_after_probe_count == selected_candidate_count * scope_count
diagnostic_rows_used_as_positive_count == 0
donor_plus_action_used_as_loss_target_count == 0
training_started_count == 0
ppo_used_count == 0
promoted_count == 0
private_holdout_used_count == 0
actor_input_contract_changed_count == 0
level3_self_id_claim_count == 0
```

If the differentiable wider scopes have nonzero gradients but still cannot
reduce alpha `0.2`, the branch should audit whether same-line selected proposals
are the wrong proposal source. If wider scopes can reduce alpha `0.2`, the next
step should still be an audit before any full repair or checkpoint artifact.

## Guardrails

Forbidden:

```text
checkpoint artifact write
state_dict overwrite
base interpolation
training loop
PPO
closed-loop replay
promotion
private holdout
actor input change
diagnostics as positive loss targets
donor_plus_hidden_action as loss target
paper-level claim
level3 self-identification claim
```

The preflight must write only metrics and must keep selected-proposal artifacts
public/debug-only.

## Next Route

M1655 admits exactly one bounded implementation:

```text
m1656-paper-route-selected-proposal-scope-sensitivity-implementation
```

M1656 should implement the two-mode scope-sensitivity preflight and write
metrics only. Regardless of pass or fail, the next step after M1656 must be a
result audit before any wider-scope repair implementation, checkpoint artifact,
replay gate, PPO, or promotion.
