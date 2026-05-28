# M1285 Paper-Route Source-History Objective Evaluator

## Summary

M1285 implements and runs the exact no-update source-history preference
objective evaluator designed in M1284.

Decision:

```text
source_history_objective_evaluator_pass_route_to_branch_synthesis
```

Infrastructure result:

```text
result_class: source_history_objective_evaluator_pass
row_count: 152
finite_row_count: 152
exact_objective_finite: true
checkpoint_weights_mutated: false
```

Objective residual:

```text
correct_preference_loss_mean: 9.3052502854
wrong_history_preference_loss_mean: 9.3052502854
combined_loss_mean: 18.6105005708
```

Interpretation:

```text
The exact objective is now measurable and finite. The residual is large, which
matches M1283's weak directional policy-gate signal and gives a concrete target
for a later objective-only update branch.
```

This is still not training, PPO, promotion, driver performance, or
self-identification proof.

## Commands

Focused tests:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q tests/test_source_history_objective_evaluator.py tests/test_source_history_policy_gate.py
```

Run:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.source_history_objective_evaluator --checkpoint runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt --history-run-dir runs/m1280_four_wheel_source_response_history_materialization --intervention-run-dir runs/m1277_four_wheel_source_intervention_materialization --run-dir runs/m1285_source_history_objective_evaluator
```

Validation:

```text
4 passed in 1.08s
```

## Artifacts

Primary artifacts:

```text
src/autodrift/source_history_objective_evaluator.py
tests/test_source_history_objective_evaluator.py
runs/m1285_source_history_objective_evaluator/summary.json
runs/m1285_source_history_objective_evaluator/source_history_objective_rows.csv
runs/m1285_source_history_objective_evaluator/policy_gate/summary.json
```

## Objective

For each source-history row:

```text
L_correct = softplus(logp_cr - logp_cp + 0.05)
L_wrong   = softplus(logp_wp - logp_wr + 0.05)
L_total   = L_correct + L_wrong
```

The evaluator reuses M1283 canonical history projection and policy-side
log-probability computation, but it writes the exact objective residual as
first-class artifacts.

## Result

Checkpoint:

```text
runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt
```

Contract:

```text
checkpoint_actor_encoder: human_view_online_gru
checkpoint_contract: canonical_72_human_view_online_recurrent
```

Mutation check:

```text
checkpoint_sha256_before: 86b665064e9a1d8d37851d04f39ff30b129552d3debcbf3cc55c85a37d90906b
checkpoint_sha256_after:  86b665064e9a1d8d37851d04f39ff30b129552d3debcbf3cc55c85a37d90906b
checkpoint_weights_mutated: false
```

Exact rows:

```text
row_count: 152
finite_row_count: 152
exact_objective_finite: true
```

Policy-direction metrics inherited from M1283:

```text
correct_preference_positive_fraction: 0.5
wrong_history_preference_positive_fraction: 0.5
both_directional_fraction: 0.0
preferred_hidden_margin_positive_fraction: 0.4868421053
history_action_l2_mean: 0.0991899077
```

Loss distribution:

```text
correct_preference_loss_mean: 9.3052502854
wrong_history_preference_loss_mean: 9.3052502854
combined_loss_mean: 18.6105005708

correct_preference_loss_median: 1.0232315154
wrong_history_preference_loss_median: 1.0232315154
combined_loss_median: 21.0442264572
```

The high combined median reflects the paired contradiction seen in M1283: many
rows are good on one branch of the preference but bad on the opposite branch.

## Guardrails

Guardrails held:

```text
labels_enter_actor_input: false
training_started: false
ppo_used: false
promoted: false
private_holdout_used: false
actor_input_contract_changed: false
accepted_thresholds_relaxed: false
high_fidelity_validation_claimed: false
```

M1285 does not run any optimizer and does not write a checkpoint.

## Interpretation

Supported claims:

```text
the exact source-history objective evaluator exists;
the full 152-row source-history objective is finite;
the current public-gate checkpoint has a large source-history residual;
the exact residual can now be used as a future objective-only optimization
target.
```

Unsupported claims:

```text
source-history objective optimization has been attempted;
PPO is admitted;
checkpoint promotion is admitted;
closed-loop source-history intervention works;
the driver has self-identification;
the compact four-wheel source pilot is high fidelity.
```

## Branch Cadence Decision

M1285 is the tenth milestone in the active branch:

```text
paper_route_four_wheel_source_intervention_materialization
```

The branch sequence is:

```text
M1276, M1277, M1278, M1279, M1280,
M1281, M1282, M1283, M1284, M1285
```

Therefore the next milestone must be branch synthesis. Do not add another
narrow objective/optimizer implementation before synthesis.

## Next Step

Admit synthesis:

```text
m1286-paper-route-four-wheel-source-intervention-materialization-synthesis
```

The synthesis should decide whether to open a new source-history objective-only
update branch, repair the source-history corpus, or pivot away from this
four-wheel source path.
