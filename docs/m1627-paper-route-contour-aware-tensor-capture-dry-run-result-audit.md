# M1627 Paper-Route Contour-Aware Tensor Capture Dry-Run Result Audit

## Summary

M1627 audits the M1626 four-row tensor-capture dry-run result.

Decision:

```text
contour_aware_tensor_capture_audit_public_pass_route_to_branch_synthesis
```

M1626 is a clean public dry-run pass. It proves deterministic policy-side tensor
capture works for the bounded four-row subset. Because the current
contour-aware materialization branch has accumulated another implementation /
audit sequence since the M1618 synthesis, the next route should be branch
synthesis before full target materialization design.

This audit does not materialize the full target corpus, construct a loss or
objective config, update an actor, train, run PPO, promote a checkpoint, use
private holdout, change actor inputs, or claim level3 self-identification.

## M1626 Audit

M1626 summary:

```text
dry_run_row_count: 4
positive_capture_count: 2
diagnostic_capture_count: 2
normal_variant_match_count: 4
wrong_history_variant_match_count: 4
donor_plus_hidden_variant_match_count: 4
missing_capture_row_count: 0
observation_shape: [4, 72]
preferred_action_shape: [4, 3]
wrong_history_action_shape: [4, 3]
donor_plus_hidden_action_shape: [4, 3]
hidden_dim: 128
correct_hidden_shape_ok: true
wrong_hidden_shape_ok: true
all_tensor_values_finite: true
diagnostic_rows_used_as_positive: false
checkpoint_weights_mutated: false
guardrail_violation_count: 0
passes_public_smoke_gates: true
```

Captured arrays:

```text
observation: float32 4x72 finite
correct_hidden: float32 4x128 finite
wrong_hidden: float32 4x128 finite
preferred_action: float32 4x3 finite
wrong_history_action: float32 4x3 finite
donor_plus_hidden_action: float32 4x3 finite
```

Traceability checks:

```text
source_preferred_action_l2 max: 0.0
source_wrong_history_action_l2 max: 0.0
source_donor_plus_hidden_action_l2 max: 0.0
```

Role checks:

```text
positive rows:
  m1592_clean_repair::selected-0000|left_target
  m1595_balanced_repair::selected-0000|left_target

diagnostic rows:
  m1588_selector::selected-0020|left_target, role_weight=0.0, used_as_positive=false
  m1595_balanced_repair::selected-0004|left_target, role_weight=0.0, used_as_positive=false
```

Guardrails:

```text
full_target_corpus_materialized: false
loss_constructed: false
objective_constructed: false
training_started: false
ppo_used: false
promoted: false
private_holdout_used: false
actor_input_contract_changed: false
labels_enter_actor_input: false
level3_self_id_claim_made: false
```

## Supported Claims

M1627 supports:

```text
the M1626 deterministic tensor-capture dry run passed;
the current replay path can recover canonical 72-dim observations;
the current replay path can recover correct and wrong online-GRU hidden tensors;
normal / wrong-history / donor-plus-hidden first actions can be recomputed
exactly from captured tensors;
diagnostic rows can be carried as zero-weight guardrails without entering
positive targets;
runner instrumentation is not the immediate blocker for the dry-run subset.
```

## Unsupported Claims

M1627 does not support:

```text
full target corpus materialization;
full positive/diagnostic tensor coverage;
objective/loss construction;
actor update;
PPO continuation;
checkpoint promotion;
private-holdout evidence;
paper-level validation;
level3 anticipatory self-identification.
```

## Remaining Risk

The main remaining risks are scale and branch governance:

```text
the full 39 positive / 232 diagnostic package has not yet been materialized;
full materialization may expose new anchor replay failures or shape issues;
the current branch has accumulated enough implementation/audit steps that
synthesis should precede another materialization design;
future objective construction must still keep diagnostic rows out of positive
targets and must not let labels enter actor inputs.
```

## Route Decision

Do not jump directly to full corpus implementation. The dry run is clean, but
the process should synthesize the branch before the next implementation/design
step.

Next route:

```text
m1628-paper-route-contour-aware-policy-target-materialization-branch-synthesis
```

Expected synthesis decision if no new contradiction is found:

```text
continue to full target materialization design;
keep objective update, actor update, PPO, promotion, private holdout, and
level3 self-ID claims blocked until later audited stages.
```
