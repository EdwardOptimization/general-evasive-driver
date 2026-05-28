# M1339 Paper-Route Materialized Source-History Objective Evaluator Implementation

## Summary

M1339 implemented and ran the exact no-update evaluator over the M1336 active
materialized source-history corpus.

Decision:

```text
materialized_source_history_objective_evaluator_pass_signal_weak_route_to_result_audit
```

The implementation passes the infrastructure gate. The scientific signal is
weak and must be audited before any objective-only update.

## Implementation

Added:

```text
src/autodrift/materialized_source_history_objective_evaluator.py
tests/test_materialized_source_history_objective_evaluator.py
```

The evaluator:

```text
loads the current public-gate checkpoint in eval mode;
replays correct and wrong materialized response histories into recurrent hidden states;
builds a same-current source observation from the final correct-history frame;
uses zero context for indices 12-71;
scores preferred and rejected source actions;
writes exact row, projection, family, fold, and summary artifacts;
checks checkpoint sha256 before and after;
does not train, backpropagate, run PPO, promote, or mutate checkpoint weights.
```

## Commands

Focused test:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q \
  tests/test_materialized_source_history_objective_evaluator.py
```

Result:

```text
1 passed in 2.11s
```

Evaluator:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.materialized_source_history_objective_evaluator \
  --checkpoint runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt \
  --corpus-run-dir runs/m1336_materialized_source_history_objective_corpus_export \
  --run-dir runs/m1339_materialized_source_history_objective_evaluator \
  --device cpu
```

## Artifacts

Primary artifacts:

```text
runs/m1339_materialized_source_history_objective_evaluator/summary.json
runs/m1339_materialized_source_history_objective_evaluator/materialized_source_history_objective_rows.csv
runs/m1339_materialized_source_history_objective_evaluator/history_projection_audit.csv
runs/m1339_materialized_source_history_objective_evaluator/family_summary.csv
runs/m1339_materialized_source_history_objective_evaluator/fold_summary.csv
```

## Structural Result

The evaluator passes all structural gates:

```text
result_class: materialized_source_history_objective_evaluator_pass
checkpoint_contract: canonical_72_human_view_online_recurrent
row_count: 1376
finite_row_count: 1376
projection_valid_count: 1376
wrong_history_valid_count: 1376
source_identity_duplicate_count: 0
active_quarantine_rows_used: 0
exact_objective_finite: true
checkpoint_weights_mutated: false
```

Checkpoint hash:

```text
before: 86b665064e9a1d8d37851d04f39ff30b129552d3debcbf3cc55c85a37d90906b
after:  86b665064e9a1d8d37851d04f39ff30b129552d3debcbf3cc55c85a37d90906b
```

Guardrails:

```text
labels_enter_actor_input: false
training_started: false
ppo_used: false
promoted: false
private_holdout_used: false
actor_update_used: false
actor_input_contract_changed: false
accepted_thresholds_relaxed: false
high_fidelity_validation_claimed: false
```

## Objective Metrics

Exact objective:

```text
correct_preference_loss_mean: 3.4480423585
wrong_history_preference_loss_mean: 3.4367110436
combined_loss_mean: 6.8847534022
```

Directional metrics:

```text
correct_preference_positive_fraction: 0.4970930233
wrong_history_preference_positive_fraction: 0.4970930233
both_directional_fraction: 0.0
correct_closer_to_preferred_fraction: 0.4970930233
wrong_closer_to_rejected_fraction: 0.4970930233
both_distance_directional_fraction: 0.0
```

History action effect:

```text
history_action_l2_mean: 0.0635018957
history_action_l2_p10: 0.0023122903
history_action_l2_p50: 0.0072870062
history_action_l2_p90: 0.2372618015
```

Interpretation:

```text
The checkpoint reacts to materialized histories, but the source-current
objective is not directionally solved. Correct-history and wrong-history
preference signs split into opposite one-sided halves rather than both becoming
positive on the same row.
```

## Family And Fold Metrics

Family summaries:

```text
left_right_split_mu: rows 148, combined_loss_mean 9.7336733377, both_directional 0.0, history_action_l2_mean 0.1015249684
load_cg_perturbation: rows 216, combined_loss_mean 6.3138282690, both_directional 0.0, history_action_l2_mean 0.0647132537
single_wheel_brake_pull: rows 248, combined_loss_mean 7.1166876939, both_directional 0.0, history_action_l2_mean 0.1025260317
single_wheel_grip_collapse: rows 256, combined_loss_mean 9.4274161236, both_directional 0.0, history_action_l2_mean 0.0397775154
steering_actuator_fault: rows 384, combined_loss_mean 4.4205200569, both_directional 0.0, history_action_l2_mean 0.0436274675
tire_blowout_like: rows 124, combined_loss_mean 6.3968818042, both_directional 0.0, history_action_l2_mean 0.0484871217
```

Fold summaries:

```text
fold 0: rows 284, combined_loss_mean 6.9264061141, both_directional 0.0
fold 1: rows 280, combined_loss_mean 6.9659336029, both_directional 0.0
fold 2: rows 272, combined_loss_mean 6.7312906740, both_directional 0.0
fold 3: rows 272, combined_loss_mean 7.2217524205, both_directional 0.0
fold 4: rows 268, combined_loss_mean 6.5695231882, both_directional 0.0
```

## Supported Claims

Supported:

```text
M1339 implements a finite exact no-update materialized source-history objective
evaluator over the M1336 active corpus.
```

Supported:

```text
The current public-gate checkpoint has measurable history-conditioned action
movement on this corpus.
```

Unsupported:

```text
The current checkpoint maps correct histories to preferred source actions and
wrong histories to rejected source actions on the same rows.
```

Unsupported:

```text
actor update;
PPO continuation;
promotion;
closed-loop driver performance;
paper-level evidence;
strong self-identification.
```

## Decision

Do not train.

Do not run PPO.

Do not update actor weights.

Do not promote.

Admit one result audit:

```text
m1340-paper-route-materialized-source-history-objective-evaluator-result-audit
```

M1340 should classify the `both_directional_fraction=0.0` result before any
objective-only update. The likely question is whether this is the same
directional conflict seen in M1290, a source-current projection artifact, or a
corpus symmetry issue that requires pair/group-level objective design.
