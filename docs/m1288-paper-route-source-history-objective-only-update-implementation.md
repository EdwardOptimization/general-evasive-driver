# M1288 Paper-Route Source-History Objective-Only Update Implementation

## Summary

M1288 implements and runs the tiny no-PPO source-history objective-only update
designed in M1287.

Decision:

```text
source_history_objective_update_exact_loss_improved_route_to_result_audit
```

Result class:

```text
source_history_objective_update_exact_loss_improved
```

M1288 is an objective-level positive result. It is not a checkpoint promotion,
not a PPO admission, and not a closed-loop driver-performance claim.

## Command

Focused tests:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m pytest -q \
  tests/test_source_history_objective_update.py \
  tests/test_source_history_objective_evaluator.py \
  tests/test_source_history_policy_gate.py
```

Result:

```text
5 passed in 3.17s
```

Objective-only probe:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.source_history_objective_update \
  --checkpoint runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt \
  --history-run-dir runs/m1280_four_wheel_source_response_history_materialization \
  --intervention-run-dir runs/m1277_four_wheel_source_intervention_materialization \
  --run-dir runs/m1288_source_history_objective_only_update \
  --device cpu \
  --trainable-scope actor_mean_only \
  --steps 100 \
  --lr 0.0001
```

## Implementation

Added:

```text
src/autodrift/source_history_objective_update.py
tests/test_source_history_objective_update.py
```

The tool:

```text
loads the M1154 public-gate base;
verifies the canonical 72-value human-view online recurrent contract;
evaluates the exact M1285 source-history objective before update;
freezes all parameters except actor_mean;
runs a 100-step Adam update on the full source-history objective;
writes train_trace.csv and parameter_delta.json;
saves raw_objective_update.pt for diagnostics only;
evaluates the exact M1285 objective after update;
writes before/after objective summaries and row CSVs.
```

No PPO rollout or PPO update occurs.

## Exact Objective Result

Before:

```text
row_count: 152
finite_before: true
base_combined_loss_mean: 18.6105005714
base_correct_preference_loss_mean: 9.3052502857
base_wrong_history_preference_loss_mean: 9.3052502857
```

After:

```text
finite_after: true
after_combined_loss_mean: 7.1793530621
after_correct_preference_loss_mean: 3.5896765310
after_wrong_history_preference_loss_mean: 3.5896765310
```

Delta:

```text
combined_loss_delta: -11.4311475093
correct_preference_loss_delta: -5.7155737547
wrong_history_preference_loss_delta: -5.7155737547
objective_improved: true
```

This passes the exact-loss-first criterion from M1287.

## Mutation Guardrail

Trainable scope:

```text
actor_mean_only
```

Parameter counts:

```text
trainable_parameter_count: 387
frozen_parameter_count: 164292
```

Parameter delta:

```text
actor_mean_changed: true
actor_mean_l2: 0.1133155453
actor_mean_max_abs: 0.0100500062
non_actor_mean_mutation_detected: false
non_actor_mean_l2: 0.0
non_actor_mean_max_abs: 0.0
```

This confirms the first probe only moved the final action-mean head.

## Directional Caveat

The exact loss improved substantially, but the policy-gate directional metrics
are still not positive:

```text
before both_directional_fraction: 0.0
after both_directional_fraction: 0.0
before preferred_hidden_margin_positive_fraction: 0.4868421053
after preferred_hidden_margin_positive_fraction: 0.4078947368
before history_action_l2_mean: 0.0991899768
after history_action_l2_mean: 0.1110339756
```

Interpretation:

```text
The actor-mean-only update reduces the exact log-probability residual, but it
does not yet produce a positive action-level source-history gate. It may be
compressing large residuals without solving row-wise directional separation.
```

Therefore M1288 should route to a result audit before any PPO or replay-gate
escalation.

## Artifacts

Run directory:

```text
runs/m1288_source_history_objective_only_update
```

Artifacts:

```text
summary.json
objective_before.json
objective_after.json
source_history_objective_rows_before.csv
source_history_objective_rows_after.csv
train_trace.csv
parameter_delta.json
checkpoints/raw_objective_update.pt
```

Diagnostic checkpoint:

```text
runs/m1288_source_history_objective_only_update/checkpoints/raw_objective_update.pt
```

This checkpoint is not promoted.

## Guardrails

M1288 did not:

```text
run PPO;
promote a checkpoint;
use private holdout;
change actor observations;
update GRU, encoder, fusion, critic, log_std, or sequence-tail parameters;
relax thresholds;
claim closed-loop driver improvement;
claim level3 self-identification;
claim paper-level evidence.
```

## Next Step

Pre-register:

```text
m1289-paper-route-source-history-objective-only-update-result-audit
```

M1289 should decide whether the M1288 exact-loss improvement is:

```text
an admissible first exact objective step;
a weak objective-only positive that needs row-wise directional repair;
or a public-corpus overfit signal requiring source-history refresh.
```

PPO and promotion remain blocked.
