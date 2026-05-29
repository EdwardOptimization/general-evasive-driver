# M1625 Paper-Route Contour-Aware Tensor Capture Dry-Run Design

## Summary

M1625 designs a minimal deterministic tensor-capture dry run after the M1623
traceability pass and M1624 audit.

Decision:

```text
contour_aware_tensor_capture_dry_run_design_admit_implementation
```

This is design-only. It does not implement tensor capture, does not materialize
the full target corpus, does not construct a loss or objective config, does not
update an actor, does not train, does not run PPO, does not promote, and does
not use private holdout.

## Dry-Run Subset

Use a small source-diverse public subset:

```text
positive rows:
  m1592_clean_repair::selected-0000|left_target
  m1595_balanced_repair::selected-0000|left_target

diagnostic rows:
  m1588_selector::selected-0020|left_target
  m1595_balanced_repair::selected-0004|left_target
```

Rationale:

```text
the two positive rows cover both positive source_run aliases;
the diagnostic rows include m1588_selector and m1595_balanced_repair;
the subset is small enough to debug deterministic capture without pretending
full materialization is complete.
```

## Capture Contract

M1626 should capture tensors for exactly the four dry-run rows and the key
variants:

```text
normal
wrong_history_hidden
donor_response_action_plus_hidden
```

Required tensor arrays:

```text
captured_targets.npz:
  observation: float32 [4, 72]
  correct_hidden: float32 [4, hidden_dim]
  wrong_hidden: float32 [4, hidden_dim]
  preferred_action: float32 [4, 3]
  wrong_history_action: float32 [4, 3]
  donor_plus_hidden_action: float32 [4, 3]
```

Optional tensor arrays:

```text
preferred_action_sequence: float32 [4, horizon, 3]
wrong_history_action_sequence: float32 [4, horizon, 3]
donor_plus_hidden_action_sequence: float32 [4, horizon, 3]
```

The observation must remain the canonical P0 72-dim human-view actor frame.
Labels, hidden parameters, oracle feasibility, TTC, path reference, and
controller mode must not enter actor input.

## Metadata Artifacts

M1626 should write:

```text
runs/m1626_contour_aware_tensor_capture_dry_run/summary.json
runs/m1626_contour_aware_tensor_capture_dry_run/captured_target_rows.csv
runs/m1626_contour_aware_tensor_capture_dry_run/captured_targets.npz
runs/m1626_contour_aware_tensor_capture_dry_run/capture_traceability_rows.csv
runs/m1626_contour_aware_tensor_capture_dry_run/shape_summary.csv
runs/m1626_contour_aware_tensor_capture_dry_run/guardrail_summary.csv
runs/m1626_contour_aware_tensor_capture_dry_run/missing_capture_rows.csv
```

Each metadata row should include:

```text
target_id
pair_id
corpus_role
source_run
source_run_dir
source_edge
target_anchor_id
donor_anchor_id
selected_pair_id
original_pair_id
normal_variant_found
wrong_history_variant_found
donor_plus_hidden_variant_found
tensor_index
used_as_positive
role_weight
public_proof_artifact
training_ready = false
```

Diagnostic rows must keep:

```text
used_as_positive: false
role_weight: 0.0
```

## Public Gates

M1626 should pass only if:

```text
dry_run_row_count == 4
positive_capture_count == 2
diagnostic_capture_count == 2
normal_variant_match_count == 4
wrong_history_variant_match_count == 4
donor_plus_hidden_variant_match_count == 4
observation_shape == [4, 72]
preferred_action_shape == [4, 3]
wrong_history_action_shape == [4, 3]
donor_plus_hidden_action_shape == [4, 3]
hidden_dim > 0
correct_hidden_shape_ok == true
wrong_hidden_shape_ok == true
all_tensor_values_finite == true
diagnostic_rows_used_as_positive == false
full_target_corpus_materialized == false
loss_constructed == false
objective_constructed == false
training_started == false
ppo_used == false
promoted == false
private_holdout_used == false
actor_input_contract_changed == false
labels_enter_actor_input == false
level3_self_id_claim_made == false
checkpoint_weights_mutated == false
guardrail_violation_count == 0
```

If tensor capture is not possible, M1626 should fail cleanly with
`missing_capture_rows.csv` and route to runner instrumentation design. It must
not write partial training-ready artifacts.

## Unsupported Claims

M1625 does not support:

```text
tensor capture has been implemented;
full policy target corpus exists;
objective/loss construction;
actor update;
PPO continuation;
checkpoint promotion;
private-holdout evidence;
paper-level validation;
level3 anticipatory self-identification.
```

## Next

Admit exactly one bounded dry-run implementation:

```text
m1626-paper-route-contour-aware-tensor-capture-dry-run-implementation
```

The implementation must route to result audit before full target materialization
or any objective update.
