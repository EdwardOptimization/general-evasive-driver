# M1621 Paper-Route Contour-Aware Policy Target Materialization Design

## Summary

M1621 designs policy-side target materialization for the contour-aware candidate
package.

Decision:

```text
contour_aware_policy_target_materialization_design_admit_audit
```

This is design-only. It does not implement materialization, does not construct
a loss or objective config, does not update an actor, does not train, does not
run PPO, does not promote, and does not use private holdout.

## Why This Is Needed

M1619 proved that the package can be evaluated with finite row-metric residuals,
but M1620 rejected direct objective update because the package lacks policy-side
tensors:

```text
observation frames;
correct/current hidden state;
wrong/donor hidden state;
preferred action or action sequence;
rejected/control action or action sequence;
trajectory snippet arrays.
```

The next safe step is to design how to materialize these targets while
preserving the public-proof role contract.

## Source Traceability

M1615 positive candidate rows contain stable trace keys:

```text
source_run
contour_pair_id
selected_pair_id
original_pair_id
target_anchor_id
donor_anchor_id
target_anchor_window
donor_anchor_window
target_source_family
donor_source_family
source_edge
```

Observed positive candidate sources:

```text
source_run counts:
  m1592_clean_repair: 29
  m1595_balanced_repair: 10

source_edge counts:
  actuator_delay_step|capability_step_up: 13
  curved_boundary_obstacle|t5_boundary_axis_retarget: 12
  actuator_delay_step|t5_near_boundary_warmup: 8
  capability_step_down|t5_near_boundary_warmup: 6

anchor windows:
  reveal_plus_4: 21
  decision_minus_32: 12
  decision_minus_24: 6
```

Known source run mapping:

```text
m1592_clean_repair ->
  runs/m1592_clean_history_control_source_generation_repair_smoke

m1595_balanced_repair ->
  runs/m1595_selector_balanced_clean_source_repair_smoke

M1609 replay package ->
  runs/m1609_diagnostic_complete_bounded_replay
```

The design must first verify that every M1615 row can be matched to M1609
`replay_pair_rows.csv` and `intervention_rows.csv`, then trace back to the
source-run selected pairs.

## Important Limitation

The current source CSVs include useful closed-loop replay metadata such as:

```text
first_action_steer / throttle / brake
terminal_margin
normal_terminal_margin
terminal_margin_gap_from_normal
success / collision
target_hidden_norm
donor_hidden_norm
target_donor_hidden_l2
target_donor_response_action_l2
```

They do not store full observation vectors or full hidden-state tensors. A
policy-side target corpus must therefore reconstruct or rerun the deterministic
fixed-policy replay with tensor capture enabled. M1621 does not implement that
rerun; it specifies the required materialization contract.

## Target Schema

Future materialization should write metadata CSV files and tensor NPZ files.

Positive metadata:

```text
positive_policy_target_rows.csv:
  target_id
  pair_id
  source_run
  source_run_dir
  contour_pair_id
  selected_pair_id
  original_pair_id
  source_edge
  target_anchor_id
  donor_anchor_id
  target_anchor_window
  donor_anchor_window
  target_anchor_step
  donor_anchor_step
  role = positive_candidate
  role_weight = 1.0
  preferred_variant = normal
  rejected_variant = wrong_history_hidden or donor_response_action_plus_hidden
  preferred_action_source = normal first action or captured sequence action[0]
  rejected_action_source = rejected variant first action or captured sequence action[0]
  tensor_index
  public_proof_artifact = true
  training_ready = false
```

Positive tensor bundle:

```text
positive_policy_targets.npz:
  observation[rows, 72]
  correct_hidden[rows, hidden_dim]
  wrong_hidden[rows, hidden_dim]
  preferred_action[rows, 3]
  rejected_action[rows, 3]
  preferred_action_sequence[rows, horizon, 3] optional
  rejected_action_sequence[rows, horizon, 3] optional
```

Diagnostic metadata:

```text
diagnostic_policy_guardrail_rows.csv:
  diagnostic_id
  pair_id
  source_run
  source_run_dir
  contour_pair_id
  selected_pair_id
  original_pair_id
  source_edge
  rule_reason
  label
  role = diagnostic_guardrail
  role_weight = 0.0
  used_as_positive = false
  tensor_index optional
  public_proof_artifact = true
  training_ready = false
```

Diagnostics may include tensors for audit or negative-control analysis, but
they must not become positive targets and must not lower a positive objective.

## Materialization Flow

Future implementation should be staged:

1. Read M1615 positive and diagnostic rows.
2. Resolve `source_run` to known source directories.
3. Match every row against M1609 `replay_pair_rows.csv`.
4. Match variants in M1609 `intervention_rows.csv`.
5. Verify that selected source-run rows exist in the original source run.
6. If full tensors are absent, rerun deterministic fixed-policy trace capture
   for matched anchors with the same checkpoint and actor contract.
7. Export metadata CSV and NPZ tensor bundles.
8. Prove no checkpoint mutation and no training artifacts.
9. Route to result audit before any objective or optimizer design.

## M1623 Implementation Gates

If a later audit admits implementation, that implementation should pass only if:

```text
positive_candidate_count == 39
positive_policy_target_count == 39
diagnostic_guardrail_count == 232
diagnostic_policy_guardrail_count == 232
positive_traceability_success_count == 39
diagnostic_traceability_success_count == 232
positive_tensor_rows == 39
diagnostic_rows_used_as_positive == false
diagnostic_positive_weight_sum == 0.0
observation_shape == [39, 72] for positives
action_shape == [39, 3] for positives
hidden_shapes_present == true
all_tensor_values_finite == true
checkpoint_weights_mutated == false
training_ready == false
training_started == false
ppo_used == false
promoted == false
private_holdout_used == false
actor_input_contract_changed == false
labels_enter_actor_input == false
level3_self_id_claim_made == false
guardrail_violation_count == 0
```

If full tensor traceability is not possible, the implementation should fail
cleanly and route to source-artifact discovery audit rather than writing a
partial training corpus.

## Public-Gate Overfit Risk

Risk remains high:

```text
the target rows are public;
positive count is 39;
source-edge count is 4;
trace reconstruction could overfit public proof surfaces;
diagnostics are guardrails, not private validation.
```

Mitigation:

```text
materialization is not training-ready;
diagnostics remain non-positive;
implementation requires result audit;
future objective update requires separate design and gate;
private holdout remains unused.
```

## Unsupported Claims

M1621 does not support:

```text
policy targets have been materialized;
objective/loss construction;
actor update;
PPO continuation;
checkpoint promotion;
private-holdout evidence;
paper-level validation;
level3 anticipatory self-identification.
```

## Next

M1621 requires an audit before implementation:

```text
m1622-paper-route-contour-aware-policy-target-materialization-design-audit
```
