# M1629 Paper-Route Contour-Aware Full Target Materialization Design

## Summary

M1629 designs full contour-aware policy-target materialization after the M1628
branch synthesis.

Decision:

```text
contour_aware_full_target_materialization_design_admit_implementation
```

This is design-only. It does not implement full materialization, construct a
loss or objective config, update an actor, train, run PPO, promote a checkpoint,
use private holdout, change actor inputs, treat diagnostics as positive targets,
or claim level3 self-identification.

## Design Inputs

Use the existing public package and replay artifacts:

```text
candidate package:
  runs/m1615_contour_aware_candidate_corpus/positive_candidate_rows.csv
  runs/m1615_contour_aware_candidate_corpus/diagnostic_guardrail_rows.csv

replay package:
  runs/m1609_diagnostic_complete_bounded_replay/replay_pair_rows.csv
  runs/m1609_diagnostic_complete_bounded_replay/intervention_rows.csv

checkpoint:
  runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt
```

Expected input rows:

```text
positive candidates: 39
diagnostic guardrails: 232
positive source_run counts:
  m1592_clean_repair: 29
  m1595_balanced_repair: 10
diagnostic source_run counts:
  m1588_selector: 8
  m1592_clean_repair: 64
  m1595_balanced_repair: 160
```

M1623 already proved every row matches a replay pair and the required
`normal`, `wrong_history_hidden`, and `donor_response_action_plus_hidden`
variants. M1626 proved the same replay path can capture actual tensors on a
source-diverse four-row subset.

## Implementation Scope

M1630 should implement a materialization runner that scales the M1626 capture
path to all 271 public rows:

```text
39 positive candidates
232 diagnostic guardrails
```

It should reuse, not fork, the dry-run capture primitives where possible:

```text
selected row assembly
replay_pair row lookup
intervention variant lookup
anchor replay cache by anchor_id
model.act_recurrent deterministic action capture
shape / finite / checkpoint-mutation guards
```

The runner should keep the P0 actor contract:

```text
observation dimension: 72
actor_encoder: human-view online GRU family
no hidden params, slip, tire force, oracle feasibility, TTC, reference path, or labels in actor input
```

## Metadata Artifacts

M1630 should write:

```text
runs/m1630_contour_aware_full_target_materialization/summary.json
runs/m1630_contour_aware_full_target_materialization/positive_policy_target_rows.csv
runs/m1630_contour_aware_full_target_materialization/diagnostic_policy_guardrail_rows.csv
runs/m1630_contour_aware_full_target_materialization/capture_traceability_rows.csv
runs/m1630_contour_aware_full_target_materialization/shape_summary.csv
runs/m1630_contour_aware_full_target_materialization/source_summary.csv
runs/m1630_contour_aware_full_target_materialization/guardrail_summary.csv
runs/m1630_contour_aware_full_target_materialization/missing_capture_rows.csv
```

Positive metadata rows must include:

```text
target_id
pair_id
corpus_role = positive_candidate
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
used_as_positive = true
role_weight = 1.0
public_proof_artifact = true
training_ready = false
preferred_variant = normal
wrong_history_variant = wrong_history_hidden
donor_plus_hidden_variant = donor_response_action_plus_hidden
source_preferred_action_l2
source_wrong_history_action_l2
source_donor_plus_hidden_action_l2
```

Diagnostic metadata rows must include the same traceability fields, but:

```text
corpus_role = diagnostic_guardrail
used_as_positive = false
role_weight = 0.0
training_ready = false
```

Diagnostics may be materialized as tensors for audit/negative-control analysis,
but they must never enter positive target counts or positive objective weights.

## Tensor Artifacts

M1630 should write separate NPZ bundles:

```text
positive_policy_targets.npz:
  observation: float32 [39, 72]
  correct_hidden: float32 [39, hidden_dim]
  wrong_hidden: float32 [39, hidden_dim]
  preferred_action: float32 [39, 3]
  wrong_history_action: float32 [39, 3]
  donor_plus_hidden_action: float32 [39, 3]

diagnostic_policy_guardrails.npz:
  observation: float32 [232, 72]
  correct_hidden: float32 [232, hidden_dim]
  wrong_hidden: float32 [232, hidden_dim]
  preferred_action: float32 [232, 3]
  wrong_history_action: float32 [232, 3]
  donor_plus_hidden_action: float32 [232, 3]
```

The hidden dimension is expected to be 128 for the current checkpoint, but the
implementation should read and verify it from captured tensors rather than
hardcoding it as a training assumption.

Optional future sequence targets remain out of scope for M1630. Do not add
sequence-head artifacts in this implementation.

## Success Gates

M1630 should pass only if:

```text
positive_input_row_count == 39
diagnostic_input_row_count == 232
positive_policy_target_count == 39
diagnostic_policy_guardrail_count == 232
positive_observation_shape == [39, 72]
diagnostic_observation_shape == [232, 72]
positive_action_shapes == [39, 3]
diagnostic_action_shapes == [232, 3]
positive_hidden_shapes_ok == true
diagnostic_hidden_shapes_ok == true
hidden_dim > 0
all_tensor_values_finite == true
positive_source_action_l2_max <= 1e-6
diagnostic_source_action_l2_max <= 1e-6
missing_capture_row_count == 0
diagnostic_rows_used_as_positive == false
diagnostic_positive_weight_sum == 0.0
checkpoint_weights_mutated == false
policy_target_materialized == true
materialization_only == true
training_ready == false
training_corpus_exported == false
loss_constructed == false
objective_constructed == false
training_started == false
ppo_used == false
promoted == false
private_holdout_used == false
actor_input_contract_changed == false
labels_enter_actor_input == false
level3_self_id_claim_made == false
guardrail_violation_count == 0
```

## Failure Handling

If any row cannot be captured, M1630 should fail cleanly:

```text
write missing_capture_rows.csv;
write summary.json with passes_public_smoke_gates=false;
do not write partial training-ready artifacts;
route to result audit or capture-tool repair design.
```

Partial NPZ bundles may be omitted on failure. If written for debugging, they
must remain explicitly `training_ready=false` and must not be consumed by later
objective design without a successful audit.

## Public-Gate Overfit Risk

This materialization is still public proof plumbing:

```text
39 positives are public;
232 diagnostics are public;
the result is not a private holdout or promotion gate;
the materialized tensors must not be treated as paper-level evidence by
themselves.
```

Mitigation:

```text
M1630 must route to result audit;
objective construction remains blocked;
future objective design must distinguish positive targets from diagnostics;
future optimizer work must include anti-overfit/generalization controls.
```

## Unsupported Claims

M1629 does not support:

```text
full materialization has been implemented;
objective/loss construction;
actor update;
PPO continuation;
checkpoint promotion;
private-holdout evidence;
paper-level validation;
level3 anticipatory self-identification.
```

## Next

Admit exactly one bounded implementation:

```text
m1630-paper-route-contour-aware-full-target-materialization-implementation
```

The implementation must route to result audit before any objective design,
optimizer, PPO, or promotion step.
