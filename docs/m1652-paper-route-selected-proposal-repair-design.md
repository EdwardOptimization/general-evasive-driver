# M1652 Paper-Route Selected Proposal Repair Design

## Summary

M1652 designs the first no-checkpoint selected-proposal repair probe after
M1650/M1651 established branch-compatible same-line proposal sources.

Decision:

```text
selected_proposal_repair_design_admit_no_checkpoint_implementation
```

The first implementation should test whether the M1646 damped actor_mean
projection rule repairs real same-line proposal deltas, not synthetic
perturbations. It should remain metrics-only: no checkpoint artifacts, no
closed-loop replay, no PPO, no promotion, no private holdout, and no
paper-level or level3 self-identification claim.

## Selected Proposal Candidates

M1650 selected five repair candidates as metadata:

```text
alpha 0.2
alpha 0.4
alpha 0.6
alpha 0.8
alpha 1.0
```

M1653 should run a small, auditable repair set:

```text
primary: alpha 0.2
stress: alpha 1.0
optional/intermediate: alpha 0.4
```

Rationale:

```text
alpha 0.2 is the smallest rejected larger proposal and tests the easiest real proposal repair;
alpha 1.0 is the raw same-line update and stress-tests whether actor_mean-only repair has enough authority;
alpha 0.4 gives an intermediate residual scale if included.
```

The selected candidates are same-line M1362 interpolation proposals, not PPO
proposals. M1653 must label them as `same_line_interpolation`. Passing M1653
would support selected-proposal projection mechanics only, not PPO continuation.

## Repair Scope

Base anchor:

```text
runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt
```

Proposal checkpoints:

```text
runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_2.pt
runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_4.pt
runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_1_0.pt
```

Materialized targets:

```text
runs/m1630_contour_aware_full_target_materialization
```

Trainable repair scope:

```text
actor_mean.weight
actor_mean.bias
```

Frozen:

```text
response encoder
context encoder
GRU
fusion layers
critic
log_std
auxiliary heads
all non-actor_mean parameters
```

M1653 should initialize the model from the proposal checkpoint and move only
`actor_mean`. It should not interpolate the proposal back to the base. Base
interpolation is a separate technique and remains blocked here.

## Exact Objective

Use the same contour-aware exact objective semantics as M1643/M1646:

```text
positive rows:
  correct hidden -> preferred_action
  wrong hidden   -> wrong_history_action
  separation-collapse residual

diagnostic rows:
  evaluated only
  zero positive weight
  no gradient

donor_plus_hidden_action:
  diagnostic-only
  never a loss target
```

The repair objective is local exact-objective feasibility restoration:

```text
reduce positive_exact_residual_mean(candidate)
while keeping diagnostics role-safe and non-actor_mean parameters unchanged.
```

It is not a closed-loop objective and not promotion evidence.

## Projection Rule

Use the M1646 damped full-batch backtracking rule:

```text
compute full positive exact objective gradient through actor_mean;
normalize actor_mean gradient direction;
try pre-registered backtracking factors;
accept the first candidate that reduces positive exact residual;
stop when target reduction is reached or max projection steps are exhausted.
```

Recommended defaults:

```text
max_projection_steps: 10
initial_step_fraction: 0.25
backtracking_factors: [1, 0.5, 0.25, 0.125, 0.0625, 0.03125, 0.015625]
min_reduction_ratio: 0.25 aggregate, not 0.50 per stress candidate
```

The aggregate threshold is deliberately lower than the synthetic perturbation
stress pass. Real same-line proposal deltas include non-actor_mean movement
that actor_mean-only repair may not fully undo. If the stress candidate fails
while the primary passes, the correct classification is not an immediate
engineering failure; it may indicate insufficient trainable scope for larger
proposal deltas.

## M1653 Output Artifacts

M1653 should write:

```text
runs/m1653_selected_proposal_repair/summary.json
runs/m1653_selected_proposal_repair/candidate_summary.csv
runs/m1653_selected_proposal_repair/aggregate_summary.csv
runs/m1653_selected_proposal_repair/guardrail_summary.csv
runs/m1653_selected_proposal_repair/candidates/<candidate_id>/
```

Each candidate subdirectory should include:

```text
repair_summary.csv
optimization_trace.csv
backtracking_candidates.csv
guardrail_summary.csv
summary.json
```

No `.pt` or `.pth` files may be written.

## Candidate Metrics

For each selected proposal, report:

```text
candidate_id
proposal_source_type
proposal_checkpoint
initial_positive_exact_residual_mean
repaired_positive_exact_residual_mean
positive_exact_residual_reduction
positive_exact_residual_reduction_ratio
initial_positive_action_l2_max
repaired_positive_action_l2_max
proposal_actor_mean_l2_to_base
repaired_actor_mean_l2_to_base
repaired_actor_mean_l2_to_proposal
non_actor_mean_delta_to_proposal_max
accepted_backtracking_step_count
projection_stop_reason
passes_candidate_gate
```

Guardrails:

```text
checkpoint_artifact_count == 0
base_interpolation_used_for_repair_count == 0
diagnostic_rows_used_as_positive_count == 0
donor_plus_action_used_as_loss_target_count == 0
non_actor_mean_parameter_changed_count == 0
training_started_count == 0
ppo_used_count == 0
promoted_count == 0
private_holdout_used_count == 0
actor_input_contract_changed_count == 0
level3_self_id_claim_count == 0
```

## Public Gates

M1653 public smoke gate should require:

```text
selected_candidate_count >= 2
candidate_public_pass_count >= 1
primary_alpha_0_2_pass == true
measurable_initial_residual_count == selected_candidate_count
residual_reduced_count >= 1
checkpoint_artifact_count == 0
base_interpolation_used_for_repair_count == 0
all role and contract guardrail counts == 0
```

Aggregate result classes:

```text
selected_proposal_repair_public_pass:
  primary alpha 0.2 passes and no guardrail fails.

selected_proposal_primary_pass_stress_fail:
  alpha 0.2 passes but stress alpha 1.0 fails.

selected_proposal_repair_scope_insufficient:
  no selected proposal can be improved by actor_mean-only repair.

guardrail_violation:
  any role, checkpoint, interpolation, actor-input, PPO, private-holdout, or level3 guardrail fails.
```

## Failure Taxonomy

Use:

```text
none:
  primary proposal repair passes cleanly.

training_instability:
  gradient is connected but damped steps are unstable.

objective_overfit:
  exact residual improves but later replay gates fail.

metric_artifact:
  aggregate metrics look useful but exact candidate gates do not pass.

lineage_invalid:
  proposal checkpoint no longer matches M1650 metadata.

contract_violation:
  actor inputs, forbidden params, diagnostics, donor-plus, or checkpoint-write guardrails fail.
```

M1653 itself should not run replay gates, so `objective_overfit` is a later
audit classification, not a M1653 gate unless the implementation accidentally
overstates the exact result.

## Next Route

Admit one bounded implementation:

```text
m1653-paper-route-selected-proposal-repair-implementation
```

M1653 should implement the no-checkpoint selected-proposal repair probe for the
pre-registered selected proposals and route to mandatory result audit. It
should not write checkpoint artifacts or run replay/PPO/promotion.
