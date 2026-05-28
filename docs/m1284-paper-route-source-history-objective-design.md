# M1284 Paper-Route Source-History Objective Design

## Summary

M1284 designs the exact source-history preference objective needed after the
M1283 policy gate produced a weak directional signal.

Decision:

```text
source_history_objective_design_admit_exact_evaluator
```

Do not start PPO.

Do not run an actor update yet.

The next step should implement an exact no-update evaluator:

```text
m1285-paper-route-source-history-objective-evaluator
```

M1285 should make the M1283 policy-gate residual first-class:

```text
correct history should prefer the preferred action;
wrong history should prefer the rejected action;
all losses should be evaluated exactly on the full M1280/M1277 corpus.
```

## Why An Objective Is Needed

M1283 was infrastructure-valid:

```text
row_count: 152
finite_row_count: 152
projection_valid_count: 152
wrong_history_valid_count: 152
```

But the current public-gate checkpoint does not use the source histories in the
desired direction:

```text
both_directional_fraction: 0.0
preferred_hidden_margin_positive_fraction: 0.4868421053
history_action_l2_mean: 0.0991899077
```

Interpretation:

```text
The histories are visible to the recurrent actor because they move action means,
but the existing checkpoint has not learned the new four-wheel source-history
semantics.
```

Therefore PPO remains blocked. The next useful variable is an exact
full-corpus objective that can quantify and later optimize this residual.

## Objective Definition

For each source-history row:

```text
o      = current 72-value intervention observation
h_c    = hidden state from correct source response history
h_w    = hidden state from same-pair wrong source response history
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

Correct-history preference:

```text
L_correct = softplus(logp_cr - logp_cp + m_correct)
```

Wrong-history preference:

```text
L_wrong = softplus(logp_wp - logp_wr + m_wrong)
```

Combined exact objective:

```text
L_source_history =
    mean(weight * (L_correct + lambda_wrong * L_wrong))
```

Default coefficients:

```text
m_correct = 0.05
m_wrong = 0.05
lambda_wrong = 1.0
```

Use uniform weights for M1285. Do not introduce row weighting until a later
objective-only update design, because weights can hide source-family coverage
problems.

## Exact Evaluator

M1285 should implement a no-update evaluator that:

```text
loads a checkpoint;
verifies canonical 72-value human-view online recurrent contract;
reuses the M1283 canonical history projection;
computes h_c and h_w by replaying M1280 source-history prefixes;
computes logp_cp, logp_cr, logp_wp, logp_wr for every row;
computes L_correct, L_wrong, and L_source_history;
writes exact row and summary artifacts;
does not mutate model weights.
```

The evaluator should not rely on sampled PPO minibatches. It must evaluate the
full `152`-row M1280/M1277 source corpus every time.

## Metrics

Row metrics:

```text
history_intervention_id
intervention_id
pair_id
condition
probe_template
correct_history_id
wrong_history_id
logp_cp
logp_cr
logp_wp
logp_wr
correct_preference_margin
wrong_history_preference_margin
preferred_hidden_margin
rejected_hidden_margin
correct_preference_loss
wrong_history_preference_loss
combined_loss
history_action_l2
finite
```

Summary metrics:

```text
row_count
finite_row_count
correct_preference_loss_mean
wrong_history_preference_loss_mean
combined_loss_mean
correct_preference_positive_fraction
wrong_history_preference_positive_fraction
both_directional_fraction
preferred_hidden_margin_positive_fraction
history_action_l2_mean
exact_objective_finite
```

Result classes:

```text
source_history_objective_evaluator_pass
source_history_objective_evaluator_contract_failure
source_history_objective_evaluator_nonfinite
```

M1285 passes as infrastructure if the exact evaluator writes finite metrics. A
high loss is not a failure; it is the residual the later objective-only update
would try to reduce.

## What M1285 Must Not Do

M1285 must not:

```text
train;
run PPO;
update actor parameters;
interpolate checkpoints;
run public replay gates;
promote;
use private holdout;
add fault/condition/pair/probe labels to actor inputs;
claim self-identification or driver performance.
```

Reason:

```text
The branch is at the end of its source-intervention materialization cadence.
After M1285 implements the exact evaluator, the next milestone should be branch
synthesis before any optimizer or actor-update work.
```

## Later Objective-Only Update Candidate

After synthesis, a future branch may design an objective-only update. It should
not be admitted before M1285 and branch synthesis.

Candidate update guardrails:

```text
start from M1154 public-gate checkpoint;
minimize exact M1285 source-history objective;
include a trust region to the base checkpoint;
add public-gate retention only after the exact objective is finite and stable;
evaluate exact objective before any replay gate;
run full public gates only after exact objective improves and guardrails hold.
```

Possible trainable scopes, in conservative order:

```text
actor_mean_only;
response_context_fusion + actor_mean;
response_encoder + GRU + fusion + actor_mean.
```

Do not start with PPO. PPO should remain blocked until an objective-only path
can reduce the exact source-history residual without obvious public-gate
washout.

## Branch Cadence

The active branch is:

```text
paper_route_four_wheel_source_intervention_materialization
```

The branch began at M1276. M1285 will be the tenth milestone in the branch:

```text
M1276, M1277, M1278, M1279, M1280, M1281, M1282, M1283, M1284, M1285
```

Therefore after M1285:

```text
write branch synthesis before adding another narrow implementation/update
milestone.
```

The synthesis should decide whether to:

```text
open a source-history objective-only update branch;
repair source-history materialization;
pivot to a richer prefix/active-probing source;
or archive the four-wheel source-history path as useful but currently
not policy-admissible.
```

## Next Step

Admit implementation-only:

```text
m1285-paper-route-source-history-objective-evaluator
```

M1285 should implement and run the exact evaluator, write row and summary
artifacts, and then route to branch synthesis. It should not train or promote.
