# M1145 V4 Public Base Row15 Promoted Objective Result Audit

## Purpose

M1145 audits the M1144 objective-corpus result before any guarded actor-update
design.

This milestone is audit-only. It does not train actor weights, run PPO, run
replay, optimize an objective, build a corpus, mine rows, promote a checkpoint,
use private holdout, or change actor inputs.

## M1144 Result

Corpus gates passed:

```text
corpus_rows: 76
physical_pairs: 13
targets: 2
success_drop_rows: 76
selected_source_rows: 76
action_reconstruction_error_max: 0.0
action_reconstruction_error_mean: 0.0
```

Objective sanity passed:

```text
objective_pass: true
seed_pass_count: 3
min_val_combined_loss_improvement: 2.906849
min_val_delta_loss_improvement: 3.633356
mean_val_pairwise_accuracy_after: 1.0
min_val_pairwise_accuracy_after: 1.0
```

The objective pass is not marginal. All three optimization seeds pass, and the
action reconstruction check confirms that materialized first actions match the
`row15_current` model snapshots.

## Limitations

The result is still narrow:

```text
targets: 2
future_braking_deceleration rows: 52
future_yaw_response rows: 24
future_lateral_accel_response rows: 0
rows are derived from public proof-surface artifacts
result is auxiliary objective sanity, not closed-loop behavior
no post-update replay has been run
```

Therefore M1144 cannot support:

```text
driver improvement
checkpoint promotion
PPO readiness
private generalization
paper-level evidence
level3 anticipatory self-identification
```

## Audit Decision

The result is strong enough to admit a guarded actor-update design, but not an
actor update.

The next design must preserve these constraints:

```text
init checkpoint:
  runs/m1123_row15_unsafe_margin_projection_probe/checkpoints/alpha_0_15.pt

snippet npz:
  runs/m1144_row15_promoted_objective_corpus/boundary_outcome_corpus.npz

train scope:
  actor_coupling only

actor inputs:
  unchanged P0 human-view no-wheel 72-dim frame + online GRU hidden state

PPO:
  blocked

promotion:
  blocked

private holdout:
  blocked
```

## Required Guarded-Update Gates

A later actor-update implementation must be pre-registered with:

```text
1. exact M1144 objective no-regression versus alpha_0_15 base;
2. exact M1144 objective improvement for at least one candidate;
3. low-drift parameter scope limited to allowed actor-coupling surfaces;
4. log_std unchanged;
5. action-anchor retention against alpha_0_15 base;
6. snippet-action-anchor retention for both preferred and rejected hidden states;
7. allowed-parameter audit before any replay;
8. first replay gates before any full public gate;
9. behavior-retention gates before any PPO design;
10. no promotion from actor update alone.
```

If any of these gates are unavailable or ambiguous, the next step must remain a
design or audit rather than implementation.

## Decision

```text
row15_promoted_objective_result_audit_admit_guarded_actor_update_design
```

Next:

```text
m1146-v4-public-base-row15-promoted-guarded-actor-update-design
```
