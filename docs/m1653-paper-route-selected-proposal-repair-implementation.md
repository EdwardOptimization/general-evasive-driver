# M1653 Paper-Route Selected Proposal Repair Implementation

## Summary

M1653 implements and runs the no-checkpoint selected-proposal actor_mean repair
probe designed in M1652.

Decision:

```text
selected_proposal_repair_negative_route_to_audit
```

The implementation and focused tests passed, and all guardrails remained clean.
However, the primary alpha `0.2` proposal did not improve under the
actor_mean-only damped projection rule. The aggregate public gate therefore
failed:

```text
passes_public_smoke_gates: false
null_result_classification: selected_proposal_repair_scope_insufficient
```

This is a negative result for actor_mean-only selected-proposal repair on real
same-line proposal deltas. It is not a checkpoint, replay, PPO, promotion,
private-holdout, paper-level, or level3 self-identification result.

## Implementation

Added:

```text
src/autodrift/selected_proposal_repair.py
tests/test_selected_proposal_repair.py
```

The probe:

```text
base checkpoint:
  runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt

proposal metadata:
  runs/m1650_proposal_source_preflight/candidate_summary.csv

materialized target tensors:
  runs/m1630_contour_aware_full_target_materialization

selected alphas:
  0.2, 0.4, 1.0

repair scope:
  actor_mean.weight
  actor_mean.bias

blocked:
  base interpolation
  checkpoint artifact write
  replay gates
  PPO
  promotion
```

## Validation

Focused test:

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m pytest -q tests/test_selected_proposal_repair.py
```

Result:

```text
3 passed in 2.10s
```

Official M1653 run:

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.selected_proposal_repair \
  --base-checkpoint runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt \
  --candidate-summary runs/m1650_proposal_source_preflight/candidate_summary.csv \
  --materialization-run-dir runs/m1630_contour_aware_full_target_materialization \
  --run-dir runs/m1653_selected_proposal_repair \
  --selected-alphas 0.2,0.4,1.0
```

Artifacts:

```text
runs/m1653_selected_proposal_repair/summary.json
runs/m1653_selected_proposal_repair/candidate_summary.csv
runs/m1653_selected_proposal_repair/aggregate_summary.csv
runs/m1653_selected_proposal_repair/guardrail_summary.csv
runs/m1653_selected_proposal_repair/candidates/
```

## Aggregate Result

```text
selected_candidate_count: 3
measurable_initial_residual_count: 3
residual_reduced_count: 1
candidate_public_pass_count: 0
primary_alpha_0_2_pass: false
passes_public_smoke_gates: false
null_result_classification: selected_proposal_repair_scope_insufficient
```

Candidate details:

| Alpha | Initial Exact | Repaired Exact | Reduction Ratio | Accepted Steps | Candidate Gate |
| --- | ---: | ---: | ---: | ---: | --- |
| 0.2 | 0.0012401377316564322 | 0.0012401377316564322 | 0.0 | 0 | false |
| 0.4 | 0.010803105309605598 | 0.010803105309605598 | 0.0 | 0 | false |
| 1.0 | 0.08403468132019043 | 0.07793601602315903 | 0.07257319479554114 | 1 | false |

Interpretation:

```text
alpha 0.2 primary: no accepted backtracking candidate; no residual reduction.
alpha 0.4 intermediate: no accepted backtracking candidate; no residual reduction.
alpha 1.0 stress: one step reduced residual by about 7.26%, below the 25% candidate gate.
```

## Guardrails

Guardrail counts:

```text
checkpoint_artifact_count: 0
base_interpolation_used_for_repair_count: 0
non_actor_mean_parameter_changed_count: 0
diagnostic_rows_used_as_positive_count: 0
donor_plus_action_used_as_loss_target_count: 0
guardrail_violation_count: 0
training_started_count: 0
ppo_used_count: 0
promoted_count: 0
private_holdout_used_count: 0
actor_input_contract_changed_count: 0
level3_self_id_claim_count: 0
```

No `.pt` or `.pth` files exist under the M1653 run directory.

## Failure Taxonomy

Failure taxonomy:

```text
training_instability
```

The label is used for projection/scope insufficiency: the repair objective was
connected and artifacts were written cleanly, but the pre-registered
actor_mean-only damped projection rule could not improve the primary proposal
and did not reach the selected-proposal candidate gate. No environment training
or PPO ran.

## Supported Claims

M1653 supports:

```text
selected-proposal repair plumbing works and is focused-tested;
M1362 same-line proposal residuals are measurable under the contour-aware exact objective;
the no-checkpoint, no-base-interpolation, actor_mean-only and role guardrails held;
actor_mean-only damped projection is insufficient for the primary alpha 0.2 same-line proposal under the pre-registered rule.
```

## Unsupported Claims

M1653 does not support:

```text
selected-proposal repair works;
PPO-proposal repair works;
checkpoint artifact generation;
closed-loop replay improvement;
behavior retention;
promotion;
private-holdout evidence;
paper-level evidence;
level3 anticipatory self-identification.
```

## Next Route

Route to result audit:

```text
m1654-paper-route-selected-proposal-repair-result-audit
```

M1654 should audit this negative result before any wider trainable-scope design,
alternative projection rule, checkpoint artifact, or replay gate. It should not
rerun repair or tune the projection parameters inside the audit.
