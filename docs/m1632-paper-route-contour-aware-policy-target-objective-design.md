# M1632 Paper-Route Contour-Aware Policy Target Objective Design

## Summary

M1632 designs role-safe objective semantics over the M1630 materialized
policy-target tensors.

Decision:

```text
contour_aware_policy_target_objective_design_admit_exact_evaluator
```

This milestone is design-only. It does not implement a loss, does not write an
objective config artifact, does not update an actor, does not train, does not
run PPO, does not promote a checkpoint, does not use private holdout, and does
not claim level3 self-identification.

## Inputs

Use only the audited M1630 public materialization package:

```text
runs/m1630_contour_aware_full_target_materialization/positive_policy_targets.npz
runs/m1630_contour_aware_full_target_materialization/diagnostic_policy_guardrails.npz
runs/m1630_contour_aware_full_target_materialization/positive_policy_target_rows.csv
runs/m1630_contour_aware_full_target_materialization/diagnostic_policy_guardrail_rows.csv
runs/m1630_contour_aware_full_target_materialization/summary.json
```

Expected tensors:

```text
positive observation: [39, 72]
positive correct_hidden / wrong_hidden: [39, 128]
positive preferred_action / wrong_history_action / donor_plus_hidden_action: [39, 3]

diagnostic observation: [232, 72]
diagnostic correct_hidden / wrong_hidden: [232, 128]
diagnostic preferred_action / wrong_history_action / donor_plus_hidden_action: [232, 3]
```

The actor input contract remains unchanged. Hidden states are training/evaluator
state for the recurrent actor, not new actor observations.

## Role Boundaries

### Positive Targets

Only `positive_policy_targets.npz` rows may contribute positive target weight.
They carry:

```text
corpus_role=positive_candidate
used_as_positive=true
role_weight=1.0
```

Their objective role is to preserve the current clean active-set relation:

```text
same canonical observation;
correct history hidden should support the preferred action;
wrong history hidden should support the wrong-history action;
wrong history hidden should not collapse onto the preferred action.
```

### Diagnostic Guardrails

`diagnostic_policy_guardrails.npz` rows are never positive targets.

They carry:

```text
corpus_role=diagnostic_guardrail
used_as_positive=false
role_weight=0.0
training_ready=false
```

Diagnostics may be evaluated and reported, but they must not reduce a future
positive objective or provide gradient as positive examples. If a future
implementation gives diagnostics nonzero positive weight, the objective fails
lexicographically before any scalar score is considered.

## V1 Objective Semantics

M1633 should implement a no-update exact evaluator first. The evaluator should
compute deterministic action residuals for the base checkpoint:

```text
a_cp = pi(observation, correct_hidden)
a_ww = pi(observation, wrong_hidden)

r_correct = ||a_cp - preferred_action||_2
r_wrong = ||a_ww - wrong_history_action||_2
d_target = ||preferred_action - wrong_history_action||_2
d_policy = ||a_cp - a_ww||_2
```

For positive rows, the V1 exact residual is:

```text
L_positive_exact =
    mean_w(r_correct^2)
  + lambda_wrong * mean_w(r_wrong^2)
  + lambda_sep * mean_w(max(0, m_sep - d_policy)^2)
```

Initial evaluator constants:

```text
lambda_wrong = 1.0
lambda_sep = 0.25
m_sep = min(0.05, quantile(d_target, 0.25))
```

The separation term is a collapse guard, not proof of self-identification. It
prevents an implementation from preserving only the correct-history branch
while letting the wrong-history branch drift toward the same action.

## Optional Log-Probability Form

If the policy distribution API is available and stable, a later implementation
may also report the log-probability preference form:

```text
logp_cp = log pi(preferred_action | observation, correct_hidden)
logp_wp = log pi(preferred_action | observation, wrong_hidden)
logp_ww = log pi(wrong_history_action | observation, wrong_hidden)

L_pref_separation = softplus(logp_wp - logp_cp + m_pref)
L_wrong_preference = softplus(logp_wp - logp_ww + m_wrong)
```

This log-probability form must remain secondary until the deterministic
action-residual evaluator passes, because M1630's targets were captured from
deterministic `act_recurrent` behavior.

## Donor-Plus-Hidden Limitation

M1630 saved `donor_plus_hidden_action`, but it did not save the
donor-response observation used to produce that action. Therefore M1632 does
not allow `donor_plus_hidden_action` to become a training objective target.

Allowed use:

```text
report action-divergence diagnostics;
check finite values and source-action reproduction;
support future schema design if donor-response observation is needed.
```

Forbidden use:

```text
treat donor_plus_hidden_action as a target for pi(observation, wrong_hidden);
claim a donor-response/action objective was evaluated;
train on donor_plus_hidden_action without materializing donor_plus_observation.
```

If a future branch needs donor-response/action training, it must first design
and audit a materialization schema that stores the corresponding observation.

## Lexicographic Acceptance

The exact evaluator must apply this order:

1. Load and shape-check positive and diagnostic tensor bundles.
2. Verify all values are finite.
3. Verify diagnostic rows are zero-weight and non-positive.
4. Verify the checkpoint hash is unchanged after evaluation.
5. Evaluate positive deterministic residuals and separation metrics.
6. Report diagnostic residuals separately as guardrails.
7. Keep objective/loss config, actor update, PPO, promotion, and private
   holdout blocked.

A scalar improvement cannot override any role-integrity or actor-contract
violation.

## M1633 Exact Evaluator Requirements

The next implementation should be a no-update evaluator:

```text
src/autodrift/contour_aware_policy_target_exact_evaluator.py
tests/test_contour_aware_policy_target_exact_evaluator.py
runs/m1633_contour_aware_policy_target_exact_evaluator/summary.json
```

Minimum artifacts:

```text
positive_objective_rows.csv
diagnostic_guardrail_rows.csv
objective_summary.csv
shape_summary.csv
guardrail_summary.csv
summary.json
```

Minimum public gates:

```text
positive_policy_target_count == 39
diagnostic_policy_guardrail_count == 232
positive_action_residuals_finite == true
diagnostic_action_residuals_finite == true
positive_source_action_reproduction_l2_max <= 1e-6
diagnostic_rows_used_as_positive == false
diagnostic_positive_weight_sum == 0.0
donor_plus_action_used_as_loss_target == false
checkpoint_weights_mutated == false
loss_constructed == false
objective_config_written == false
training_started == false
ppo_used == false
promoted == false
private_holdout_used == false
actor_input_contract_changed == false
labels_enter_actor_input == false
level3_self_id_claim_made == false
```

The evaluator may report exact objective metrics, but it must not optimize
them. Any actor update requires a later design and audit.

## Unsupported Claims

M1632 does not support:

```text
the objective has been implemented;
the objective improves any checkpoint;
the donor-plus branch is a valid training target;
actor update or PPO is admitted;
candidate rows are paper-level evidence;
closed-loop behavior improved;
the driver has level3 self-identification.
```

## Decision

Admit one no-update exact evaluator implementation:

```text
m1633-paper-route-contour-aware-policy-target-exact-evaluator-implementation
```

Do not route directly to actor update, PPO, promotion, private holdout, or
paper-level claims.
