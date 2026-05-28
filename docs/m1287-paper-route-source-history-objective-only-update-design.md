# M1287 Paper-Route Source-History Objective-Only Update Design

## Summary

M1287 designs the first bounded update step after the M1286 branch synthesis.

Decision:

```text
source_history_objective_only_update_design_admit_tiny_actor_mean_implementation
```

The next step should implement a tiny no-PPO objective-only probe:

```text
m1288-paper-route-source-history-objective-only-update-implementation
```

M1287 does not train a policy, does not run PPO, does not promote a checkpoint,
does not use private holdout, and does not change the actor input contract.

## Blocker

M1285 made the source-history residual measurable:

```text
row_count: 152
finite_row_count: 152
exact_objective_finite: true
combined_loss_mean: 18.6105005708
correct_preference_loss_mean: 9.3052502854
wrong_history_preference_loss_mean: 9.3052502854
```

M1283 showed the current public-gate checkpoint reacts to source histories, but
not in the desired direction:

```text
both_directional_fraction: 0.0
preferred_hidden_margin_positive_fraction: 0.4868421053
history_action_l2_mean: 0.0991899077
```

Interpretation:

```text
The recurrent hidden state changes the action mean, so the generated histories
are visible to the actor. The public-gate checkpoint has not learned the new
correct-history versus wrong-history semantics.
```

Therefore PPO remains blocked. The next admissible question is narrower:

```text
Can an exact objective-only update reduce the M1285 residual without immediately
changing actor inputs or entering PPO?
```

## Update Scope

Use the current public-gate base:

```text
runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt
```

The first implementation should update only the final action-mean head:

```text
trainable_scope: actor_mean_only
```

Reason:

```text
M1283 already observed nonzero action movement under different source histories.
Updating only the final mean head tests whether the existing hidden/context
features contain enough separability before touching recurrent or encoder
weights.
```

Do not start with:

```text
response_encoder;
GRU weights;
context encoder;
fusion trunk;
log_std;
critic;
PPO rollout/update machinery.
```

Those scopes remain future escalation options only if the actor-mean probe is
finite, bounded, and retention-safe enough to justify another design milestone.

## Exact Objective

For each row:

```text
o      = current 72-value intervention observation
h_c    = hidden state after correct source response history
h_w    = hidden state after same-pair wrong source response history
a_p    = preferred source action
a_r    = rejected source action
```

Policy log-probabilities:

```text
logp_cp = log pi(a_p | o, h_c)
logp_cr = log pi(a_r | o, h_c)
logp_wp = log pi(a_p | o, h_w)
logp_wr = log pi(a_r | o, h_w)
```

Loss:

```text
L_correct = softplus(logp_cr - logp_cp + 0.05)
L_wrong   = softplus(logp_wp - logp_wr + 0.05)
L_total   = mean(L_correct + L_wrong)
```

The exact full-corpus M1285 objective must be evaluated before and after the
update. It is the first gate.

## M1288 Probe Budget

M1288 should be a tiny implementation probe, not a training campaign:

```text
optimizer: Adam
trainable scope: actor_mean_only
steps: 100
learning_rate: 0.0001
batching: full 152-row exact corpus, or deterministic minibatches with exact
          full-corpus before/after evaluation
gradient clipping: enabled if already local to the optimizer helper
PPO: disabled
promotion: disabled
private holdout: disabled
```

The probe may write a raw candidate checkpoint for diagnosis:

```text
runs/m1288_source_history_objective_only_update/checkpoints/raw_objective_update.pt
```

This checkpoint is not promotable in M1288. It is an artifact for the next audit.

## Required Artifacts For M1288

M1288 should write:

```text
runs/m1288_source_history_objective_only_update/summary.json
runs/m1288_source_history_objective_only_update/objective_before.json
runs/m1288_source_history_objective_only_update/objective_after.json
runs/m1288_source_history_objective_only_update/source_history_objective_rows_before.csv
runs/m1288_source_history_objective_only_update/source_history_objective_rows_after.csv
runs/m1288_source_history_objective_only_update/train_trace.csv
runs/m1288_source_history_objective_only_update/parameter_delta.json
runs/m1288_source_history_objective_only_update/checkpoints/raw_objective_update.pt
```

The summary must include:

```text
base_combined_loss_mean
after_combined_loss_mean
combined_loss_delta
base_correct_preference_loss_mean
after_correct_preference_loss_mean
base_wrong_history_preference_loss_mean
after_wrong_history_preference_loss_mean
finite_before
finite_after
trainable_scope
trainable_parameter_count
frozen_parameter_count
non_actor_mean_mutation_detected
ppo_used
promoted
private_holdout_used
actor_input_contract_changed
```

## Gate Order

M1288 should use this order:

```text
1. checkpoint contract gate
2. actor-input contract unchanged gate
3. trainable-scope gate: only actor_mean parameters changed
4. exact M1285 before/after finite gate
5. exact M1285 improvement gate
6. checkpoint-delta/trust-region diagnostics
7. no promotion; route to result audit
```

Do not run old public replay gates before exact objective improves. If exact
loss does not improve, replay gates are not informative and should not be used
to rescue the candidate.

## Exact Improvement Criteria

M1288 should be conservative. A pass requires:

```text
finite_before: true
finite_after: true
combined_loss_delta < 0
correct_preference_loss_delta <= 0
wrong_history_preference_loss_delta <= 0
non_actor_mean_mutation_detected: false
ppo_used: false
promoted: false
private_holdout_used: false
actor_input_contract_changed: false
```

If the combined loss improves by less than a small practical threshold, record
the candidate as weak-positive rather than promote it. Promotion is forbidden in
M1288 either way.

## Retention Planning

M1288 is not allowed to promote and does not need full replay gates. Its result
should route to one of these next milestones:

```text
objective_update_result_audit
  if exact loss improves and mutation guardrails pass;

source_history_update_scope_repair
  if actor_mean_only cannot improve the exact residual;

source_history_corpus_refresh_design
  if loss improves too easily or appears overfit to the 152 public rows;

old_public_retention_design
  if a later audit finds obvious public proof washout risk.
```

The first later closed-loop retention stack, after a successful exact-loss
probe and result audit, should include:

```text
M1285 exact objective non-regression;
M1283 policy-gate metrics;
old public replay surfaces;
protected key diagnostics;
behavior seeds;
fresh source-history refresh before paper-level claims.
```

## Forbidden Shortcuts

The next implementation must not:

```text
run PPO;
promote a checkpoint;
use private holdout;
change actor observations;
add condition, fault, pair, probe, success, or feasibility labels to actor input;
update GRU or encoder weights in the first probe;
relax M1285 objective thresholds after seeing a result;
claim closed-loop driver improvement;
claim level3 anticipatory self-identification;
claim paper-level evidence from the public 152-row corpus.
```

## Claim Discipline

M1287 supports only this claim:

```text
The source-history objective-only update branch has a bounded, exact-loss-first
implementation plan.
```

It does not prove:

```text
driver performance;
closed-loop source adaptation;
history necessity under rollout;
high-fidelity four-wheel validation;
paper-level generalization;
real-vehicle readiness.
```

## Next Milestone

Pre-register:

```text
experiments/manifests/m1288-paper-route-source-history-objective-only-update-implementation.json
```

M1288 should implement and run the tiny actor-mean-only objective probe. It must
finish with no promotion and route to a result audit before any PPO or public
replay escalation.
