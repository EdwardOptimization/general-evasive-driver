# M1658 Paper-Route Fusion Actor Proposal Repair Design

## Summary

M1658 designs the minimal wider-scope no-checkpoint repair route admitted by the
M1657 audit.

Decision:

```text
fusion_actor_repair_design_route_to_branch_synthesis
```

The design chooses `fusion_actor`:

```text
response_context_fusion.0.*
actor_mean.*
```

It does not widen into `context_encoder`, `response_encoder`, or
`online_gru_cell`, because M1656 already showed the smallest wider scope has
essentially the same one-step primary alpha `0.2` reduction as larger scopes.

## Scope

Trainable scope for the implementation:

```text
response_context_fusion.0.weight
response_context_fusion.0.bias
actor_mean.weight
actor_mean.bias
```

Excluded:

```text
response_encoder.*
context_encoder.*
online_gru_cell.*
critic.*
response_prediction_head.*
log_std
```

The repair objective must use differentiable features:

```text
features = model.recurrent_features_tensor(obs, hidden) with grad enabled
actions = tanh(actor_mean(features))
```

The old frozen-feature mode may be reported as diagnostic context but must not
be used as evidence that upstream repair is possible.

## Candidate Set

Use the same selected proposal candidates as M1653 and M1656:

```text
alpha 0.2: primary
alpha 0.4: intermediate
alpha 1.0: stress
```

Base anchor:

```text
runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt
```

Selected proposals:

```text
runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_2.pt
runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_4.pt
runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_1_0.pt
```

Materialized tensor source:

```text
runs/m1630_contour_aware_full_target_materialization
```

## Repair Rule

The implementation should run a no-checkpoint in-memory damped projection:

```text
1. load proposal checkpoint;
2. freeze all parameters except fusion_actor;
3. compute differentiable-feature exact residual on positive rows;
4. take normalized negative-gradient candidate steps with backtracking;
5. accept only finite residual-reducing steps that do not expand the fusion_actor distance to base;
6. stop when reduction ratio reaches the candidate threshold or no candidate step is accepted;
7. record best in-memory metrics;
8. restore model state before returning;
9. write metrics only, never checkpoint artifacts.
```

The implementation may reuse M1656 tensor loading, feature-mode, and guardrail
helpers, but the output must be a repair metric artifact, not a checkpoint.

## Acceptance Gates

Candidate gate:

```text
initial_exact_residual > 1e-8
repaired_exact_residual < initial_exact_residual
reduction_ratio >= 0.25
accepted_backtracking_step_count >= 1
fusion_actor_l2_to_base does not expand beyond the current proposal distance
excluded_parameter_delta_max == 0
model_restored_after_probe == true
guardrail_violation_count == 0
```

Aggregate gate:

```text
selected_candidate_count == 3
measurable_initial_residual_count == 3
candidate_public_pass_count >= 1
primary_alpha_0_2_pass == true
checkpoint_artifact_count == 0
excluded_parameter_delta_violation_count == 0
model_restored_after_probe_count == selected_candidate_count
diagnostic_rows_used_as_positive_count == 0
donor_plus_action_used_as_loss_target_count == 0
training_started_count == 0
ppo_used_count == 0
promoted_count == 0
private_holdout_used_count == 0
actor_input_contract_changed_count == 0
level3_self_id_claim_count == 0
```

The stress alpha `1.0` should be reported, but it is not required to pass for
the first implementation. If primary alpha `0.2` fails, the route must go to
audit rather than tuning the rule in place.

## Public-Overfit Boundary

This remains public fixed-tensor evidence. A pass would justify only:

```text
fusion_actor no-checkpoint exact repair works on selected same-line proposal tensors.
```

It would not justify:

```text
checkpoint artifact generation;
closed-loop replay;
behavior retention;
PPO continuation;
private-holdout or paper-level evidence;
level3 self-identification.
```

## Next Route

M1658 does not admit implementation directly, because the workflow synthesis
cadence has been reached. The next required step is branch synthesis:

```text
m1659-paper-route-proposal-projection-repair-branch-synthesis
```

M1659 must synthesize M1649-M1658 before any fusion_actor implementation,
checkpoint artifact, replay gate, PPO, or promotion.
