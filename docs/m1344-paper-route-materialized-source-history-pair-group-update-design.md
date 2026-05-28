# M1344 Paper-Route Materialized Source-History Pair-Group Update Design

## Summary

M1344 designs a bounded no-PPO pair-group objective-update protocol after M1343
selected the update-design route.

Decision:

```text
materialized_source_history_pair_group_update_design_route_to_branch_synthesis
```

Do not implement the update yet.

This branch has reached its synthesis cadence. The next milestone must be:

```text
m1345-paper-route-materialized-source-history-objective-corpus-synthesis
```

## Why Synthesis Comes Next

The active branch is:

```text
paper_route_materialized_source_history_objective_corpus
```

It now contains ten milestones:

```text
M1335 design active objective corpus
M1336 export active/quarantine corpus
M1337 audit export
M1338 design evaluator
M1339 implement evaluator
M1340 audit evaluator result
M1341 design pair-group objective
M1342 implement group metrics
M1343 audit group metrics
M1344 design bounded update protocol
```

The harness rule is clear: after ten narrow milestones, write branch synthesis
before implementation. M1344 therefore designs the next update protocol but
does not admit implementation directly.

## Update Objective

Inputs for a later implementation:

```text
M1339 materialized source-history objective rows
M1342 pair-group metric rows
M1154 current public-gate checkpoint
```

Row loss:

```text
L_row = mean(L_correct + L_wrong)
```

Group-min loss:

```text
row_joint_margin = min(correct_preference_margin, wrong_history_preference_margin)
group_min_joint_margin = min(row_joint_margin_A, row_joint_margin_B)
L_group_min = mean softplus(0.05 - group_min_joint_margin)
```

Condition-balance loss:

```text
L_balance = mean abs(row_joint_margin_A - row_joint_margin_B)
```

Optional trust-region loss:

```text
L_trust = parameter L2 to base checkpoint over allowed trainable scope
```

Candidate combined objective:

```text
L = L_row
  + 1.0 * L_group_min
  + 0.1 * L_balance
  + lambda_trust * L_trust
```

These are design defaults. They are not approved update hyperparameters until
the synthesis decides to open an implementation branch.

## Trainable Scopes

Candidate scopes:

```text
scope A: actor_mean_only
scope B: response_context_fusion + actor_mean
scope C: response_encoder + GRU + response_context_fusion + actor_mean
```

Recommended first implementation after synthesis:

```text
scope B
```

Reason:

```text
Earlier source-history branches found actor_mean_only underpowered, while
fusion_head carried a stronger directional signal. Scope C should stay blocked
until scope B is audited because it has higher blast radius.
```

Always freeze:

```text
log_std
critic/value head
response prediction heads
non-actor optimizer state
all non-selected actor modules
```

## Split And Evaluation Discipline

Use source/fold structure from M1336/M1342.

For the first later implementation:

```text
train folds: 0,1,2,3
eval fold: 4
```

Evaluate before and after on:

```text
train folds
eval fold
full corpus
per-family summaries
per-fold summaries
```

Do not use pair-specific weights. Uniform group weights are allowed. Family or
fold summaries may be reported but should not silently change loss weights in
the first probe.

## Acceptance Gates For A Future Implementation

Exact row gates:

```text
row_count == 1376
finite_row_count == 1376
exact_objective_finite == true
checkpoint_weights_mutated only within allowed scope
```

Group gates:

```text
group_count == 688
valid_two_condition_group_count == 688
group_min_joint_margin_mean improves
group_one_sided_conflict_count decreases
group_all_rows_both_directional_count increases
eval-fold group_min_joint_margin_mean does not regress
eval-fold group_one_sided_conflict_count does not increase
```

Parameter gates:

```text
no forbidden parameter mutation
log_std unchanged
checkpoint remains loadable
```

Process gates:

```text
no PPO
no private holdout
no promotion
no actor input change
no replay/promotion claim from fixed source metrics alone
```

## Failure Classification

A future implementation should classify failures as:

```text
objective_overfit:
  train folds improve but eval fold worsens

proof_washout:
  later public proof gates fail after an update candidate is audited

training_instability:
  nonfinite loss or exploding update

contract_violation:
  actor input or checkpoint contract changes

lineage_invalid:
  update does not start from the declared public-gate base
```

## Next Branch Decision

M1344 does not open implementation directly. It routes to synthesis:

```text
m1345-paper-route-materialized-source-history-objective-corpus-synthesis
```

M1345 should decide whether to:

```text
promote_to_next_branch:
  open a bounded pair-group objective-update implementation branch

pivot:
  repair source-current projection or source corpus before update work

stop:
  close this source-history fixed-current route if evidence is not actionable
```

## Unsupported Claims

Still unsupported:

```text
actor update;
PPO continuation;
promotion;
closed-loop driver performance;
paper-level evidence;
strong self-identification.
```
